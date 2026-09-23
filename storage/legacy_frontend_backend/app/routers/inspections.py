from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Inspection, Officer

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.post("/")
def create_inspection(
    image_url: str,
    image_public_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: Officer = Depends(get_current_user),
):
    scan_id = f"MS-{uuid.uuid4().hex[:8].upper()}"

    inspection = Inspection(
        scan_id=scan_id,
        inspector_id=current_user.id,
        image_url=image_url,
        image_public_id=image_public_id,
        status="uploaded",
    )

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return {
        "message": "Inspection created successfully",
        "inspection": {
            "id": inspection.id,
            "scan_id": inspection.scan_id,
            "inspector_id": inspection.inspector_id,
            "image_url": inspection.image_url,
            "image_public_id": inspection.image_public_id,
            "status": inspection.status,
            "created_at": inspection.created_at,
        },
    }


@router.get("/")
def get_my_inspections(
    db: Session = Depends(get_db),
    current_user: Officer = Depends(get_current_user),
):
    inspections = (
        db.query(Inspection)
        .filter(Inspection.inspector_id == current_user.id)
        .order_by(Inspection.created_at.desc())
        .all()
    )

    return inspections
@router.get("/all")
def get_all_inspections(
    db: Session = Depends(get_db),
    current_user: Officer = Depends(get_current_user),
):
    if current_user.role not in ["Supervisor", "Administrator"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access all inspections",
        )

    inspections = (
        db.query(Inspection)
        .order_by(Inspection.created_at.desc())
        .all()
    )

    return inspections

@router.get("/{inspection_id}")
def get_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: Officer = Depends(get_current_user),
):
    inspection = (
        db.query(Inspection)
        .filter(
            Inspection.id == inspection_id,
            Inspection.inspector_id == current_user.id,
        )
        .first()
    )

    if not inspection:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found",
        )

    return inspection


