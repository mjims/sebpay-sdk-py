import json
import unittest
from pathlib import Path

from sebpay import SIGNATURE_HEADER, verify_signature

VECTORS = json.loads((Path(__file__).resolve().parents[2] / "test-vectors" / "webhooks.json").read_text(encoding="utf-8"))


class SignatureVectors(unittest.TestCase):
    def test_vectors(self):
        for case in VECTORS["cases"]:
            for body in (case["body"].encode("utf-8"), case["body"]):
                with self.subTest(case["name"], body_type=type(body).__name__):
                    self.assertIs(verify_signature(body, case["signature"], VECTORS["secret_key"]), case["valid"])

    def test_missing_or_odd_inputs_return_false_without_raising(self):
        ok = VECTORS["cases"][0]
        self.assertIs(verify_signature(ok["body"].encode(), None, VECTORS["secret_key"]), False)
        self.assertIs(verify_signature(ok["body"].encode(), "é" * 64, VECTORS["secret_key"]), False)
        self.assertIs(verify_signature(None, ok["signature"], VECTORS["secret_key"]), False)

    def test_signature_header(self):
        self.assertEqual(SIGNATURE_HEADER, "X-SebPay-Signature")


if __name__ == "__main__":
    unittest.main()
