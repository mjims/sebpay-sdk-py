import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sebpay import SebpayClient

# Keys from your dashboard (API développeur): pk_test_ keys go to the sandbox server, pk_live_ keys to live.
sebpay = SebpayClient(
    public_key=os.environ.get("SEBPAY_PUBLIC_KEY", "pk_test_your_key"),
    secret_key=os.environ.get("SEBPAY_SECRET_KEY", "sk_test_your_secret"),
    base_url=os.environ.get("SEBPAY_BASE_URL"),  # e.g. http://localhost:8000/api/v1 for local testing
)

# One checkout session per order: your order id is the external_reference.
order_id = f"ORDER-{int(time.time())}"

session = sebpay.checkout_sessions.create(
    amount=5000,
    currency="XOF",
    redirect_url=os.environ.get("RETURN_URL", "https://yoursite.com/orders/return"),
    external_reference=order_id,
    callback_url=os.environ.get("CALLBACK_URL", "https://yoursite.com/webhook/sebpay"),
    metadata={"order_id": order_id},
)

print(f"Redirect your customer to: {session['checkout_url']}")
