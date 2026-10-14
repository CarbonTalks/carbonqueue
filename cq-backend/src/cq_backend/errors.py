class BackendError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 503,
        application_id: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.application_id = application_id
