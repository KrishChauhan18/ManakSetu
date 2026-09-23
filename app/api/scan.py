import os
import cv2
import asyncio
import numpy as np
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
import math

from app.db.session import get_db, SessionLocal
from app.models.domain import Scan, Violation, Rule, User
from app.schemas.scan import ScanResponse, ScanUploadResponse, OverrideFieldRequest
from app.core.storage_backend import storage_backend
from app.core.envelope import success_response, error_response
from app.core.ws_manager import ws_manager
from app.pipeline.preprocess import preprocess_image
from app.pipeline.quality_check import quality_checker
from app.pipeline.ocr_engine import ocr_engine
from app.pipeline.rule_engine import evaluate_rules, rule_engine
from app.core.storage_backend import save_upload, get_file_path, storage_backend
from ml.visualize_explainability import generate_annotated_label_image
from app.api.auth import get_current_user, get_optional_current_user, require_role
from app.core.audit import log_audit

router = APIRouter(prefix="/scan", tags=["Scan"])

def process_scan(scan_id: int, image_path: str, category: str):
    """
    Background & synchronous task matching §2.3:
    1. Read image and run ocr_engine.extract_and_parse()
    2. Save OCR output to Scan.label_record in DB
    3. Evaluate rules and save Violations to DB
    4. Update compliance_pct and status
    """
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        asyncio.run(ws_manager.broadcast_status(str(scan_id), "preprocessing", 20, "Preprocessing & reading image..."))
        resolved_path = get_file_path(image_path)
        image_np = cv2.imread(resolved_path)
        if image_np is None:
            scan.status = "failed"
            db.commit()
            asyncio.run(ws_manager.broadcast_status(str(scan_id), "failed", 100, "Invalid image format."))
            return

        # 1. OCR Extraction
        asyncio.run(ws_manager.broadcast_status(str(scan_id), "ocr", 45, f"Running OCR extraction for {category}..."))
        label_record = ocr_engine.extract_and_parse(image_np, category=category)

        # SAVE OCR OUTPUT TO THE SCAN ROW
        scan.label_record = label_record
        db.commit()

        # 2. RUN RULE ENGINE AND SAVE VIOLATIONS
        asyncio.run(ws_manager.broadcast_status(str(scan_id), "rule_check", 80, "Evaluating legal statutory rules..."))
        violations, compliance_pct = evaluate_rules(label_record, category=category, db=db)

        # Clear existing violations if re-running
        db.query(Violation).filter(Violation.scan_id == scan_id).delete()
        for v in violations:
            db.add(Violation(scan_id=scan_id, **v))

        scan.compliance_pct = compliance_pct
        scan.status = "needs_review" if any(v.get("status") in ["needs_review", "fail"] for v in violations) else "done"
        db.commit()

        # Generate Explainability Annotated Image
        try:
            annotated_path = os.path.join(os.path.dirname(resolved_path), f"annotated_{os.path.basename(resolved_path)}")
            generate_annotated_label_image(resolved_path, label_record, violations, output_path=annotated_path)
        except Exception:
            pass

        asyncio.run(ws_manager.broadcast_status(str(scan_id), "done", 100, f"Scan audit complete. Compliance: {compliance_pct:.1f}%"))
    except Exception as e:
        db.rollback()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = "failed"
            db.commit()
        asyncio.run(ws_manager.broadcast_status(str(scan_id), "failed", 100, f"Processing failed: {str(e)}"))
        raise
    finally:
        db.close()

run_scan_pipeline_task = process_scan

def _format_scan_dict(s: Scan) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "image_path": s.image_path,
        "image_url": f"/api/v1/scan/{s.id}/image",
        "annotated_image_url": f"/api/v1/scan/{s.id}/image?annotated=true",
        "pdf_report_url": f"/api/v1/reports/{s.id}/pdf",
        "category": s.category,
        "status": s.status,
        "compliance_pct": s.compliance_pct,
        "label_record": s.label_record,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "gps_lat": s.gps_lat,
        "gps_lng": s.gps_lng,
        "violations": [
            {
                "id": v.id,
                "rule_id": v.rule_id,
                "legal_rule_ref": v.legal_rule_ref,
                "source_law": v.source_law,
                "field": v.field,
                "severity": v.severity,
                "status": v.status,
                "detected_value": v.detected_value,
                "expected": v.expected,
                "confidence": v.confidence,
                "bbox": v.bbox,
                "message": v.message,
                "recommendation": v.recommendation
            } for v in s.violations
        ]
    }

@router.websocket("/{scan_id}/status-stream")
async def websocket_scan_status(websocket: WebSocket, scan_id: str):
    await ws_manager.connect(scan_id, websocket)
    try:
        while True:
            # Keep alive and listen for client ping
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(scan_id, websocket)
    except Exception:
        ws_manager.disconnect(scan_id, websocket)

