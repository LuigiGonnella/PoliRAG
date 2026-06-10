"""Application-level errors converted to API responses."""


class AppError(Exception):
    status_code = 500
    error = "application_error"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404
    error = "not_found"


class ConfigurationError(AppError):
    status_code = 503
    error = "configuration_error"


class AgentExecutionError(AppError):
    status_code = 502
    error = "agent_execution_error"
