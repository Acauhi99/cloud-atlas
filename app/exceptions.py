class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        title: str = "Error",
        type_url: str = "about:blank",
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.title = title
        self.type_url = type_url
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=404, detail=detail, title="Not Found")


class ConflictError(AppError):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(status_code=409, detail=detail, title="Conflict")
