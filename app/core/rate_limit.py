import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        user_id = request.headers.get("X-User-ID", "anonymous")
        now = time.time()
        window_start = now - 60

        self.requests[user_id] = [t for t in self.requests[user_id] if t > window_start]

        if len(self.requests[user_id]) >= self.requests_per_minute:
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

        self.requests[user_id].append(now)
        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[user_id])
        )
        return response
