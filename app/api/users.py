import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.models.domain import User
from app.api.auth import require_role, get_current_user
from app.core.security import get_password_hash
from app.core.audit import log_audit
from app.core.envelope import success_response, error_response

router = APIRouter(prefix="/users", tags=["Users"])

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "inspector"  # inspector | supervisor | admin
    region: Optional[str] = None
    supervisor_id: Optional[int] = None

class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    region: Optional[str] = None
    is_active: Optional[bool] = None
    supervisor_id: Optional[int] = None

def _format_user(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "role": u.role,
        "region": u.region,
        "supervisor_id": u.supervisor_id,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None
    }

@router.get("/")
def list_users(
    role: Optional[str] = None,
    region: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if region:
        query = query.filter(User.region == region)

    if page is not None and page_size is not None:
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        return success_response({
            "items": [_format_user(u) for u in users],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages
            }
        })

    users = query.all()
    return success_response([_format_user(u) for u in users])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
        region=user_in.region,
        supervisor_id=user_in.supervisor_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="user_create",
        target_type="user",
        target_id=str(new_user.id),
        old_value=None,
        new_value={"email": new_user.email, "role": new_user.role, "region": new_user.region},
        reason="User created by Admin"
    )
    db.commit()

    return success_response(_format_user(new_user))

@router.put("/{user_id}")
def update_user(
    user_id: int,
    user_in: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_val = {"role": user.role, "region": user.region, "is_active": user.is_active}

    if user_in.role is not None:
        user.role = user_in.role
    if user_in.region is not None:
        user.region = user_in.region
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.supervisor_id is not None:
        user.supervisor_id = user_in.supervisor_id

    db.commit()
    db.refresh(user)

    new_val = {"role": user.role, "region": user.region, "is_active": user.is_active}

    log_audit(
        db=db,
        user_id=current_user.id,
        action="role_change" if old_val["role"] != new_val["role"] else "user_edit",
        target_type="user",
        target_id=str(user.id),
        old_value=old_val,
        new_value=new_val,
        reason="User updated by Admin"
    )
    db.commit()

    return success_response(_format_user(user))

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_val = {"email": user.email, "role": user.role}
    db.delete(user)
    db.commit()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="user_delete",
        target_type="user",
        target_id=str(user_id),
        old_value=old_val,
        new_value=None,
        reason="User deleted by Admin"
    )
    db.commit()

    return success_response({"message": f"User {user_id} deleted successfully."})
