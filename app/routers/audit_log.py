from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.user import User


router = APIRouter(
    prefix="/api/audit-logs",
    tags=["Audit Logs"],
)


@router.get("/")
def get_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    action: str | None = None,
    entity: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view audit logs",
        )

    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)

    if entity:
        query = query.where(AuditLog.entity == entity)

    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)

    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)

    query = query.order_by(AuditLog.timestamp.desc())

    total = len(db.scalars(query).all())

    logs = db.scalars(
        query.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "timestamp": log.timestamp,
                "ip_address": log.ip_address,
                "metadata": log.metadata_,
            }
            for log in logs
        ],
    }