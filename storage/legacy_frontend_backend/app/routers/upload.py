"""
upload.py — Handles image upload to Cloudinary and full compliance scan pipeline.
Uploads image → Cloudinary, then proxies to ComplyErg engine (port 8001),
saves results to the inspections table, and returns a unified response.
"""

import io
import uuid
import httpx
import cloudinary.uploader

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Inspection, Officer

router = APIRouter(prefix="/scan", tags=["Scan"])


@router.post("/upload")
async def upload_scan_image(file: UploadFile = File(...)):
    """Upload image to Cloudinary. Returns url and public_id."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    contents = await file.read()

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder="manak-setu/scans",
            resource_type="image",
        )

        return {
            "message": "Image uploaded successfully",
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary upload failed: {str(exc)}"
        ) from exc


@router.post("/analyze")
async def analyze_label(
    file: UploadFile = File(...),
    category: str = Form(default="food"),
    db: Session = Depends(get_db),
    current_user: Officer = Depends(get_current_user),
):
    """
    Full pipeline:
    1. Upload image to Cloudinary
    2. Proxy image bytes to ComplyErg engine (/api/v1/scan/upload on port 8001)
    3. Save inspection + compliance results to PostgreSQL
    4. Return unified response for React frontend
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    image_bytes = await file.read()
    filename = file.filename or "label.jpg"

    # ── Step 1: Upload to Cloudinary ────────────────────────────────────────
    cloudinary_url = None
    cloudinary_public_id = None
    try:
        cld_result = cloudinary.uploader.upload(
            image_bytes,
            folder="manak-setu/scans",
            resource_type="image",
        )
        cloudinary_url = cld_result["secure_url"]
        cloudinary_public_id = cld_result["public_id"]
    except Exception:
        # Cloudinary is optional — proceed with engine scan anyway
        cloudinary_url = f"local://{filename}"

    # ── Step 2: Send image to ComplyErg engine ──────────────────────────────
    engine_result = {}
    scan_id_str = f"MS-{uuid.uuid4().hex[:8].upper()}"
    compliance_pct = 0.0
    verdict = "UNKNOWN"
    violations = []
    extracted = {}
    risk_score = 0.5

    try:
        engine_url = f"{settings.COMPLYERG_ENGINE_URL}/api/v1/scan/upload"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                engine_url,
                files={"file": (filename, io.BytesIO(image_bytes), file.content_type or "image/jpeg")},
                data={"category": category},
            )
            if response.status_code == 200:
                engine_data = response.json()
                engine_result = engine_data.get("data", engine_data)
                compliance_pct = engine_result.get("compliance_pct", 0.0)
                verdict = engine_result.get("verdict", "UNKNOWN")
                violations = engine_result.get("violations", [])
                extracted = engine_result.get("label_record", {})
                risk_score = engine_result.get("risk_score", 0.5)
                scan_id_str = f"MS-{engine_result.get('id', uuid.uuid4().hex[:8].upper())}"
    except httpx.ConnectError:
        # ComplyErg engine offline — use a graceful fallback
        verdict = "ENGINE_OFFLINE"
        engine_result = {"message": "ComplyErg compliance engine is offline. Start it on port 8001."}

    # ── Step 3: Save to PostgreSQL ──────────────────────────────────────────
    result_status = (
        "Compliant" if compliance_pct == 100
        else "Review Required" if compliance_pct >= 70
        else "Potential Issue"
    )

    # Build extracted fields in the format the React app expects
    extracted_fields = []
    if isinstance(extracted, dict):
        for fkey, fval in extracted.items():
            if isinstance(fval, dict):
                extracted_fields.append({
                    "label": fkey.replace("_", " ").title(),
                    "value": str(fval.get("value") or "MISSING"),
                    "confidence": int((fval.get("confidence") or 0.0) * 100),
                    "box": fval.get("bbox", {"x": 0, "y": 0, "w": 50, "h": 10}),
                })

    # Build rule checks in the format the React app expects
    rule_checks = []
    for v in violations:
        sev = v.get("severity", "medium").capitalize()
        rule_checks.append({
            "ruleId": v.get("rule_id", ""),
            "name": v.get("field", ""),
            "category": category,
            "status": "Review Required" if sev in ["Medium", "Low"] else "Potential Issue",
            "severity": sev if sev in ["Critical", "High", "Medium", "Low"] else "Medium",
            "confidence": 85,
            "evidence": v.get("message", ""),
            "recommendation": v.get("recommendation", ""),
        })

    inspection = Inspection(
        scan_id=scan_id_str,
        inspector_id=current_user.id,
        product=filename,
        category=category,
        manufacturer=extracted.get("manufacturer_name", {}).get("value", "Unknown") if isinstance(extracted, dict) else "Unknown",
        result=result_status,
        score=int(compliance_pct),
        region=getattr(current_user, "region", "Unknown"),
        location=getattr(current_user, "region", "India"),
        image_url=cloudinary_url,
        image_public_id=cloudinary_public_id,
        extracted=extracted_fields,
        rules=rule_checks,
        status="analyzed",
    )

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    # ── Step 4: Return unified response ─────────────────────────────────────
    return {
        "message": "Analysis complete",
        "inspection": {
            "id": inspection.id,
            "scan_id": inspection.scan_id,
            "score": inspection.score,
            "result": inspection.result,
            "compliance_pct": compliance_pct,
            "verdict": verdict,
            "category": category,
            "image_url": cloudinary_url,
            "extracted": extracted_fields,
            "rules": rule_checks,
            "violations": violations,
            "risk_score": risk_score,
            "created_at": str(inspection.created_at),
        },
        "engine": engine_result,
    }