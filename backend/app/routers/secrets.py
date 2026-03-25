# FastAPI routing, query parameters, HTTP exceptions, request object, and status codes
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
# SQLAlchemy session for DB access
from sqlalchemy.orm import Session

# Database session dependency
from app.database import get_db
# User ORM model — needed to type the current_user dependency
from app.models.user import User
# Generic message response schema
from app.schemas.auth import MessageResponse
# All secret-related Pydantic schemas
from app.schemas.secret import (
    SecretAssignRequest,   # Body for the /assign endpoint: password + beneficiary_id
    SecretCreate,          # Body for creating a secret: title, content, type, password, beneficiary_ids
    SecretListResponse,    # Paginated list of secrets: items, total, page, has_more
    SecretResponse,        # Full secret detail (includes encrypted fields for owner decryption)
    SecretUpdate,          # Body for updating a secret: optional title, content, type, password
    SecretListItem,        # Lightweight item used in list responses (no encrypted content)
)
# JWT validation dependency and audit logging
from app.services.auth_service import get_current_user, log_audit
# Business logic functions for secret operations
from app.services.secret_service import (
    assign_secret,       # Post-creation assignment of a secret to a beneficiary
    create_secret,       # Encrypts and stores a new secret
    get_secret_or_404,   # Fetches a secret by ID with ownership check
    update_secret,       # Updates an existing secret's content/metadata
)
# Secret ORM model — used directly for list queries
from app.models.secret import Secret

# Group all secret endpoints under /api/secrets with the "Secrets" tag in Swagger
router = APIRouter(prefix="/api/secrets", tags=["Secrets"])

# Hard cap on page size to prevent clients from requesting huge result sets
_MAX_PAGE_SIZE = 100


# POST /api/secrets — create a new encrypted secret
@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: SecretCreate,                             # Validated request body
    request: Request,                               # Needed to read the client IP for audit logging
    current_user: User = Depends(get_current_user), # JWT-authenticated user
    db: Session = Depends(get_db),                  # Scoped DB session
):
    # Delegate all encryption and DB operations to the secret service
    secret = create_secret(
        db=db,
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        secret_type=body.secret_type,
        password=body.password,
        beneficiary_ids=body.beneficiary_ids,
    )
    # Record the create event in the audit log (title is included; content is never logged)
    log_audit(
        db,
        current_user.id,
        "secret.create",
        details=f"title={body.title}",
        ip_address=request.client.host,
    )
    return secret


# GET /api/secrets — list the current user's secrets with pagination
@router.get("", response_model=SecretListResponse)
def list_secrets(
    # page defaults to 1; must be >= 1
    page: int = Query(default=1, ge=1),
    # page_size defaults to 20; capped at _MAX_PAGE_SIZE to prevent huge queries
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Base query filters to only the current user's secrets
    base_query = db.query(Secret).filter(Secret.user_id == current_user.id)
    # Get the total count before applying pagination (needed for the "has_more" flag)
    total = base_query.count()
    # Fetch the requested page, ordered newest-first
    items = (
        base_query.order_by(Secret.created_at.desc())
        # Skip the preceding pages
        .offset((page - 1) * page_size)
        # Return at most page_size items
        .limit(page_size)
        .all()
    )
    return SecretListResponse(
        # Serialize each Secret ORM object into a SecretListItem Pydantic model
        items=[SecretListItem.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        # True if there are more results beyond the current page
        has_more=(page * page_size) < total,
    )


# GET /api/secrets/{secret_id} — retrieve a single secret by ID
@router.get("/{secret_id}", response_model=SecretResponse)
def get_one(
    secret_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch and verify ownership in one step — raises 404 if not found or wrong owner
    secret = get_secret_or_404(db, secret_id, current_user.id)
    # Log every read so we have a trail of who accessed what
    log_audit(
        db,
        current_user.id,
        "secret.read",
        details=f"secret_id={secret_id}",
        ip_address=request.client.host,
    )
    return secret


# PUT /api/secrets/{secret_id} — update a secret's title, content, and/or type
@router.put("/{secret_id}", response_model=SecretResponse)
def update(
    secret_id: int,
    body: SecretUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Require at least one field to update — prevents no-op requests
    if body.title is None and body.content is None and body.secret_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )
    # Verify the secret exists and belongs to the current user
    secret = get_secret_or_404(db, secret_id, current_user.id)
    # Delegate re-encryption and DB update to the service layer
    updated = update_secret(
        db=db,
        secret=secret,
        title=body.title,
        content=body.content,
        secret_type=body.secret_type,
        password=body.password,
    )
    # Audit the update event
    log_audit(
        db,
        current_user.id,
        "secret.update",
        details=f"secret_id={secret_id}",
        ip_address=request.client.host,
    )
    return updated


# DELETE /api/secrets/{secret_id} — permanently delete a secret and its assignments
@router.delete("/{secret_id}", response_model=MessageResponse)
def delete(
    secret_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership before allowing deletion
    secret = get_secret_or_404(db, secret_id, current_user.id)
    # Capture the title before deleting so we can include it in the audit log
    title = secret.title
    # Delete the Secret row — cascade deletes all SecretAssignment rows automatically
    db.delete(secret)
    db.commit()
    # Audit the deletion including the title (the secret is gone, but the log remains)
    log_audit(
        db,
        current_user.id,
        "secret.delete",
        details=f"secret_id={secret_id}, title={title}",
        ip_address=request.client.host,
    )
    return MessageResponse(message="Secret deleted")


# POST /api/secrets/{secret_id}/assign — assign an existing secret to a beneficiary
@router.post("/{secret_id}/assign", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def assign(
    secret_id: int,
    body: SecretAssignRequest,  # Contains the owner's password and the beneficiary ID
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify the secret exists and belongs to the current user
    secret = get_secret_or_404(db, secret_id, current_user.id)
    # Decrypt the AES key using the owner's password, then re-encrypt for the beneficiary
    assign_secret(db=db, secret=secret, password=body.password, beneficiary_id=body.beneficiary_id)
    # Audit the assignment event
    log_audit(
        db,
        current_user.id,
        "secret.assign",
        details=f"secret_id={secret_id}, beneficiary_id={body.beneficiary_id}",
        ip_address=request.client.host,
    )
    return MessageResponse(message="Secret assigned to beneficiary")
