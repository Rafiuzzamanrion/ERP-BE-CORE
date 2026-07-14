from fastapi import Request

from app.core.http_status import HttpStatus
from app.infrastructure.logging import create_logger
from app.schemas.response import ApiResponse

logger = create_logger(__name__)


class AppException(Exception):
    def __init__(
        self, message: str, status_code: int = 400, errors: list | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(message)


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        "app_exception",
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return ApiResponse.error(
        message=exc.message, status_code=exc.status_code, errors=exc.errors
    )


async def validation_exception_handler(request: Request, exc):
    errors = exc.errors() if hasattr(exc, "errors") else [{"message": str(exc)}]
    formatted = []
    for err in errors:
        formatted.append(
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", str(err)),
            }
        )
    logger.warning("validation_error", errors=formatted, path=request.url.path)
    return ApiResponse.error(
        message="Validation failed",
        status_code=HttpStatus.UNPROCESSABLE_ENTITY,
        errors=formatted,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception", error=str(exc), path=request.url.path, exc_info=True
    )
    return ApiResponse.error(
        message="Internal server error", status_code=HttpStatus.INTERNAL_SERVER_ERROR
    )
