import os
import io
import csv
from PIL import Image as PILImage
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.db.session import get_db
from app.models.domain import Scan, Violation, Report, User
from app.core.storage_backend import storage_backend, get_file_path
from app.core.envelope import success_response
from app.api.auth import get_optional_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


def generate_pdf_bytes(scan: Scan, violations: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=6)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'), spaceAfter=10)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=6)
    disclaimer_style = ParagraphStyle('DiscStyle', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#DC2626'), fontName='Helvetica-Bold')
    normal_small = ParagraphStyle('SmallNormal', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#334155'))

    elements = []

    # 1. Header & Title
    elements.append(Paragraph("MANAK SETU / ComplyErg — Statutory Label Inspection Evidence Report", title_style))
    created_str = scan.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if scan.created_at else "N/A"
    elements.append(Paragraph(
        f"<b>Inspection ID:</b> #{scan.id} &nbsp;|&nbsp; "
        f"<b>Timestamp:</b> {created_str} &nbsp;|&nbsp; "
        f"<b>Category:</b> {scan.category.upper()} &nbsp;|&nbsp; "
        f"<b>Rule Set Version:</b> LMPC-2026.01",
        subtitle_style
    ))

    # 2. Mandatory Statutory Disclaimer
    disclaimer_text = (
        "⚖️ <b>STATUTORY NOTICE & LEGAL PRINCIPLE:</b> "
        "AI-assisted preliminary screening report. The system highlights potential non-compliances and recommendations "
        "to assist the regulatory officer. It does NOT independently issue a final legal penalty, order, or seizure decision. "
        "Final enforcement decisions rest strictly with the authorized Legal Metrology Inspector."
    )
    disc_box = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[540])
    disc_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#EF4444')),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    elements.append(disc_box)
    elements.append(Spacer(1, 8))

    # 3. Overall Compliance Score Card
    comp_pct = scan.compliance_pct if scan.compliance_pct is not None else 0.0
    comp_color = colors.HexColor('#10B981') if comp_pct >= 85 else (colors.HexColor('#F59E0B') if comp_pct >= 60 else colors.HexColor('#EF4444'))
    status_text = "COMPLIANT SCREENING RESULT" if comp_pct == 100 else ("POSSIBLE NON-COMPLIANCE" if comp_pct < 70 else "NEEDS HUMAN REVIEW")

    score_table_data = [
        [
            Paragraph(f"<b>Compliance Screening Score: {comp_pct:.1f}%</b>", styles['Normal']),
            Paragraph(f"<b>Status: {status_text}</b>", styles['Normal'])
        ]
    ]
    score_table = Table(score_table_data, colWidths=[270, 270])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0,0), (-1,-1), comp_color),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 8))

    # 4. Packaging Evidence Photo
    if scan.image_path:
        try:
            real_img_path = get_file_path(scan.image_path)
            ann_path = os.path.join(os.path.dirname(real_img_path), f"annotated_{os.path.basename(real_img_path)}")
            img_to_use = ann_path if os.path.exists(ann_path) else real_img_path

            if os.path.exists(img_to_use):
                # Ensure valid RGB format for ReportLab
                pil_check = PILImage.open(img_to_use).convert("RGB")
                temp_thumb = io.BytesIO()
                pil_check.save(temp_thumb, format="JPEG")
                temp_thumb.seek(0)
                img = RLImage(temp_thumb, width=260, height=180)
                elements.append(Paragraph("Packaging Visual Evidence & Spatial Annotation", section_style))
                elements.append(img)
                elements.append(Spacer(1, 8))
        except Exception:
            pass

    # 5. Extracted Statutory Declarations Table
    elements.append(Paragraph("Extracted Mandatory Legal Declarations", section_style))
    extracted_data = scan.label_record or {}

    table_rows = [["Declaration Field", "Extracted Value", "Confidence", "Source"]]
    display_fields = [
        ("product_name", "Product / Commodity"),
        ("net_quantity", "Net Quantity"),
        ("mrp", "Maximum Retail Price (MRP)"),
        ("manufacturer", "Manufacturer Name & Address"),
        ("packer", "Packer Details"),
        ("importer", "Importer Details"),
        ("country_of_origin", "Country of Origin"),
        ("mfg_date", "Date of Manufacture / Packing"),
        ("expiry_date", "Best Before / Expiry Date"),
        ("consumer_care", "Consumer Care Details"),
        ("batch_number", "Batch / Lot Number")
    ]

    for fkey, flabel in display_fields:
        fval = extracted_data.get(fkey)
        if isinstance(fval, dict):
            val_str = fval.get("value") or "MISSING / NOT DETECTED"
            if fval.get("unit") and str(fval.get("unit")) not in str(val_str):
                val_str = f"{val_str} {fval.get('unit')}"
            conf_val = fval.get("confidence", 0.0)
            conf_str = f"{float(conf_val or 0.0)*100:.0f}%" if fval.get("value") else "0%"
            src_str = str(fval.get("source_engine") or fval.get("source") or "OCR").upper()
            table_rows.append([flabel, str(val_str)[:45], conf_str, src_str])
        else:
            table_rows.append([flabel, "MISSING / NOT DETECTED", "0%", "NONE"])

    dec_table = Table(table_rows, colWidths=[160, 220, 80, 80])
    dec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    elements.append(dec_table)
    elements.append(Spacer(1, 8))

    # 6. Violations & Regulatory Recommendations Table
    elements.append(Paragraph("Itemized Rule Evaluations & Regulatory Observations", section_style))
    if violations:
        v_rows = [["Rule ID & Law Ref", "Field", "Severity", "Observation & Remedy"]]
        for v in violations:
            v_id = getattr(v, "rule_id", None) or (v.get("rule_id") if isinstance(v, dict) else "LM2011-R6")
            v_field = getattr(v, "field", None) or (v.get("field") if isinstance(v, dict) else "general")
            v_sev = str(getattr(v, "severity", None) or (v.get("severity") if isinstance(v, dict) else "HIGH")).upper()
            v_msg = getattr(v, "message", None) or (v.get("message") if isinstance(v, dict) else "Non-compliance observed.")
            v_rec = getattr(v, "recommendation", None) or (v.get("recommendation") if isinstance(v, dict) else "Ensure compliance.")
            v_law = getattr(v, "source_law", None) or (v.get("source_law") if isinstance(v, dict) else "LM Rules 2011")

            law_ref = f"<b>{v_id}</b><br/><font color='#64748B'>{v_law}</font>"
            v_text = f"<b>{v_msg}</b><br/><font color='#047857'><b>Remedy:</b> {v_rec}</font>"
            v_rows.append([Paragraph(law_ref, normal_small), v_field, v_sev, Paragraph(v_text, normal_small)])

        v_table = Table(v_rows, colWidths=[130, 80, 70, 260])
        v_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#991B1B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECACA')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FEF2F2')])
        ]))
        elements.append(v_table)
    else:
        elements.append(Paragraph("<b>No statutory violations detected. Package label conforms with applicable Rule 6 requirements.</b>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/{scan_id}/pdf")
def export_pdf_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    violations = db.query(Violation).filter(Violation.scan_id == scan_id).all()
    try:
        pdf_bytes = generate_pdf_bytes(scan, violations)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"REPORT_GENERATION_FAILED: {str(exc)}")

    report_key = storage_backend.save_report_pdf(pdf_bytes, scan_id)

    report = db.query(Report).filter(Report.scan_id == scan_id).first()
    if not report:
        report = Report(scan_id=scan_id, pdf_path=report_key)
        db.add(report)
        db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=inspection-{scan_id}.pdf"
        }
    )


@router.get("/{scan_id}/json")
def export_json_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    violations = db.query(Violation).filter(Violation.scan_id == scan_id).all()
    return success_response({
        "scan_id": scan.id,
        "category": scan.category,
        "status": scan.status,
        "compliance_pct": scan.compliance_pct,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "label_record": scan.label_record,
        "violations": [
            {
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
            } for v in violations
        ]
    })


@router.get("/{scan_id}/csv")
def export_csv_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    violations = db.query(Violation).filter(Violation.scan_id == scan_id).all()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Scan ID", "Category", "Compliance Pct", "Rule ID", "Source Law", "Rule Ref", "Field", "Severity", "Message", "Recommendation"])
    if violations:
        for v in violations:
            writer.writerow([scan.id, scan.category, scan.compliance_pct, v.rule_id, v.source_law, v.legal_rule_ref, v.field, v.severity, v.message, v.recommendation])
    else:
        writer.writerow([scan.id, scan.category, scan.compliance_pct, "NONE", "NONE", "NONE", "NONE", "PASSED", "No violations", "N/A"])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inspection-{scan_id}.csv"}
    )
