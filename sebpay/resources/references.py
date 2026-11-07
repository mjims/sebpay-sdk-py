from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import SebpayClient


class References:
    def __init__(self, client: "SebpayClient"):
        self._client = client

    def countries(self) -> list:
        return self._client.request("GET", "/countries")

    def operators(self, country: Optional[str] = None) -> list:
        params = {"country": country} if country else {}
        return self._client.request("GET", "/operators", params)

    def calculate_fee(
        self,
        amount,
        source_country: str,
        destination_country: str,
        transaction_type: str = "collection",
    ) -> dict:
        """Preview the fee (in XOF) for a corridor before creating a transaction.
        Country codes are ISO (e.g. "bj"). This is the standard public tariff: it does
        not know a tariff negotiated for your account, so the fee actually charged can differ."""
        return self._client.request(
            "GET",
            "/c/calculate-fee",
            {
                "amount": amount,
                "source_country": source_country,
                "destination_country": destination_country,
                "transaction_type": transaction_type,
            },
        )
