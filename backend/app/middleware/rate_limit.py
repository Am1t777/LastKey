from slowapi import Limiter
from slowapi.util import get_remote_address

# NOTE: Uses in-memory storage. Rate limit state does not persist across
# process restarts and does not work correctly with multiple Uvicorn workers.
# For production with multiple workers, switch to a Redis backend.
limiter = Limiter(key_func=get_remote_address)
