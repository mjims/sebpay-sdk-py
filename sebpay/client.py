from __future__ import annotations

from typing import Any, Optional

import requests

from ._version import __version__
from .errors import SebpayApiError
from .resources.checkout_sessions import CheckoutSessions

LIVE_BASE_URL = "https://newapi.sebpay.africa/api/v1"
SANDBOX_BASE_URL = "https://api.sandbox.sebpay.bj/api/v1"
DEFAULT_TIMEOUT = 30


class SebpayClient:
    """Entry point for Sebpay hosted checkout. Pass the key pair from your
    dashboard (API développeur): the sandbox and live are separate servers,
    and pk_test_ keys are sent to the sandbox, pk_live_ keys to live.
    `base_url` overrides that choice; `timeout` is in seconds.
    """

    def __init__(self, public_key: str, secret_key: str, base_url: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        self._public_key = public_key
        self._secret_key = secret_key
        self._timeout = timeout
        self.base_url = (base_url or (SANDBOX_BASE_URL if public_key.startswith("pk_test_") else LIVE_BASE_URL)).rstrip("/")
        self._session = requests.Session()

        # The transport stays private: the SDK only calls the endpoints it wraps
        self.checkout_sessions = CheckoutSessions(self._request)

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> Any:
        """Returns the `data` field of a successful response; raises SebpayApiError otherwise."""
        headers = {
            "X-Public-Key": self._public_key,
            "X-Secret-Key": self._secret_key,
            "Accept": "application/json",
            "User-Agent": f"sebpay-python/{__version__}",
        }

        try:
            response = self._session.request(method, f"{self.base_url}{path}", headers=headers, json=body, timeout=self._timeout)
        except requests.Timeout as e:
            raise SebpayApiError(f"Sebpay request timed out after {self._timeout} s", 0, None, code="TIMEOUT") from e
        except requests.RequestException as e:
            raise SebpayApiError(f"Sebpay request failed: {e}", 0, None, code="NETWORK_ERROR") from e

        try:
            decoded = response.json()
        except ValueError:
            decoded = None
        error_body = decoded if decoded is not None else response.text

        if not 200 <= response.status_code < 300 or (isinstance(decoded, dict) and decoded.get("success") is False):
            errors = decoded.get("errors") if isinstance(decoded, dict) else None
            code = errors.get("code") if isinstance(errors, dict) else None
            message = decoded.get("message") if isinstance(decoded, dict) else None
            raise SebpayApiError(
                message if isinstance(message, str) else f"Sebpay API error (HTTP {response.status_code})",
                response.status_code,
                error_body,
                code=code if isinstance(code, str) else None,
            )

        if not isinstance(decoded, dict) or not isinstance(decoded.get("data"), dict):
            raise SebpayApiError("Sebpay API returned an unexpected response", response.status_code, error_body, code="INVALID_RESPONSE")

        return decoded["data"]
