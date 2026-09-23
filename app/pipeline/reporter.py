import os
import io
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class MetrologyReportGenerator:
    """
    Generates production-grade ReportLab PDF evidence documents for Legal Metrology inspections.
    """
    def generate_pdf_report(
        self,
        scan_id: str,
        created_at: str,
        image_path: str,
        validation_res: Dict[str, Any],
        extracted_fields: Dict[str, Any],
        output_pdf_path: str
    ) -> str:
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Heading1'],
            fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=8
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#475569'), spaceAfter=14
        )
        section_style = ParagraphStyle(
            'SectionStyle', parent=styles['Heading2'],
            fontSize=13, textColor=colors.HexColor('#1E293B'), spaceBefore=14, spaceAfter=8
        )

        elements = []

        # 1. Header
        elements.append(Paragraph("ComplyErg — Legal Metrology Evidence Inspection Report", title_style))
        elements.append(Paragraph(f"Scan Reference ID: <b>#{scan_id}</b> | Inspection Timestamp: {created_at} UTC", subtitle_style))

        # 2. Compliance Status Banner
        is_compliant = validation_res.get("is_compliant", False)
        comp_score = validation_res.get("compliance_score", 0.0)

        banner_bg = colors.HexColor('#DCFCE7') if is_compliant else colors.HexColor('#FEE2E2')
        banner_fg = colors.HexColor('#166534') if is_compliant else colors.HexColor('#991B1B')
        status_str = "COMPLIANT PASS" if is_compliant else "NON-COMPLIANT STATUTORY VIOLATION"

        banner_table = Table([[
            Paragraph(f"<b>Legal Status: {status_str}</b>", styles['Normal']),
            Paragraph(f"<b>Compliance Score: {comp_score:.1f}%</b>", styles['Normal'])
        ]], colWidths=[270, 270])

        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), banner_bg),
            ('TEXTCOLOR', (0,0), (-1,-1), banner_fg),
            ('PADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 12))

        # 3. Packaging Evidence Photo
        if image_path and os.path.exists(image_path):
            try:
                img = RLImage(image_path, width=220, height=160)
                elements.append(Paragraph("Captured Packaging Evidence Snapshot", section_style))
                elements.append(img)
                elements.append(Spacer(1, 12))
            except Exception:
                pass

        # 4. Extracted Declarations Table
        elements.append(Paragraph("Extracted Mandatory Declarations", section_style))
        rows = [["Declaration Field", "Extracted Value", "Confidence", "Source"]]
        
        field_labels = {
            "manufacturer": "Manufacturer Details",
            "net_quantity": "Net Quantity",
            "mrp": "Maximum Retail Price",
            "mfg_date": "Date of Mfg / Packing",
            "expiry_date": "Expiry / Best Before Date",
            "consumer_care": "Consumer Care Details"
        }

        for fkey, flabel in field_labels.items():
            fval = extracted_fields.get(fkey)
            if isinstance(fval, dict):
                val_str = fval.get("value", "MISSING")
                conf_str = f"{fval.get('confidence', 0.0)*100:.0f}%"
                src_str = str(fval.get("source", "N/A")).upper()
                rows.append([flabel, str(val_str)[:45], conf_str, src_str])
            else:
                rows.append([flabel, "MISSING / NOT DETECTED", "0%", "NONE"])

        dec_table = Table(rows, colWidths=[150, 230, 80, 80])
        dec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
        ]))
        elements.append(dec_table)
        elements.append(Spacer(1, 12))

        # 5. Itemized Rule Violations
        elements.append(Paragraph("Itemized Rule Violations & Recommendations", section_style))
        violations = validation_res.get("violations", [])
        if violations:
            v_rows = [["Rule Reference", "Field", "Severity", "Violation & Recommendation"]]
            for v in violations:
                v_body = f"<b>{v['rule_name']}</b><br/>{v['description']}<br/><font color='#475569'>Rec: {v.get('recommendation')}</font>"
                v_rows.append([v["rule_id"], v["field"], v["severity"], Paragraph(v_body, styles['Normal'])])

            v_table = Table(v_rows, colWidths=[110, 80, 70, 280])
            v_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#991B1B')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECACA')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FEF2F2')])
            ]))
            elements.append(v_table)
        else:
            elements.append(Paragraph("<b>No statutory violations detected. All declarations conform to Rule 6.</b>", styles['Normal']))

        doc.build(elements)
        return output_pdf_path

report_generator = MetrologyReportGenerator()
