# asynccontextmanager lets us define startup/shutdown logic as an async generator
from contextlib import asynccontextmanager

# FastAPI is the web framework that handles HTTP routing, validation, and serialization
from fastapi import FastAPI
# CORSMiddleware allows the browser frontend (on a different port) to call this API
from fastapi.middleware.cors import CORSMiddleware
# _rate_limit_exceeded_handler returns a 429 response when a rate limit is hit
from slowapi import _rate_limit_exceeded_handler
# RateLimitExceeded is the exception raised by slowapi when the rate limit is breached
from slowapi.errors import RateLimitExceeded

# settings is a singleton holding all environment/config values (DB URL, secrets, etc.)
from app.config import settings
# Base is the SQLAlchemy declarative base; engine is the DB connection
from app.database import Base, engine
# CSRFMiddleware blocks state-changing requests that lack the X-Requested-With header
from app.middleware.csrf import CSRFMiddleware
# limiter is the slowapi rate-limiter instance shared by all route decorators
from app.middleware.rate_limit import limiter
# SecurityHeadersMiddleware injects security-related HTTP headers into every response
from app.middleware.security_headers import SecurityHeadersMiddleware
# Each router groups related endpoints under a common URL prefix
from app.routers.auth import router as auth_router
from app.routers.beneficiaries import router as beneficiaries_router
from app.routers.checkin import router as checkin_router
from app.routers.release import router as release_router
from app.routers.secrets import router as secrets_router
from app.routers.settings import router as settings_router
# verifier has two routers: one protected (JWT) and one public (token-based)
from app.routers.verifier import public_verify_router, router as verifier_router
# run_checkin_job is the daily cron function; scheduler is the APScheduler instance
from app.services.scheduler import run_checkin_job, scheduler
# Importing all models registers their metadata with Base before create_all is called
import app.models  # noqa: F401 — ensures all models are registered before create_all

# Create all database tables defined by SQLAlchemy models (idempotent — skips existing tables)
Base.metadata.create_all(bind=engine)


# lifespan is an async context manager that runs code before the server starts (startup)
# and after it stops (shutdown) — the `yield` separates the two phases
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register the daily check-in enforcement job to run every day at 02:00 UTC
    scheduler.add_job(run_checkin_job, "cron", hour=2, minute=0, id="daily_checkin")
    # Start the background scheduler so cron jobs begin executing
    scheduler.start()
    # yield hands control back to FastAPI to serve requests
    yield
    # After the server shuts down, gracefully stop the scheduler to prevent orphaned threads
    scheduler.shutdown()


# Create the FastAPI application instance with metadata for auto-generated API docs
app = FastAPI(
    title="LastKey API",
    description="Digital Inheritance Vault — secure secrets released to beneficiaries via dead man's switch",
    version="0.1.0",
    # Pass the lifespan context manager so startup/shutdown hooks fire correctly
    lifespan=lifespan,
    # Hide /docs and /redoc in production to reduce the attack surface
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
)

# Attach the rate limiter to the app's state so slowapi can find it via request.app.state
app.state.limiter = limiter
# Register the handler that converts RateLimitExceeded exceptions into HTTP 429 responses
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware stack (registered in this order = applied outer-to-inner at runtime):
# SecurityHeadersMiddleware is outermost — it adds security headers to ALL responses
app.add_middleware(SecurityHeadersMiddleware)
# CSRFMiddleware checks state-changing /api/* requests for the X-Requested-With header
app.add_middleware(CSRFMiddleware)
# CORSMiddleware whitelists the React frontend origin and the allowed request headers
app.add_middleware(
    CORSMiddleware,
    # Only allow requests from the configured frontend URL (not wildcard *)
    allow_origins=[settings.FRONTEND_URL],
    # Allow cookies and Authorization headers to be sent cross-origin
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS)
    allow_methods=["*"],
    # Only allow the three headers the frontend actually sends
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Mount each router — they add their endpoints under their respective URL prefixes
app.include_router(auth_router)           # /api/auth/*
app.include_router(secrets_router)        # /api/secrets/*
app.include_router(beneficiaries_router)  # /api/beneficiaries/*
app.include_router(verifier_router)       # /api/verifier/*
app.include_router(public_verify_router)  # /api/verify/* (public, token-based)
app.include_router(checkin_router)        # /api/checkin/*
app.include_router(release_router)        # /api/release/*
app.include_router(settings_router)       # /api/settings/*


# Simple health-check endpoint used by load balancers and deployment tooling
@app.get("/health")
def health_check():
    # Returns the current environment name so ops teams can verify which build is running
    return {"status": "ok", "env": settings.APP_ENV}
