# FastAPI routing, dependency injection, HTTP exceptions, request object, and status codes
from fastapi import APIRouter, Depends, HTTPException, Request, status
# SQLAlchemy session for DB access
from sqlalchemy.orm import Session

# Database session dependency
from app.database import get_db
# Beneficiary ORM model
from app.models.beneficiary import Beneficiary
# SecretAssignment ORM model — needed to manually delete assignments before deleting a beneficiary
from app.models.secret_assignment import SecretAssignment
# User ORM model — type hint for current_user dependency
from app.models.user import User
# Generic message response schema
from app.schemas.auth import MessageResponse
# All beneficiary-related Pydantic schemas
from app.schemas.beneficiary import (
    BeneficiaryCreate,          # Name + email for creating a new beneficiary
    BeneficiaryResponse,        # Public beneficiary info (has_key flag, no private key)
    BeneficiaryUpdate,          # Optional name and email for updating a beneficiary
    BeneficiaryWithKeyResponse, # Like BeneficiaryResponse but also includes the newly generated private key PEM
    SecretAssignmentInfo,       # Info about a single secret assigned to a beneficiary
)
# JWT validation and audit logging
from app.services.auth_service import get_current_user, log_audit
# RSA key pair generation — used when the owner requests a key for a beneficiary
from app.services.encryption_service import generate_rsa_keypair

# Group all beneficiary endpoints under /api/beneficiaries with the "Beneficiaries" tag
router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiaries"])


# _get_beneficiary_or_404 is a shared helper for fetching a beneficiary with ownership check
def _get_beneficiary_or_404(db: Session, beneficiary_id: int, user_id: int) -> Beneficiary:
    """Fetch a beneficiary by ID ensuring it belongs to the current user. Returns 404 for both
    not-found and wrong-owner cases to avoid leaking existence information."""
    b = (
        db.query(Beneficiary)
        # Filter by both ID and user_id — prevents accessing another user's beneficiary (IDOR)
        .filter(Beneficiary.id == beneficiary_id, Beneficiary.user_id == user_id)
        .first()
    )
    if not b:
        # Return 404 in both cases (not found AND wrong owner) to avoid leaking information
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")
    return b


# _to_response converts a Beneficiary ORM object to the safe public response schema
def _to_response(b: Beneficiary) -> BeneficiaryResponse:
    return BeneficiaryResponse(
        id=b.id,
        name=b.name,
        email=b.email,
        # has_key is a computed boolean — True if the public_key column is populated
        has_key=b.public_key is not None,
    )


# POST /api/beneficiaries — add a new beneficiary
@router.post("", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
def add_beneficiary(
    body: BeneficiaryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Prevent duplicate emails within the same user's beneficiary list
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
    # Create the new Beneficiary row — public_key is NULL until the owner generates a key
    b = Beneficiary(user_id=current_user.id, name=body.name, email=str(body.email))
    db.add(b)
    db.commit()
    db.refresh(b)
    # Log the addition of a new beneficiary
    log_audit(db, current_user.id, "beneficiary.add", details=str(body.email), ip_address=request.client.host)
    return _to_response(b)


# GET /api/beneficiaries — list all beneficiaries belonging to the current user
@router.get("", response_model=list[BeneficiaryResponse])
def list_beneficiaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch all beneficiaries for this user (no pagination — typically a small list)
    items = db.query(Beneficiary).filter(Beneficiary.user_id == current_user.id).all()
    # Convert each ORM object to the safe response schema
    return [_to_response(b) for b in items]


# GET /api/beneficiaries/{beneficiary_id} — get a single beneficiary by ID
@router.get("/{beneficiary_id}", response_model=BeneficiaryResponse)
def get_beneficiary(
    beneficiary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership and return the beneficiary
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    return _to_response(b)


# PATCH /api/beneficiaries/{beneficiary_id} — update a beneficiary's name and/or email
@router.patch("/{beneficiary_id}", response_model=BeneficiaryResponse)
def update_beneficiary(
    beneficiary_id: int,
    body: BeneficiaryUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership before modifying
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    # Only update fields that were provided (PATCH semantics)
    if body.name is not None:
        b.name = body.name
    if body.email is not None:
        b.email = str(body.email)  # str() coerces Pydantic EmailStr to a plain string
    db.commit()
    db.refresh(b)
    # Log the update event
    log_audit(db, current_user.id, "beneficiary.update", details=f"id={beneficiary_id}", ip_address=request.client.host)
    return _to_response(b)


# DELETE /api/beneficiaries/{beneficiary_id} — remove a beneficiary and their secret assignments
@router.delete("/{beneficiary_id}", response_model=MessageResponse)
def delete_beneficiary(
    beneficiary_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership before allowing deletion
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    # Manually delete all SecretAssignment rows for this beneficiary
    # (the Beneficiary model has no cascade delete configured on its backref)
    db.query(SecretAssignment).filter(SecretAssignment.beneficiary_id == beneficiary_id).delete()
    # Delete the beneficiary record itself
    db.delete(b)
    db.commit()
    # Log the deletion for auditing
    log_audit(db, current_user.id, "beneficiary.delete", details=f"id={beneficiary_id}", ip_address=request.client.host)
    return MessageResponse(message="Beneficiary deleted")


# POST /api/beneficiaries/{beneficiary_id}/generate-key — generate an RSA key pair for a beneficiary
@router.post("/{beneficiary_id}/generate-key", response_model=BeneficiaryWithKeyResponse)
def generate_key(
    beneficiary_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify ownership before generating a key
    b = _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    # Key generation is a one-time operation — once set, the private key cannot be recovered from the server
    if b.public_key is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Key already generated. Delete and recreate the beneficiary to reset.",
        )
    # Generate a fresh RSA-2048 key pair
    public_pem, private_pem = generate_rsa_keypair()
    # Store only the public key server-side
    b.public_key = public_pem
    db.commit()
    db.refresh(b)
    # Log the key generation event
    log_audit(db, current_user.id, "beneficiary.key_generated", details=b.email, ip_address=request.client.host)
    # Return the private key in the response — this is the ONLY time it is ever transmitted
    # The owner must give it to the beneficiary and then it is gone from the server forever
    return BeneficiaryWithKeyResponse(
        id=b.id,
        name=b.name,
        email=b.email,
        has_key=True,
        private_key_pem=private_pem,  # Never stored — shown once, then discarded
    )


# GET /api/beneficiaries/{beneficiary_id}/secrets — list secrets assigned to a beneficiary
@router.get("/{beneficiary_id}/secrets", response_model=list[SecretAssignmentInfo])
def list_assigned_secrets(
    beneficiary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify the beneficiary belongs to the current user before listing their assignments
    _get_beneficiary_or_404(db, beneficiary_id, current_user.id)
    # Fetch all assignment rows for this beneficiary
    assignments = (
        db.query(SecretAssignment)
        .filter(SecretAssignment.beneficiary_id == beneficiary_id)
        .all()
    )
    # Return the assignments — Pydantic serializes them using SecretAssignmentInfo schema
    return assignments
