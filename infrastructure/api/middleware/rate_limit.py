import time
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.
    
    LIMITATION: This implementation uses in-memory storage (defaultdict).
    - Does NOT persist across worker restarts
    - Does NOT share state between multiple workers
    
    If running with multiple uvicorn workers (--workers N), the rate limit
    is applied per-worker, not globally. For production-grade rate limiting,
    migrate to Redis-based storage (e.g., slowapi with Redis backend).
    
    TODO: Migrate to slowapi + Redis for multi-worker support:
        pip install slowapi
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
    
    For now, ensure the server runs with --workers 1 in production.
    """
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def _cleanup_old_requests(self, ip: str):
        current_time = time.time()
        cutoff = current_time - 60
        self.requests[ip] = [ts for ts in self.requests[ip] if ts > cutoff]

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        self._cleanup_old_requests(client_ip)

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429, detail="Too many requests. Please try again later."
            )

        self.requests[client_ip].append(time.time())

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"
