from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.beneficiary import Beneficiary
from app.models.secret_assignment import SecretAssignment
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.beneficiary import (
    BeneficiaryCreate,
    BeneficiaryResponse,
    BeneficiaryUpdate,
    BeneficiaryWithKeyResponse,
    SecretAssignmentInfo,
)
from app.services.auth_service import get_current_user, log_audit
from app.services.encryption_service import generate_rsa_keypair

router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiaries"])


def _get_beneficiary_or_404(db: Session, beneficiary_id: int, user_id: int) -> Beneficiary:
    """Fetch a beneficiary by ID ensuring it belongs to the current user. Returns 404 for both
    not-found and wrong-owner cases to avoid leaking existence information."""
    b = (
        db.query(Beneficiary)
        .filter(Beneficiary.id == beneficiary_id, Beneficiary.user_id == user_id)
        .first()
    )
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")
    return b


def _to_response(b: Beneficiary) -> BeneficiaryResponse:
    return BeneficiaryResponse(
        id=b.id,
        name=b.name,
        email=b.email,
        has_key=b.public_key is not None,
    )


@router.post("", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
def add_beneficiary(
    body: BeneficiaryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Prevent duplicate email per user
    existing = (
        db.query(Beneficiary)
        .filter(Beneficiary.user_id == current_user.id, Beneficiary.email == body.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A beneficiary with that email already exists",
        )
    b = Beneficiary(user_id=current_user.id, name=body.name, email=str(body.email))
    db.add(b)
    db.commit()
    db.refresh(b)
    log_audit(db, current_user.id, "beneficiary.add", details=str(body.email), ip_address=request.client.host)
    return _to_response(b)


@router.get("", response_model=list[BeneficiaryResponse])
def list_beneficiaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(Beneficiary).filter(Beneficiary.user_id == current_user.id).all()
    return [_to_response(b) for b in items]


@router.get("/{beneficiary_id}", response_model=BeneficiaryResponse)
def get_beneficiary(
    beneficiary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    return _to_response(b)


@router.patch("/{beneficiary_id}", response_model=BeneficiaryResponse)
def update_beneficiary(
    beneficiary_id: int,
    body: BeneficiaryUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    if body.name is not None:
        b.name = body.name
    if body.email is not None:
        b.email = str(body.email)
    db.commit()
    db.refresh(b)
    log_audit(db, current_user.id, "beneficiary.update", details=f"id={beneficiary_id}", ip_address=request.client.host)
    return _to_response(b)


@router.delete("/{beneficiary_id}", response_model=MessageResponse)
def delete_beneficiary(
    beneficiary_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    # Manually delete assignments (no cascade on Beneficiary side)
    db.query(SecretAssignment).filter(SecretAssignment.beneficiary_id == beneficiary_id).delete()
    db.delete(b)
    db.commit()
    log_audit(db, current_user.id, "beneficiary.delete", details=f"id={beneficiary_id}", ip_address=request.client.host)
    return MessageResponse(message="Beneficiary deleted")


@router.post("/{beneficiary_id}/generate-key", response_model=BeneficiaryWithKeyResponse)
def generate_key(
    beneficiary_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    if b.public_key is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Key already generated. Delete and recreate the beneficiary to reset.",
        )
    public_pem, private_pem = generate_rsa_keypair()
    b.public_key = public_pem
    db.commit()
    db.refresh(b)
    log_audit(db, current_user.id, "beneficiary.key_generated", details=b.email, ip_address=request.client.host)
    return BeneficiaryWithKeyResponse(
        id=b.id,
        name=b.name,
        email=b.email,
        has_key=True,
        private_key_pem=private_pem,
    )


@router.get("/{beneficiary_id}/secrets", response_model=list[SecretAssignmentInfo])
def list_assigned_secrets(
    beneficiary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    assignments = (
        db.query(SecretAssignment)
        .filter(SecretAssignment.beneficiary_id == beneficiary_id)
        .all()
    )
    return assignments
