"""Shapes of what the API returns, for type checkers and editors — plain dicts at runtime."""

from typing import Any, Dict, Literal, Optional, TypedDict

CheckoutSessionStatus = Literal["open", "completed", "expired", "canceled"]


class _CheckoutSessionFields(TypedDict):
    id: str
    status: CheckoutSessionStatus
    checkout_url: str
    amount: float
    currency: str
    external_reference: Optional[str]
    metadata: Optional[Dict[str, Any]]
    expires_at: str


class CheckoutSession(_CheckoutSessionFields, total=False):
    # present (True) when this external_reference had already created the session
    idempotent_replay: bool


class CheckoutSessionDetails(_CheckoutSessionFields):
    transaction_id: Optional[str]
    # "approved" is the only status that means paid
    transaction_status: Optional[Literal["pending", "approved", "rejected"]]
    created_at: str


class _WebhookPayloadFields(TypedDict):
    transaction_id: str
    external_reference: Optional[str]
    # only final statuses are sent
    status: Literal["approved", "rejected"]
    amount: float
    currency: str
    customer_phone: Optional[str]
    created_at: str
    updated_at: str


class WebhookPayload(_WebhookPayloadFields, total=False):
    # a hosted checkout's webhook names its session and echoes its metadata
    checkout_session_id: str
    metadata: Optional[Dict[str, Any]]
