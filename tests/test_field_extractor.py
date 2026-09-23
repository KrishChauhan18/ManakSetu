from app.pipeline.field_extractor import field_extractor

def test_field_extractor_regex_pass():
    ocr_blocks = [
        {"text": "Mfd. by: Amul Dairy Foods Pvt. Ltd., Anand", "confidence": 0.92, "bbox": [10, 10, 200, 30]},
        {"text": "Net Quantity: 500 g", "confidence": 0.88, "bbox": [10, 40, 150, 60]},
        {"text": "M.R.P. ₹120.00 (INCL. OF ALL TAXES)", "confidence": 0.95, "bbox": [10, 70, 220, 90]},
        {"text": "Mfg Date: 03/2025", "confidence": 0.85, "bbox": [10, 100, 140, 120]},
        {"text": "Batch No: B2503A", "confidence": 0.80, "bbox": [10, 130, 130, 150]}
    ]

    record = field_extractor.extract_fields(ocr_blocks)

    assert record["manufacturer_name"] is not None
    assert "Amul Dairy" in record["manufacturer_name"]["value"]
    assert record["net_quantity"]["value"] == "500"
    assert record["net_quantity"]["unit"] == "g"
    assert record["mrp"]["value"] == "₹120.00"
    assert record["mfg_date"]["value"] == "03/2025"
    assert record["batch_number"]["value"] == "B2503A"
