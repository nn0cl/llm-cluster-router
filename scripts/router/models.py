"""Shared error and provider request types for the router boundary."""


class ClusterConfigError(Exception):
    pass


class PathValidationError(Exception):
    pass


class RoutingError(Exception):
    pass


class ProviderExecutionError(Exception):
    pass


class ProviderRequestError(ProviderExecutionError):
    def __init__(
        self,
        message,
        category,
        retryable,
        status_code=None,
        retry_after=None,
        request_id=None,
        detail=None,
        operation=None,
        model=None,
        attempt=None,
        max_attempts=None,
    ):
        super().__init__(message)
        self.category = category
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after = retry_after
        self.request_id = request_id
        self.detail = detail
        self.operation = operation
        self.model = model
        self.attempt = attempt
        self.max_attempts = max_attempts
