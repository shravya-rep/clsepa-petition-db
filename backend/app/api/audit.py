from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import require_admin
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return (
        db.query(AuditLog)
        .options(joinedload(AuditLog.user))
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
