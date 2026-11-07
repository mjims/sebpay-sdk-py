import hashlib
import hmac
from typing import Optional, Union

SIGNATURE_HEADER = "X-SebPay-Signature"


def verify_signature(raw_body: Union[bytes, str], signature: Optional[str], secret_key: str) -> bool:
    """Verify the `X-SebPay-Signature` header Sebpay sends with every webhook
    callback. Always pass the raw request body — re-serializing a parsed
    payload (e.g. via json.dumps after parsing) can reorder keys and break
    the signature. A missing signature returns False.
    """
    if not isinstance(signature, str) or not signature:
        return False
    if isinstance(raw_body, str):
        raw_body = raw_body.encode("utf-8")
    if not isinstance(raw_body, (bytes, bytearray)):
        return False

    expected = hmac.new(secret_key.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.encode("ascii"), signature.encode("utf-8"))
