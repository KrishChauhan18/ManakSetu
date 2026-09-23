from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models.domain import AuditLog

def log_audit(
    db: Session,
    user_id: int,
    action: str,
    target_type: str,
    target_id: str,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    reason: Optional[str] = None
) -> AuditLog:
    """
    Helper function to insert an audit log record within the current DB transaction.
    """
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        old_value=old_value,
        new_value=new_value,
        reason=reason
    )
    db.add(audit_entry)
    db.flush()  # Ensure ID is generated within existing transaction
    return audit_entry
