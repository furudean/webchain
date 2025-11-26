class WebchainError(Exception):
    pass


class InvalidContentType(WebchainError):
    def __init__(self, content_type: str):
        super().__init__(f"Invalid content type: {content_type}")
        self.content_type = content_type


class InvalidStatusCode(WebchainError):
    def __init__(self, status: int, message: str | None = None):
        super().__init__(f"Status {status} not retryable: {message}")
        self.status = status


class RobotsExclusionError(WebchainError):
    pass


class ParentNotCrawledError(WebchainError):
    pass
