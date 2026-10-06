from typing import Any

from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    vendor_id: int,
    user: AuthUser | None,
    action: str,
    entity_type: str,
    entity_id: int,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            vendor_id=vendor_id,
            user_id=str(user.id) if user else None,
            user_name=user.name if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
        )
    )
