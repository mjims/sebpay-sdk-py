# sebpay-python

Official Python SDK for [Sebpay](https://sebpay.africa) **hosted checkout**. It does four things:
- create a checkout session;
- redirect your customer to the Sebpay payment page;
- confirm the payment when they come back;
- verify Sebpay's webhooks.

Its only dependency is `requests`. Direct collections, payouts and reference data are not part of the SDK. They remain available over plain HTTP: see [`docs/SEBPAY_PUBLIC_API.md`](../../docs/SEBPAY_PUBLIC_API.md).

## Install

Not yet published on PyPI. For now, install it from the repository:

```bash
pip install ../sebpay/sdks/python
```

## Usage

### 1. Create a session and redirect your customer

```python
import os
from sebpay import SebpayClient

# Keys from your dashboard (API développeur): pk_test_ keys go to the sandbox server, pk_live_ keys to live.
sebpay = SebpayClient(os.environ["SEBPAY_PUBLIC_KEY"], os.environ["SEBPAY_SECRET_KEY"])

session = sebpay.checkout_sessions.create(
    amount=5000,
    currency="XOF",
    redirect_url="https://yoursite.com/orders/return",
    external_reference=order.id,  # your order id: sending it again returns the same session
    callback_url="https://yoursite.com/webhook/sebpay",
    metadata={"order_id": order.id},
)

return redirect(session["checkout_url"])
```

### 2. Confirm the payment when your customer comes back

Your `redirect_url` receives `?checkout_session_id=<id>`. Coming back proves nothing, so ask Sebpay before you deliver:

```python
session = sebpay.checkout_sessions.retrieve(request.args["checkout_session_id"])

if session["transaction_status"] == "approved":
    ...  # Paid: deliver the order (session["external_reference"], session["metadata"]).
```

`retrieve()` also accepts your `external_reference`.

### 3. Verify the webhook

Sebpay POSTs the final status (`approved` or `rejected`) to your `callback_url`. For a checkout, the request also carries `checkout_session_id` and your `metadata`.

```python
from sebpay import SIGNATURE_HEADER, verify_signature

# With Flask:
if not verify_signature(request.get_data(), request.headers.get(SIGNATURE_HEADER), os.environ["SEBPAY_SECRET_KEY"]):
    return {"error": "Invalid signature"}, 401

payload = request.get_json()  # payload["status"]: "approved" | "rejected"
```

- Always pass the **raw** request body. Re-serializing a parsed payload can reorder keys and break the signature.
- A missing header returns `False`.

The shapes of the session and of the webhook payload are described as `TypedDict`s in `sebpay.types`, for editors and type checkers.

## Options

```python
SebpayClient(public_key, secret_key,
             base_url="http://localhost:8000/api/v1",  # only to test against a local API; otherwise chosen from the keys
             timeout=10)                               # seconds, default 30
```

`sebpay.base_url` tells which server the client talks to.

## Errors

Every failed call raises a `SebpayApiError`, with three attributes:
- `status`: the HTTP status, or 0 when no response came back;
- `code`: the API's `errors.code`, or one of the SDK's own codes. Examples: `EXTERNAL_REFERENCE_CONFLICT`, `RATE_LIMITED`, `WRONG_ENVIRONMENT`, `NETWORK_ERROR`, `TIMEOUT`, `INVALID_RESPONSE`. It is `None` otherwise;
- `body`: the decoded response.

```python
from sebpay import SebpayApiError

try:
    sebpay.checkout_sessions.create(...)
except SebpayApiError as e:
    if e.code == "EXTERNAL_REFERENCE_CONFLICT":
        ...  # This order id was already used with other parameters.
```

## Examples

See [`examples/`](examples/). Set `SEBPAY_PUBLIC_KEY` and `SEBPAY_SECRET_KEY`, then:
- `python examples/create_checkout.py` creates a session and prints its `checkout_url`;
- `python examples/webhook_server.py` starts a Flask server (`pip install flask`) that handles the webhook and the return page, on `PORT` (default 3002).

For local testing, also set `SEBPAY_BASE_URL`.

## Tests

`python -m unittest discover -s tests` runs the SDK's offline tests. They cover the transport, against a local HTTP server, and the shared signature vectors.

## Requirements

Python 3.9+ and `requests`.
