from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.beneficiary import Beneficiary
from app.models.secret import Secret
from app.models.secret_assignment import SecretAssignment
from app.schemas.release import ReleasedSecretItem, ReleaseResponse
from app.services.auth_service import log_audit

router = APIRouter(prefix="/api/release", tags=["Release"])


@router.get("/{token}", response_model=ReleaseResponse)
def get_release(token: str, request: Request, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    b = (
        db.query(Beneficiary)
        .filter(
            Beneficiary.release_token == token,
            Beneficiary.release_token_expires_at > now,
        )
        .first()
    )
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired release link.")

    log_audit(db, b.user_id, "release.accessed", details=b.email, ip_address=request.client.host)

    items = []
    for assignment in b.assignments:
        secret: Secret = assignment.secret
        items.append(
            ReleasedSecretItem(
                title=secret.title,
                secret_type=secret.secret_type,
                encrypted_content=secret.encrypted_content,
                encryption_iv=secret.encryption_iv,
                encryption_tag=secret.encryption_tag,
                encrypted_key=assignment.encrypted_key,
            )
        )

    user = b.user
    return ReleaseResponse(
        deceased_name=user.name,
        beneficiary_name=b.name,
        released_at=user.released_at,
        secrets=items,
    )
