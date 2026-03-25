# BaseHTTPMiddleware is the Starlette base class for writing custom ASGI middleware
from starlette.middleware.base import BaseHTTPMiddleware

# Swagger UI and ReDoc need relaxed CSP because they load inline scripts and styles
_SWAGGER_PATHS = ("/docs", "/redoc", "/openapi.json")


# SecurityHeadersMiddleware injects defensive HTTP response headers into every response
# These headers instruct the browser to enforce stricter security policies
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Let the actual route handler process the request first
        response = await call_next(request)

        # X-Content-Type-Options: nosniff — prevents browsers from MIME-sniffing responses
        # (stops an attacker from tricking a browser into executing a response as a different type)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: DENY — prevents the app from being embedded in <iframe> or <frame>
        # This blocks clickjacking attacks where the app is overlaid on a malicious page
        response.headers["X-Frame-Options"] = "DENY"

        # Strict-Transport-Security — tells browsers to always use HTTPS for this domain
        # max-age=31536000 = 1 year; includeSubDomains extends the policy to all subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer-Policy — controls how much URL information is sent in the Referer header
        # "strict-origin-when-cross-origin" sends the origin (no path) for cross-origin requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy — disables browser features the app doesn't need
        # Denying geolocation, microphone, and camera prevents accidental or malicious access
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if any(request.url.path.startswith(p) for p in _SWAGGER_PATHS):
            # Swagger/ReDoc need to run inline scripts and styles — use a relaxed CSP for those paths only
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:"
            )
        else:
            # All API endpoints return JSON — they should never load any resources at all
            # "default-src 'none'" blocks everything; "frame-ancestors 'none'" reinforces anti-framing
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response
