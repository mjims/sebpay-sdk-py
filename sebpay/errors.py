from typing import Any, Optional


class SebpayApiError(Exception):
    """Raised for every failed call.

    status: the HTTP status, or 0 when no response came back (code "NETWORK_ERROR" or "TIMEOUT").
    code: the API's errors.code when it sends one ("EXTERNAL_REFERENCE_CONFLICT", "RATE_LIMITED",
          "WRONG_ENVIRONMENT"…), else None.
    body: the decoded response (its text when it was not JSON).
    """

    def __init__(self, message: str, status: int, body: Any = None, code: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.body = body
