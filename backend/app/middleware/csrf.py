from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# These public endpoints are called directly from email client links —
# JavaScript cannot set custom headers there, so they are CSRF-exempt.
# They are protected by their own opaque tokens instead.
_CSRF_EXEMPT_PREFIXES = ("/api/checkin", "/api/verify/")
_STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if (
            request.method in _STATE_CHANGING_METHODS
            and request.url.path.startswith("/api/")
            and not any(request.url.path.startswith(p) for p in _CSRF_EXEMPT_PREFIXES)
        ):
            if "x-requested-with" not in request.headers:
                return JSONResponse(
                    {"detail": "Missing X-Requested-With header"}, status_code=403
                )
        return await call_next(request)
