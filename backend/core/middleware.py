import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging import logger


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique X-Request-ID and X-Process-Time header to each request,
    correlating log messages and client interactions.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time_ms}ms"

        # Log request summary for observability
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time_ms}ms) [req_id={request_id}]"
        )
        return response
