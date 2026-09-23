import pytest
from app.pipeline.rule_engine import rule_engine

@pytest.fixture
def seed_rules():
    return [
        {"rule_id": "LM2011-R6-MFR", "field": "manufacturer_name", "check": "presence", "severity": "critical", "category": ["all"], "version": "2011"},
        {"rule_id": "LM2011-R6-QTY", "field": "net_quantity", "check": "presence_and_unit", "severity": "critical", "category": ["all"], "version": "2011"},
        {"rule_id": "LM2011-R6-MRP", "field": "mrp", "check": "regex", "pattern": "^(₹|Rs\\.?|INR)?\\s?\\d+(\\.\\d{1,2})?$", "severity": "critical", "category": ["all"], "version": "2011"},
        {"rule_id": "LM2011-R6-MFG_DATE", "field": "mfg_date", "check": "date_format", "pattern": "^(0[1-9]|1[0-2])/\\d{4}$", "severity": "high", "category": ["all"], "version": "2011"},
        {"rule_id": "LM2011-R6-DATE_LOGIC", "field": ["mfg_date","expiry_date"], "check": "date_order", "severity": "critical", "category": ["all"], "version": "2011"},
        {"rule_id": "LM2011-R6-MRP_INCLUSIVE", "field": "mrp", "check": "keyword_present", "pattern": "inclusive of all taxes", "severity": "low", "category": ["all"], "version": "2011"}
    ]

def test_rule_engine_compliant(seed_rules):
    label_record = {
        "manufacturer_name": {"value": "Amul Foods Ltd", "confidence": 0.95},
        "net_quantity": {"value": "500", "unit": "g", "confidence": 0.90},
        "mrp": {"value": "₹120.00", "confidence": 0.95},
        "mfg_date": {"value": "03/2025", "confidence": 0.85},
        "expiry_date": {"value": "03/2026", "confidence": 0.85},
        "raw_ocr_text": "Amul Foods Ltd Net Qty 500 g MRP ₹120.00 inclusive of all taxes Mfg 03/2025 Exp 03/2026"
    }

    comp_pct, violations = rule_engine.evaluate_rules(label_record, seed_rules)
    assert comp_pct == 100.0
    assert len(violations) == 0

def test_rule_engine_missing_manufacturer(seed_rules):
    label_record = {
        "manufacturer_name": None,
        "net_quantity": {"value": "500", "unit": "g", "confidence": 0.90},
        "mrp": {"value": "₹120.00", "confidence": 0.95},
        "mfg_date": {"value": "03/2025", "confidence": 0.85},
        "expiry_date": {"value": "03/2026", "confidence": 0.85},
        "raw_ocr_text": "Net Qty 500 g MRP ₹120.00 inclusive of all taxes Mfg 03/2025"
    }

    comp_pct, violations = rule_engine.evaluate_rules(label_record, seed_rules)
    assert comp_pct < 100.0
    assert any(v["rule_id"] == "LM2011-R6-MFR" for v in violations)

def test_rule_engine_invalid_date_order(seed_rules):
    label_record = {
        "manufacturer_name": {"value": "Amul Foods Ltd", "confidence": 0.95},
        "net_quantity": {"value": "500", "unit": "g", "confidence": 0.90},
        "mrp": {"value": "₹120.00", "confidence": 0.95},
        "mfg_date": {"value": "08/2026", "confidence": 0.85},
        "expiry_date": {"value": "03/2025", "confidence": 0.85},
        "raw_ocr_text": "Amul Foods Ltd Net Qty 500 g MRP ₹120.00 inclusive of all taxes"
    }

    comp_pct, violations = rule_engine.evaluate_rules(label_record, seed_rules)
    assert comp_pct < 100.0
    assert any(v["rule_id"] == "LM2011-R6-DATE_LOGIC" for v in violations)
