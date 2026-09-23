import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SAMPLE_DIR = os.path.join(os.getcwd(), "ml", "data", "samples")
os.makedirs(SAMPLE_DIR, exist_ok=True)

def create_label(filename: str, lines: list, is_medicine: bool = False, has_rx: bool = False):
    width, height = 800, 600
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([10, 10, width - 10, height - 10], outline=(30, 41, 59), width=3)

    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_body = ImageFont.truetype("arial.ttf", 18)
        font_rx = ImageFont.truetype("arial.ttf", 36)
        font_warning = ImageFont.truetype("arial.ttf", 15)
    except Exception:
        font_title = font_body = font_rx = font_warning = ImageFont.load_default()

    y = 30
    if has_rx:
        draw.text((40, y), "Rx", fill=(220, 38, 38), font=font_rx)
        y += 45

    for line in lines:
        if line.startswith("TITLE:"):
            draw.text((40, y), line.replace("TITLE:", "").strip(), fill=(15, 23, 42), font=font_title)
            y += 40
            draw.line([40, y, width - 40, y], fill=(203, 213, 225), width=2)
            y += 20
        elif line.startswith("WARN:"):
            warn_text = line.replace("WARN:", "").strip()
            draw.rectangle([35, y, width - 35, y + 55], outline=(220, 38, 38), fill=(254, 242, 242), width=2)
            draw.text((45, y + 15), warn_text, fill=(185, 28, 28), font=font_warning)
            y += 70
        else:
            draw.text((40, y), line, fill=(30, 41, 59), font=font_body)
            y += 32

    out_path = os.path.join(SAMPLE_DIR, filename)
    img.save(out_path, quality=95)
    print(f"Generated sample label: {out_path}")

def generate_all():
    # 1. Grocery Known-Good
    create_label("grocery_compliant.jpg", [
        "TITLE: Organic Whole Wheat Atta",
        "Net Quantity: 1 kg",
        "MRP: Rs. 65.00 (Inclusive of all taxes)",
        "Mfd Date: 02/2026",
        "Expiry Date: 08/2026",
        "Batch No: BATCH-AT778",
        "Mfd by: Apex Organic Foods Ltd, Delhi NCR, India",
        "FSSAI Lic. No: 10018011002345",
        "Ingredients: 100% Whole Wheat Grain",
        "Consumer Care: care@apexorganic.com | 1800-11-2233",
        "Country of Origin: India"
    ])

    # 2. Grocery Known-Bad (Violations: missing tax statement, invalid unit, missing FSSAI)
    create_label("grocery_violation.jpg", [
        "TITLE: Premium Roasted Cashews",
        "Net Weight: 250 bags",
        "Price: Rs 300",
        "Mfd Date: 05/2026",
        "Expiry Date: 01/2026",
        "Batch: CASHEW-99",
        "Manufactured by: Sunshine Traders Pvt Ltd"
    ])

    # 3. Medicine Known-Good
    create_label("medicine_compliant.jpg", [
        "TITLE: Amoxicillin Tablets IP 500mg",
        "Composition: Each film coated tablet contains Amoxicillin Trihydrate IP eq to Amoxicillin 500 mg",
        "Mfg Lic No: DL-8890/2020",
        "Batch No: LOT-AMX901",
        "Mfd: 01/2026",
        "Exp: 12/2027",
        "MRP: Rs. 120.50 (Inclusive of all taxes)",
        "Mfd by: Zydus Healthcare Ltd, Sikkim, India",
        "Storage: Store in a cool and dry place below 25°C. Protect from light.",
        "WARN: SCHEDULE H PRESCRIPTION DRUG - CAUTION: Not to be sold by retail without prescription of Registered Medical Practitioner."
    ], is_medicine=True, has_rx=True)

    # 4. Medicine Known-Bad (Violations: missing Rx, missing Schedule warning, missing mfg license)
    create_label("medicine_violation.jpg", [
        "TITLE: PainRelief Forte Tablets",
        "Contains: Ibuprofen & Paracetamol",
        "Batch: MED-0012",
        "Mfd: 03/2026",
        "Exp: 03/2025",
        "Price: Rs. 45.00",
        "Manufactured by: QuickMed Remedies"
    ], is_medicine=True, has_rx=False)

if __name__ == "__main__":
    generate_all()
