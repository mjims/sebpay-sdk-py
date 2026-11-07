from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from ..client import SebpayClient


class Payouts:
    def __init__(self, client: "SebpayClient"):
        self._client = client

    def create(self, **params) -> dict:
        """Send funds from your Sebpay wallet to a mobile money recipient.
        The balance is deducted immediately; final confirmation arrives via webhook.

        Params: recipient_name, phone, operator, country, amount, currency,
        external_reference (required), callback_url, description (optional).
        """
        return self._client.request("POST", "/payouts", params)

    def retrieve(self, id_or_reference: str) -> dict:
        return self._client.request("GET", f"/payouts/{quote(id_or_reference)}")
