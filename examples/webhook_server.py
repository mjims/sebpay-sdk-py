# A minimal Flask server for both ends of a hosted checkout:
#   POST /webhook/sebpay  — the signed notification Sebpay sends to your callback_url;
#   GET  /orders/return   — your redirect_url, where the customer lands with ?checkout_session_id=…
# pip install flask, then: python examples/webhook_server.py
# (env: SEBPAY_PUBLIC_KEY, SEBPAY_SECRET_KEY, optional SEBPAY_BASE_URL and PORT)

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, request

from sebpay import SIGNATURE_HEADER, SebpayApiError, SebpayClient, verify_signature

app = Flask(__name__)
SECRET_KEY = os.environ.get("SEBPAY_SECRET_KEY", "sk_test_your_secret")
sebpay = SebpayClient(os.environ.get("SEBPAY_PUBLIC_KEY", "pk_test_your_key"), SECRET_KEY, base_url=os.environ.get("SEBPAY_BASE_URL"))


@app.post("/webhook/sebpay")
def handle_webhook():
    if not verify_signature(request.get_data(), request.headers.get(SIGNATURE_HEADER), SECRET_KEY):
        return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json()

    if payload["status"] == "approved":
        pass  # Fulfil the order identified by payload["external_reference"] (or payload["metadata"]).
    elif payload["status"] == "rejected":
        pass  # Notify the customer of the failed payment.

    return jsonify({"received": True}), 200


@app.get("/orders/return")
def handle_return():
    session_id = request.args.get("checkout_session_id", "")

    if not session_id:
        return jsonify({"error": "Missing checkout_session_id"}), 400

    try:
        # Coming back proves nothing: ask Sebpay, and deliver only an approved payment.
        session = sebpay.checkout_sessions.retrieve(session_id)
    except SebpayApiError as e:
        if e.status == 404:
            return jsonify({"error": "Unknown checkout session"}), 404
        return jsonify({"error": "Could not confirm the payment, try again"}), 502

    return jsonify({
        "paid": session["transaction_status"] == "approved",
        "status": session["status"],
        "external_reference": session["external_reference"],
    })


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 3002)))
