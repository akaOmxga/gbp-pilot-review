class GoogleApiError(Exception):
    pass


class GoogleAuthError(GoogleApiError):
    """401 / invalid_grant — token revoked or expired non-refreshable."""


class GoogleRateLimitError(GoogleApiError):
    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("Rate limited by Google API")
        self.retry_after = retry_after


class GoogleApi5xxError(GoogleApiError):
    pass


class GoogleNetworkError(GoogleApiError):
    pass
