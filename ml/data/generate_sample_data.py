import os
import json
import random
import pandas as pd

PREPARED_DIR = os.path.join(os.getcwd(), "ml", "data", "prepared")
ANNOTATIONS_DIR = os.path.join(os.getcwd(), "ml", "data", "annotations")

MANUFACTURERS = [
    "Mfd. by: Amul Dairy Foods Pvt. Ltd., Anand, Gujarat",
    "Manufactured & Packed by Nestlé India Ltd., MGR Road, New Delhi",
    "Packed by: Britannia Industries Ltd., Off Old Airport Road, Bengaluru",
    "Mfd. by Dabur India Limited, Village Billanwali, Baddi, HP",
    "Manufactured by Parle Products Pvt Ltd, Vile Parle East, Mumbai",
    "Mfd. by: Haldiram Snacks Pvt. Ltd., Noida Sector 63, UP",
    "Imported & Marketed by Global Consumer Products Ltd, Cyber City Gurgaon",
    "उत्पादक एवं पैककर्ता: पतंजलि आयुर्वेद लिमिटेड, हरिद्वार, उत्तराखंड",
    "निर्माता: डाबर इंडिया लिमिटेड, बद्दी, हिमाचल प्रदेश"
]

MRP_TEXTS = [
    "M.R.P. Rs. 120.00 (Incl. of all taxes)",
    "MRP ₹250.00 inclusive of all taxes",
    "M.R.P. : Rs 45.00 (INCL. OF ALL TAXES)",
    "MRP ₹ 99.00 (inclusive of all taxes)",
    "MAX. RETAIL PRICE ₹1,250.00 INCL. ALL TAXES",
    "MRP Rs. 15.00 incl. of all taxes",
    "अधिकतम खुदरा मूल्य: ₹120.00 (सभी कर सहित)"
]

QTY_TEXTS = [
    "Net Quantity: 500 g",
    "Net Qty : 1 L",
    "Net Weight: 250g",
    "Net Vol.: 750 ml",
    "Net Content: 100 N (100 units)",
    "NET QUANTITY : 5 kg",
    "Net Wt. 50 ml",
    "शुद्ध मात्रा: 500 ग्राम",
    "शुद्ध मात्रा: 1 लीटर"
]

MFG_DATES = [
    "Mfg Date: 03/2025",
    "Mfd: 01/2025",
    "Date of Mfg: 12/2024",
    "PKD: 02/2025",
    "Packed on: 04/2025",
    "MFG. 10/2024",
    "निर्माण तिथि: 03/2025"
]

EXP_DATES = [
    "Expiry Date: 03/2026",
    "Use Before: 01/2026",
    "Best Before 12 Months from Packaging (12/2025)",
    "EXP. DATE: 02/2026",
    "Expiry: 04/2026",
    "BEST BEFORE: 09/2025",
    "अवसान तिथि: 03/2026"
]

CARE_TEXTS = [
    "Consumer Care Executive: 1800-112-2334 or email care@amul.co.in",
    "For Feedback/Complaint Contact: Customer Care Cell 1800-425-1111 / care@nestle.com",
    "Customer Support: Toll Free 1800-102-3456 or write to support@britannia.in",
    "In case of complaints contact Consumer Care Officer, Tel: 011-23456789",
    "Helpline: 1800-200-9999 / customercare@dabur.com",
    "ग्राहक सेवा केंद्र: 1800-112-2334 / care@patanjali.com"
]

OTHER_TEXTS = [
    "Store in a cool and dry place away from direct sunlight.",
    "Ingredients: Wheat Flour, Sugar, Edible Vegetable Oil, Cocoa Solids, Salt.",
    "Nutritional Information per 100g: Energy 450 kcal, Protein 6.5g, Carbohydrate 68g.",
    "Keep container tightly closed after use.",
    "Recycle symbol - 100% recyclable packaging.",
    "FSSAI Lic. No. 10014011001894",
    "ठंडे एवं सूखे स्थान पर रखें।"
]

def generate_field_blocks_csv(num_samples: int = 700):
    os.makedirs(PREPARED_DIR, exist_ok=True)
    os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

    rows = []
    label_map = [
        (MANUFACTURERS, "manufacturer"),
        (MRP_TEXTS, "mrp"),
        (QTY_TEXTS, "net_quantity"),
        (MFG_DATES, "mfg_date"),
        (EXP_DATES, "expiry_date"),
        (CARE_TEXTS, "consumer_care"),
        (OTHER_TEXTS, "other")
    ]

    for texts, label in label_map:
        for _ in range(num_samples // len(label_map)):
            txt = random.choice(texts)
            rows.append({"text": txt, "label": label})

    df = pd.DataFrame(rows)
    csv_path = os.path.join(PREPARED_DIR, "field_blocks.csv")
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} labeled text blocks at {csv_path}")

    # Generate sample annotations JSON
    sample_annotation = {
        "image_id": "sample_label_01.jpg",
        "category": "food",
        "ground_truth": {
            "manufacturer": "Amul Dairy Foods Pvt. Ltd., Anand, Gujarat",
            "net_quantity": "500 g",
            "mrp": "₹120.00",
            "mfg_date": "03/2025",
            "expiry_date": "03/2026",
            "consumer_care": "1800-112-2334 / care@amul.co.in"
        }
    }
    with open(os.path.join(ANNOTATIONS_DIR, "sample_label_01.json"), "w", encoding="utf-8") as f:
        json.dump(sample_annotation, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    generate_field_blocks_csv()
