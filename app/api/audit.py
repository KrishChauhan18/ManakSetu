import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.domain import AuditLog, User
from app.api.auth import require_role
from app.core.envelope import success_response, error_response

router = APIRouter(prefix="/audit", tags=["Audit Log"])

def _format_audit(a: AuditLog) -> dict:
    return {
        "id": a.id,
        "user_id": a.user_id,
        "action": a.action,
        "target_type": a.target_type,
        "target_id": a.target_id,
        "old_value": a.old_value,
        "new_value": a.new_value,
        "reason": a.reason,
        "timestamp": a.timestamp.isoformat() if a.timestamp else None
    }

@router.get("/")
def get_audit_logs(
    target_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    """
    Read-only Audit Log Endpoint for Supervisors and Admins with pagination.
    """
    query = db.query(AuditLog)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    logs = query.order_by(AuditLog.id.desc()).offset(offset).limit(page_size).all()

    return success_response({
        "items": [_format_audit(l) for l in logs],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    })
