from contextlib import asynccontextmanager

import socketio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.http_status import HttpStatus
from app.infrastructure.cloudinary import init_cloudinary
from app.infrastructure.logging import LoggingMiddleware, create_logger, setup_logging
from app.infrastructure.mongo.client import close_db, init_db
from app.infrastructure.rate_limiter import limiter
from app.router import router as api_router
from app.schemas.response import ApiResponse
from app.socketio import sio

setup_logging()
logger = create_logger("main")


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return ApiResponse.error(
        "Too many requests. Please try again later.", HttpStatus.TOO_MANY_REQUESTS
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    await init_db()
    init_cloudinary()
    logger.info("server_started", port=settings.PORT, env=settings.NODE_ENV)
    yield
    await close_db()
    logger.info("server_shutdown")


app = FastAPI(
    title="ERP Inventory & Sales Management API",
    version="1.0.0",
    docs_url="/api-docs",
    openapi_url="/api-docs.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.client_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router, prefix="/api/v1")

socket_app = socketio.ASGIApp(sio, app)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:socket_app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.is_development,
    )

x = 1
y = 2
