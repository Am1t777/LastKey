# datetime and timedelta are used to compute token expiry timestamps
from datetime import datetime, timedelta

# FastAPI dependency injection helpers and HTTP exception/status utilities
from fastapi import Depends, HTTPException, status
# OAuth2PasswordBearer extracts the Bearer token from the Authorization header automatically
from fastapi.security import OAuth2PasswordBearer
# jose provides JWT encoding and decoding; JWTError is raised on invalid/expired tokens
from jose import JWTError, jwt
# CryptContext wraps bcrypt and handles password hashing and verification
from passlib.context import CryptContext
# Session is the SQLAlchemy ORM session type used for DB operations
from sqlalchemy.orm import Session

# App-wide settings (SECRET_KEY, ALGORITHM, token expiry, etc.)
from app.config import settings
# get_db is the FastAPI dependency that provides a scoped DB session
from app.database import get_db
# AuditLog model used when writing security events to the database
from app.models.audit_log import AuditLog
# User model — fetched from the DB during token validation
from app.models.user import User

# Configure the bcrypt hashing context; "deprecated=auto" auto-upgrades old hash formats
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tells FastAPI where clients send their token to obtain a new one (used in /docs UI)
# and automatically reads the Bearer token from incoming Authorization headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# hash_password turns a plain-text password into a bcrypt hash safe to store in the DB
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


# verify_password checks whether a plain-text password matches a stored bcrypt hash
# Returns True if they match, False otherwise
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# create_access_token builds a signed JWT containing the user's ID and an expiry claim
def create_access_token(user_id: int) -> str:
    # Calculate the absolute expiry time from now + configured lifetime
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # "sub" (subject) is the standard JWT claim for the entity the token represents
    payload = {"sub": str(user_id), "exp": expire}
    # Encode and sign the payload with the app secret key using HMAC-SHA256
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# get_current_user is a FastAPI dependency that validates the JWT and returns the User
# It is injected into protected route handlers via Depends(get_current_user)
def get_current_user(
    # oauth2_scheme automatically extracts the Bearer token from the Authorization header
    token: str = Depends(oauth2_scheme),
    # get_db provides a scoped DB session so we can query the users table
    db: Session = Depends(get_db),
) -> User:
    # Pre-build the 401 exception so we always return the same error regardless of failure reason
    # (avoids leaking whether the token was malformed vs. the user not existing)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        # WWW-Authenticate header tells clients to use Bearer token auth
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode and verify the JWT signature and expiry claim in one step
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Extract the user ID from the "sub" claim
        user_id: str | None = payload.get("sub")
        # If "sub" is missing the token is malformed — reject it
        if user_id is None:
            raise credentials_exception
    except JWTError:
        # Token signature invalid, malformed, or expired
        raise credentials_exception

    # Look up the user by ID to make sure they still exist and are not deactivated
    user = db.query(User).filter(User.id == int(user_id)).first()
    # Return 401 for non-existent or soft-deleted users — same error as invalid token
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# log_audit writes a single immutable audit log entry to the database
def log_audit(
    db: Session,            # Active DB session to write into
    user_id: int | None,    # The acting user (None for pre-auth events like failed logins)
    action: str,            # Dot-namespaced event name e.g. "user.login", "secret.delete"
    details: str | None = None,     # Optional extra context (JSON string, email, title, etc.)
    ip_address: str | None = None,  # Client IP for forensic tracing
) -> None:
    # Create the AuditLog row in memory
    entry = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
    )
    # Stage the new entry in the current session
    db.add(entry)
    # Persist immediately — audit logs should be written even if the outer transaction rolls back
    db.commit()
