class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.original_error = original_error
