import json
import re
import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import sebpay
from sebpay import SebpayApiError, SebpayClient


def _json(handler, status, payload):
    raw = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _text(handler, status, text):
    raw = text.encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


class FakeApi(BaseHTTPRequestHandler):
    """A local stand-in for the API: the first path segment picks the answer."""

    last = None

    def log_message(self, *args):
        pass

    def _handle(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode() if length else ""
        FakeApi.last = {"method": self.command, "path": self.path, "headers": dict(self.headers), "raw": raw}
        mode = self.path.split("/")[1]
        if mode == "ok":
            _json(self, 200, {"success": True, "data": {"echo": {"method": self.command, "url": self.path, "body": json.loads(raw) if raw else None}}})
        elif mode == "conflict":
            _json(self, 409, {"success": False, "message": "Already used", "errors": {"code": "EXTERNAL_REFERENCE_CONFLICT"}})
        elif mode == "invalid":
            _json(self, 422, {"success": False, "message": "Validation Error.", "errors": {"redirect_url": ["required"]}})
        elif mode == "refused":
            _json(self, 200, {"success": False, "message": "Refused"})
        elif mode == "nodata":
            _json(self, 200, {"success": True})
        elif mode == "html":
            _text(self, 200, "<html>maintenance</html>")
        elif mode == "gateway":
            _text(self, 502, "<html>Bad gateway</html>")
        elif mode == "slow":
            time.sleep(1.5)
            _json(self, 200, {"success": True, "data": {}})

    do_GET = _handle
    do_POST = _handle


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeApi)
        cls.server.daemon_threads = True
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def client(self, mode, **options):
        return SebpayClient("pk_test_pub", "sk_test_sec", base_url=f"{self.base}/{mode}", **options)

    def test_base_url_follows_the_key_prefix(self):
        self.assertEqual(SebpayClient("pk_test_x", "sk_test_x").base_url, "https://api.sandbox.sebpay.bj/api/v1")
        self.assertEqual(SebpayClient("pk_live_x", "sk_live_x").base_url, "https://newapi.sebpay.africa/api/v1")
        self.assertEqual(SebpayClient("pk_test_x", "sk_test_x", base_url="http://localhost:8000/api/v1/").base_url, "http://localhost:8000/api/v1")

    def test_only_hosted_checkout_is_exposed(self):
        client = self.client("ok")
        self.assertTrue(callable(client.checkout_sessions.create) and callable(client.checkout_sessions.retrieve))
        for gone in ("collections", "payouts", "references", "request"):
            self.assertFalse(hasattr(client, gone), gone)
        self.assertEqual(sorted(sebpay.__all__), ["SIGNATURE_HEADER", "SebpayApiError", "SebpayClient", "verify_signature"])

    def test_version_matches_pyproject(self):
        pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        self.assertEqual(re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1), sebpay.__version__)

    def test_create_posts_json_with_the_keys_and_user_agent(self):
        echo = self.client("ok").checkout_sessions.create(amount=5000, currency="XOF", redirect_url="https://shop.test/r", metadata={"a": 1})["echo"]
        self.assertEqual(echo, {"method": "POST", "url": "/ok/checkout/sessions", "body": {"amount": 5000, "currency": "XOF", "redirect_url": "https://shop.test/r", "metadata": {"a": 1}}})
        headers = FakeApi.last["headers"]
        self.assertEqual(headers["X-Public-Key"], "pk_test_pub")
        self.assertEqual(headers["X-Secret-Key"], "sk_test_sec")
        self.assertEqual(headers["User-Agent"], f"sebpay-python/{sebpay.__version__}")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "application/json")

    def test_retrieve_gets_the_encoded_id_without_body(self):
        echo = self.client("ok").checkout_sessions.retrieve("A/B C?d")["echo"]
        self.assertEqual(echo["url"], "/ok/checkout/sessions/A%2FB%20C%3Fd")
        self.assertEqual(echo["method"], "GET")
        self.assertEqual(FakeApi.last["raw"], "")

    def test_api_error_carries_status_code_and_body(self):
        with self.assertRaises(SebpayApiError) as ctx:
            self.client("conflict").checkout_sessions.retrieve("x")
        err = ctx.exception
        self.assertEqual((err.status, err.code, str(err)), (409, "EXTERNAL_REFERENCE_CONFLICT", "Already used"))
        self.assertEqual(err.body["errors"], {"code": "EXTERNAL_REFERENCE_CONFLICT"})

    def test_error_without_code_has_code_none(self):
        with self.assertRaises(SebpayApiError) as ctx:
            self.client("invalid").checkout_sessions.retrieve("x")
        self.assertEqual((ctx.exception.status, ctx.exception.code), (422, None))
        self.assertEqual(ctx.exception.body["errors"]["redirect_url"], ["required"])

    def test_success_false_is_an_error_even_with_200(self):
        with self.assertRaises(SebpayApiError) as ctx:
            self.client("refused").checkout_sessions.retrieve("x")
        self.assertEqual((ctx.exception.status, str(ctx.exception)), (200, "Refused"))

    def test_2xx_without_data_or_not_json_is_invalid_response(self):
        for mode in ("nodata", "html"):
            with self.subTest(mode), self.assertRaises(SebpayApiError) as ctx:
                self.client(mode).checkout_sessions.retrieve("x")
            self.assertEqual((ctx.exception.status, ctx.exception.code), (200, "INVALID_RESPONSE"))

    def test_non_json_error_page_keeps_status_and_text(self):
        with self.assertRaises(SebpayApiError) as ctx:
            self.client("gateway").checkout_sessions.retrieve("x")
        self.assertEqual((ctx.exception.status, ctx.exception.code), (502, None))
        self.assertIn("Bad gateway", ctx.exception.body)

    def test_no_server_is_network_error(self):
        client = SebpayClient("pk_test_x", "sk_test_x", base_url=f"http://127.0.0.1:{_free_port()}")
        with self.assertRaises(SebpayApiError) as ctx:
            client.checkout_sessions.retrieve("x")
        self.assertEqual((ctx.exception.status, ctx.exception.code), (0, "NETWORK_ERROR"))

    def test_timeout_aborts_a_slow_request(self):
        started = time.monotonic()
        with self.assertRaises(SebpayApiError) as ctx:
            self.client("slow", timeout=0.2).checkout_sessions.retrieve("x")
        self.assertEqual((ctx.exception.status, ctx.exception.code), (0, "TIMEOUT"))
        self.assertLess(time.monotonic() - started, 1.2)


if __name__ == "__main__":
    unittest.main()
