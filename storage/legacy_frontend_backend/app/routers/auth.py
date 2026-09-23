from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
)
from app.db.database import get_db
from app.db.models import Officer

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    officer = db.query(Officer).filter(Officer.email == email).first()

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(password, officer.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not officer.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    # Make sure selected role matches the role stored in DB
    if officer.role != role:
        raise HTTPException(
            status_code=401,
            detail="Selected role does not match your account"
        )

    token = create_access_token({
        "sub": str(officer.id),
        "role": officer.role,
        "email": officer.email,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": officer.id,
            "name": officer.name,
            "email": officer.email,
            "role": officer.role,
        }
    }


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }