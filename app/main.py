import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.error_handlers import app_error_handler
from app.api.routes import health, tags, values
from app.core.config import settings
from app.core.logging import generate_request_id, request_id_var, setup_logging
from app.exceptions import AppError

setup_logging(settings.log_level)

app = FastAPI(title="Cloud Atlas Tags API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.include_router(health.router)
app.include_router(tags.router)
app.include_router(values.router)

logger = logging.getLogger("uvicorn.access")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: object) -> Response:
    rid = request.headers.get("X-Request-ID")
    if not rid:
        rid = generate_request_id()
    request_id_var.set(rid)
    start = time.perf_counter()
    response: Response = await call_next(request)  # type: ignore[operator]
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = rid
    logger.info(
        "",
        extra={
            "request_id": rid,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
