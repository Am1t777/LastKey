from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.secret import (
    SecretAssignRequest,
    SecretCreate,
    SecretListResponse,
    SecretResponse,
    SecretUpdate,
    SecretListItem,
)
from app.services.auth_service import get_current_user, log_audit
from app.services.secret_service import (
    assign_secret,
    create_secret,
    get_secret_or_404,
    update_secret,
)
from app.models.secret import Secret

router = APIRouter(prefix="/api/secrets", tags=["Secrets"])

_MAX_PAGE_SIZE = 100


@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: SecretCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    secret = create_secret(
        db=db,
        user_id=current_user.id,
        title=body.title,
        content=body.content,
        secret_type=body.secret_type,
        password=body.password,
        beneficiary_ids=body.beneficiary_ids,
    )
    log_audit(
        db,
        current_user.id,
        "secret.create",
        details=f"title={body.title}",
        ip_address=request.client.host,
    )
    return secret


@router.get("", response_model=SecretListResponse)
def list_secrets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=_MAX_PAGE_SIZE),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_query = db.query(Secret).filter(Secret.user_id == current_user.id)
    total = base_query.count()
    items = (
        base_query.order_by(Secret.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return SecretListResponse(
        items=[SecretListItem.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{secret_id}", response_model=SecretResponse)
def get_one(
    secret_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    secret = get_secret_or_404(db, secret_id, current_user.id)
    log_audit(
        db,
        current_user.id,
        "secret.read",
        details=f"secret_id={secret_id}",
        ip_address=request.client.host,
    )
    return secret


@router.put("/{secret_id}", response_model=SecretResponse)
def update(
    secret_id: int,
    body: SecretUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.title is None and body.content is None and body.secret_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )
    secret = get_secret_or_404(db, secret_id, current_user.id)
    updated = update_secret(
        db=db,
        secret=secret,
        title=body.title,
        content=body.content,
        secret_type=body.secret_type,
        password=body.password,
    )
    log_audit(
        db,
        current_user.id,
        "secret.update",
        details=f"secret_id={secret_id}",
        ip_address=request.client.host,
    )
    return updated


@router.delete("/{secret_id}", response_model=MessageResponse)
def delete(
    secret_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    secret = get_secret_or_404(db, secret_id, current_user.id)
    title = secret.title
    db.delete(secret)  # cascade deletes SecretAssignment rows
    db.commit()
    log_audit(
        db,
        current_user.id,
        "secret.delete",
        details=f"secret_id={secret_id}, title={title}",
        ip_address=request.client.host,
    )
    return MessageResponse(message="Secret deleted")


@router.post("/{secret_id}/assign", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def assign(
    secret_id: int,
    body: SecretAssignRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    secret = get_secret_or_404(db, secret_id, current_user.id)
    assign_secret(db=db, secret=secret, password=body.password, beneficiary_id=body.beneficiary_id)
    log_audit(
        db,
        current_user.id,
        "secret.assign",
        details=f"secret_id={secret_id}, beneficiary_id={body.beneficiary_id}",
        ip_address=request.client.host,
    )
    return MessageResponse(message="Secret assigned to beneficiary")
