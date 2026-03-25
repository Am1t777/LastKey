# Limiter is the core slowapi class that tracks request counts per client
from slowapi import Limiter
# get_remote_address extracts the client's IP address from the incoming request
# and uses it as the key for counting requests (one counter per IP)
from slowapi.util import get_remote_address

# NOTE: Uses in-memory storage. Rate limit state does not persist across
# process restarts and does not work correctly with multiple Uvicorn workers.
# For production with multiple workers, switch to a Redis backend.

# Create a single shared Limiter instance imported by route handlers that need rate limiting
# key_func=get_remote_address means each unique client IP has its own independent counter
limiter = Limiter(key_func=get_remote_address)
