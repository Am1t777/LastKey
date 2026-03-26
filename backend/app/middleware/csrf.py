# BaseHTTPMiddleware is the Starlette base class for writing custom ASGI middleware
from starlette.middleware.base import BaseHTTPMiddleware
# JSONResponse lets us return a structured JSON error body from the middleware layer
from starlette.responses import JSONResponse

# These public endpoints are called directly from email client links —
# JavaScript cannot set custom headers there, so they are CSRF-exempt.
# They are protected by their own opaque tokens instead.
_CSRF_EXEMPT_PREFIXES = ("/api/checkin", "/api/verify/")

# Only state-changing HTTP methods need CSRF protection
# GET and HEAD are safe (read-only) and OPTIONS is used for CORS preflight
_STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


# CSRFMiddleware blocks cross-site request forgery by requiring a custom header
# Browsers never attach custom headers to cross-origin requests without a CORS preflight,
# so checking for "X-Requested-With" is an effective and lightweight CSRF defence
class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if (
            # Only apply the check to state-changing HTTP methods
            request.method in _STATE_CHANGING_METHODS
            # Only apply to our own API routes (not static files or public pages)
            and request.url.path.startswith("/api/")
            # Skip routes that are deliberately exempt (email-link endpoints)
            and not any(request.url.path.startswith(p) for p in _CSRF_EXEMPT_PREFIXES)
        ):
            # The frontend axios instance always sets this header on every API call
            # An attacker's forged cross-origin form submission cannot set custom headers
            if "x-requested-with" not in request.headers:
                # Return 403 immediately — do not pass the request to the route handler
                return JSONResponse(
                    {"detail": "Missing X-Requested-With header"}, status_code=403
                )
        # Header is present (or route is exempt) — pass the request through to the next layer
        return await call_next(request)
