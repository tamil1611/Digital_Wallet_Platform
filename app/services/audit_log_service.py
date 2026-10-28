from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogService:

    @staticmethod
    def create_log(
        db: Session,
        action: str,
        entity: str,
        entity_id: int | str | None = None,
        user_id: int | None = None,
        request: Request | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Audit logs should be append-only:
        create new entries, but do not edit or delete existing entries.
        """

        ip_address = None

        if request is not None and request.client is not None:
            ip_address = request.client.host

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id) if entity_id is not None else None,
            ip_address=ip_address,
            metadata_=metadata,
        )

        db.add(audit_log)
        db.flush()

        return audit_log