from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from ..client import SebpayClient


class Collections:
    def __init__(self, client: "SebpayClient"):
        self._client = client

    def create(self, **params) -> dict:
        """Directly charge a customer's mobile money account — you supply the
        operator/phone/OTP yourself. For a hosted, redirect-based flow use
        `SebpayClient.checkout_sessions` instead.

        Params: amount, currency, phone, operator, country, external_reference
        (required), callback_url, customer_name, customer_email, otp_code (optional).
        """
        return self._client.request("POST", "/collections", params)

    def retrieve(self, id_or_reference: str) -> dict:
        return self._client.request("GET", f"/collections/{quote(id_or_reference)}")
