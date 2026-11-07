from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import quote

if TYPE_CHECKING:
    from ..types import CheckoutSession, CheckoutSessionDetails


class CheckoutSessions:
    def __init__(self, request: Callable[..., Any]):
        self._request = request

    def create(self, **params: Any) -> CheckoutSession:
        """Create a hosted checkout session. Returns `checkout_url` — redirect
        your customer's browser there.

        Params: amount, currency, redirect_url (required), external_reference,
        callback_url, customer_name, customer_email, customer_phone, metadata (optional).
        Sending an external_reference again with the same parameters returns the
        same session with `idempotent_replay` = True.
        """
        return self._request("POST", "/checkout/sessions", params)

    def retrieve(self, id_or_reference: str) -> CheckoutSessionDetails:
        """Retrieve a session by its id (the `checkout_session_id` of your
        redirect_url), its token or your external_reference. This is the
        server-to-server confirmation: when your customer comes back, deliver
        only if `transaction_status` is "approved" — the redirect alone proves nothing."""
        return self._request("GET", f"/checkout/sessions/{quote(id_or_reference, safe='')}")