@router.post("/upload")
def upload_scan(
    file: UploadFile = File(...),
    category: str = Form("all"),
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    contents = file.file.read() if hasattr(file.file, "read") else file.read()
    image_path = storage_backend.save_image(contents, file.filename or "label.jpg")

    user_id = current_user.id if current_user else None

    scan = Scan(
        user_id=user_id,
        image_path=image_path,
        category=category,
        status="processing",
        compliance_pct=0.0,
        gps_lat=gps_lat,
        gps_lng=gps_lng
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Execute pipeline synchronously so client immediately receives results
    run_scan_pipeline_task(scan.id, image_path, category)
    db.refresh(scan)

    return success_response(_format_scan_dict(scan))

@router.get("/{scan_id}")
def get_scan_result(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan #{scan_id} not found")

    if current_user and current_user.role == "inspector" and scan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inspectors can only view their own scan results."
        )

    return success_response(_format_scan_dict(scan))

@router.get("/")
def list_scans(
    category: Optional[str] = None,
    scan_status: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = db.query(Scan)

    if current_user and current_user.role == "inspector":
        query = query.filter(Scan.user_id == current_user.id)

    if category and category != "all":
        query = query.filter(Scan.category == category)
    if scan_status and scan_status != "all":
        query = query.filter(Scan.status == scan_status)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    scans = query.order_by(Scan.id.desc()).offset(offset).limit(page_size).all()

    return success_response({
        "items": [_format_scan_dict(s) for s in scans],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    })

@router.get("/{scan_id}/image")
def get_scan_image(
    scan_id: int,
    annotated: bool = Query(False),
    db: Session = Depends(get_db)
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan or not scan.image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    real_path = get_file_path(scan.image_path)
    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    target_path = real_path
    if annotated:
        ann_path = os.path.join(os.path.dirname(real_path), f"annotated_{os.path.basename(real_path)}")
        if os.path.exists(ann_path):
            target_path = ann_path

    ext = os.path.splitext(target_path)[1].lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return FileResponse(target_path, media_type=media_type)

@router.patch("/{scan_id}/override")
def override_scan_field(
    scan_id: int,
    override_in: OverrideFieldRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    if not override_in.reason or len(override_in.reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="A reason is required to override field values for audit compliance.")

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    label_record = scan.label_record or {}
    field_key = override_in.field
    old_value = label_record.get(field_key)

    # Update field in label_record
    if isinstance(old_value, dict):
        label_record[field_key]["value"] = override_in.new_value
        label_record[field_key]["overridden"] = True
        label_record[field_key]["overridden_by"] = current_user.email
    else:
        label_record[field_key] = {
            "value": override_in.new_value,
            "confidence": 1.0,
            "overridden": True,
            "overridden_by": current_user.email
        }

    # Re-evaluate rules
    db_rules = db.query(Rule).filter(Rule.enabled == True).all()
    rules_list = []
    for r in db_rules:
        rules_list.append({
            "rule_id": r.rule_id_str,
            "legal_rule_ref": r.legal_rule_ref or "Rule 6",
            "source_law": r.source_law or "Legal Metrology 2011",
            "field": r.field,
            "check": r.check_type,
            "pattern": r.pattern,
            "severity": r.severity,
            "category": r.category,
            "version": r.version
        })

    comp_pct, violations = rule_engine.evaluate_rules(label_record, rules_list, category=scan.category)

    # Re-create violations
    db.query(Violation).filter(Violation.scan_id == scan.id).delete()
    for v in violations:
        violation_obj = Violation(
            scan_id=scan.id,
            rule_id=v["rule_id"],
            legal_rule_ref=v.get("legal_rule_ref", "Rule 6"),
            source_law=v.get("source_law", "Legal Metrology 2011"),
            field=v["field"],
            severity=v["severity"],
            status=v.get("status", "fail"),
            detected_value=v.get("detected_value"),
            expected=v.get("expected"),
            confidence=v.get("confidence", 0.0),
            bbox=v.get("bbox"),
            message=v["message"],
            recommendation=v.get("recommendation")
        )
        db.add(violation_obj)

    scan.compliance_pct = comp_pct
    scan.label_record = label_record
    scan.status = "done" if comp_pct == 100.0 else "needs_review"

    # Regenerate annotated image
    ann_path = os.path.join(os.path.dirname(scan.image_path), f"annotated_{os.path.basename(scan.image_path)}")
    generate_annotated_label_image(scan.image_path, label_record, violations, output_path=ann_path)

    # Log to Audit Log
    log_audit(
        db=db,
        user_id=current_user.id,
        action="override",
        target_type="scan",
        target_id=str(scan.id),
        old_value={field_key: old_value},
        new_value={field_key: override_in.new_value},
        reason=override_in.reason
    )

    db.commit()
    db.refresh(scan)
    return success_response(_format_scan_dict(scan))

@router.delete("/{scan_id}")
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")

    old_val = {"id": scan.id, "image_path": scan.image_path, "compliance_pct": scan.compliance_pct}

    db.delete(scan)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="delete",
        target_type="scan",
        target_id=str(scan_id),
        old_value=old_val,
        new_value=None,
        reason="Scan deleted by Admin"
    )

    db.commit()
    return success_response({"message": f"Scan {scan_id} deleted successfully."})
