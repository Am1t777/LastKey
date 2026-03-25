# datetime provides utcnow() to initialize last_check_in_at at registration time
from datetime import datetime

# FastAPI routing, dependency injection, HTTP exceptions, request object, and status codes
from fastapi import APIRouter, Depends, HTTPException, Request, status
# SQLAlchemy session for DB access
from sqlalchemy.orm import Session

# Database session dependency
from app.database import get_db
# User ORM model used to query and create user accounts
from app.models.user import User
# Pydantic request/response schemas for this router
from app.schemas.auth import (
    MessageResponse,   # Generic {"message": "..."} response body
    TokenResponse,     # {"access_token": "..."} response body
    UserLogin,         # Email + password login request body
    UserRegister,      # Email + password + name registration request body
    UserResponse,      # Public user profile (no password hash)
)
# Rate limiter instance — shared with all other rate-limited routes
from app.middleware.rate_limit import limiter
# Service helpers for password operations, token creation, JWT validation, and audit logging
from app.services.auth_service import (
    create_access_token,  # Builds and signs a JWT for the user
    get_current_user,     # FastAPI dependency that validates the JWT and returns the User
    hash_password,        # Hashes a plain-text password with bcrypt
    log_audit,            # Writes an event to the audit_logs table
    verify_password,      # Checks a plain-text password against a bcrypt hash
)

# Group all auth endpoints under /api/auth with the "Authentication" tag in Swagger
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# POST /api/auth/register — create a new account and return a JWT
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
# Rate-limited to 5 attempts per minute per IP to prevent account enumeration / credential stuffing
@limiter.limit("5/minute")
def register(body: UserRegister, request: Request, db: Session = Depends(get_db)):
    # Check whether the email is already in use — emails must be globally unique
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Build a new User row — password is stored as a bcrypt hash, never in plaintext
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),  # Hash before storing
        name=body.name,
        # Initialize last_check_in_at to now so the first deadline is check_in_interval_days from registration
        last_check_in_at=datetime.utcnow(),
    )
    # Stage the new user for insertion
    db.add(user)
    # Persist to the database and populate user.id
    db.commit()
    # Reload the user object to get any DB-generated defaults
    db.refresh(user)

    # Write a registration event to the audit log for forensic tracing
    log_audit(db, user.id, "user.register", ip_address=request.client.host)

    # Issue a JWT so the newly-registered user is immediately logged in
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


# POST /api/auth/login — verify credentials and return a JWT
@router.post("/login", response_model=TokenResponse)
# Rate-limited to 5 attempts per minute per IP to slow brute-force password attacks
@limiter.limit("5/minute")
def login(body: UserLogin, request: Request, db: Session = Depends(get_db)):
    # Look up the user by email (email is unique and indexed)
    user = db.query(User).filter(User.email == body.email).first()
    # Verify the password — if either the user doesn't exist or the password is wrong,
    # return the same generic error (prevents email enumeration)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reject login for soft-deleted accounts (is_active=False)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Record the successful login in the audit log
    log_audit(db, user.id, "user.login", ip_address=request.client.host)

    # Issue a new JWT for this session
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


# GET /api/auth/me — return the currently authenticated user's profile
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    # get_current_user validates the JWT and fetches the User from the DB
    # We just return it — Pydantic/FastAPI serialises it to UserResponse automatically
    return current_user


# POST /api/auth/logout — log the user out (client-side JWT deletion + audit event)
@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    # Validates the JWT — only authenticated users can call logout
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Write the logout event to the audit log before the token is discarded
    log_audit(db, current_user.id, "user.logout", ip_address=request.client.host)
    # JWT is stateless — no server-side invalidation needed.
    # A token blocklist could be added later for true invalidation.
    # The client removes the token from localStorage upon receiving this response.
    return MessageResponse(message="Logged out successfully")
