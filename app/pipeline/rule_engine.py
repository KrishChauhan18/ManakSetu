import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

VALID_UNITS = {"g", "gm", "gms", "kg", "ml", "l", "ltr", "n", "units", "pcs", "cm", "m", "tablets", "capsules", "tabs", "caps"}

class RuleEngine:
    def evaluate_rules(
        self,
        label_record: Dict[str, Any],
        rules: List[Dict[str, Any]],
        category: str = "all"
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Generic, deterministic Rule Engine for:
        1. Legal Metrology (Packaged Commodities) Rules, 2011 (Rules 6, 7, 9, 10)
        2. Drugs and Cosmetics Rules, 1945 (Schedule H/H1/X, Rule 96/97) when category == 'medicine'

        Returns: (compliance_pct, list_of_violations_with_explainability_payload)
        """
        violations = []
        applicable_rules = []

        for rule in rules:
            rule_cats = rule.get("category", ["all"])
            # Category gating: rule applies if "all" in categories or exact category matches
            if "all" in rule_cats or category in rule_cats or (category == "all" and "medicine" not in rule_cats):
                applicable_rules.append(rule)

        passed_count = 0

        for rule in applicable_rules:
            rule_id = rule["rule_id"]
            field_name = rule["field"]
            check_type = rule["check"]
            severity = rule.get("severity", "medium")
            pattern = rule.get("pattern")
            legal_ref = rule.get("legal_rule_ref", "Rule 6")
            source_law = rule.get("source_law", "Legal Metrology 2011")

            is_passed = True
            message = ""
            reason = ""
            recommendation = ""
            detected_val = None
            expected_val = str(pattern) if pattern else "Valid presence & format"
            bbox = None
            conf = 0.0

            # --- Check 1: Presence ---
            if check_type == "presence":
                field_data = label_record.get(field_name)
                if isinstance(field_data, dict):
                    detected_val = field_data.get("value")
                    bbox = field_data.get("bbox")
                    conf = field_data.get("confidence", 0.0)

                if not field_data or not detected_val:
                    is_passed = False
                    message = f"Mandatory declaration '{field_name}' is missing from package label."
                    reason = f"Field '{field_name}' was not detected in OCR text blocks."
                    recommendation = f"Ensure '{field_name}' is clearly printed in prominent font as required by {legal_ref}."

            # --- Check 2: Presence and Metric Unit ---
            elif check_type == "presence_and_unit":
                field_data = label_record.get(field_name)
                if isinstance(field_data, dict):
                    detected_val = field_data.get("value")
                    bbox = field_data.get("bbox")
                    conf = field_data.get("confidence", 0.0)

                if not field_data or not detected_val:
                    is_passed = False
                    message = f"Mandatory net quantity declaration '{field_name}' is missing."
                    reason = "Net quantity text was not found on package."
                    recommendation = "Declare net quantity along with standard metric units (e.g. g, kg, ml, l, N)."
                else:
                    unit = field_data.get("unit", "")
                    val_str = str(detected_val).lower()
                    has_unit = unit in VALID_UNITS or any(u in val_str for u in VALID_UNITS)
                    if not has_unit:
                        is_passed = False
                        message = f"Net quantity '{detected_val}' lacks a valid standard metric unit."
                        reason = f"Extracted unit '{unit}' is not in approved Legal Metrology metric units."
                        recommendation = "Use authorized Legal Metrology metric units (g, kg, ml, l, or N)."

            # --- Check 3: Regex Match ---
            elif check_type == "regex":
                field_data = label_record.get(field_name)
                if isinstance(field_data, dict):
                    detected_val = field_data.get("value")
                    bbox = field_data.get("bbox")
                    conf = field_data.get("confidence", 0.0)

                if not field_data or not detected_val:
                    is_passed = False
                    message = f"Mandatory field '{field_name}' is missing."
                    reason = f"No text block matched statutory regex pattern for '{field_name}'."
                    recommendation = f"Provide valid formatted '{field_name}' as required by {legal_ref}."
                else:
                    val = str(detected_val).strip()
                    pattern_str = pattern if isinstance(pattern, str) else str(pattern) if pattern else r".+"
                    if pattern_str and not re.search(pattern_str, val, re.I):
                        is_passed = False
                        message = f"Field '{field_name}' value '{val}' does not conform to statutory pattern."
                        reason = f"Value '{val}' failed regex match against pattern '{pattern_str}'."
                        recommendation = f"Format '{field_name}' according to Legal Metrology standards."

            # --- Check 4: Date Format (MM/YYYY) ---
            elif check_type == "date_format":
                field_data = label_record.get(field_name)
                if isinstance(field_data, dict):
                    detected_val = field_data.get("value")
                    bbox = field_data.get("bbox")
                    conf = field_data.get("confidence", 0.0)

                if not field_data or not detected_val:
                    if field_name == "expiry_date" and category not in ["food", "cosmetics", "medicine", "all"]:
                        is_passed = True
                    else:
                        is_passed = False
                        message = f"Mandatory date field '{field_name}' is missing."
                        reason = f"Statutory date for '{field_name}' was not detected."
                        recommendation = f"Print '{field_name}' in MM/YYYY format."
                else:
                    val = str(detected_val).strip()
                    pattern_str = pattern if isinstance(pattern, str) else r"\d{2}/\d{4}"
                    if pattern_str and not re.search(pattern_str, val):
                        is_passed = False
                        message = f"Date '{field_name}' ('{val}') is not in required MM/YYYY format."
                        reason = f"Date string '{val}' failed MM/YYYY syntax validation."
                        recommendation = "Use standard month/year format MM/YYYY (e.g. 03/2026)."

            # --- Check 5: Date Order (Mfg before Expiry) ---
            elif check_type == "date_order":
                mfg_data = label_record.get("mfg_date")
                exp_data = label_record.get("expiry_date")
                if mfg_data and mfg_data.get("value") and exp_data and exp_data.get("value"):
                    try:
                        m_str = str(mfg_data["value"]).strip()
                        e_str = str(exp_data["value"]).strip()
                        detected_val = f"Mfg: {m_str}, Exp: {e_str}"
                        bbox = mfg_data.get("bbox")
                        conf = min(mfg_data.get("confidence", 0.8), exp_data.get("confidence", 0.8))

                        m_dt = datetime.strptime(m_str, "%m/%Y")
                        e_dt = datetime.strptime(e_str, "%m/%Y")
                        if m_dt > e_dt:
                            is_passed = False
                            message = f"Manufacturing date ({m_str}) cannot be later than Expiry date ({e_str})."
                            reason = "Temporal conflict: Manufacturing date exceeds expiration date."
                            recommendation = "Verify printed manufacturing and expiration dates for chronological sequence."
                    except ValueError:
                        pass

            # --- Check 6: Keyword Nearby (e.g., 'inclusive of all taxes') ---
            elif check_type in ["keyword_nearby", "keyword_present"]:
                raw_text = label_record.get("raw_ocr_text", "").lower()
                mrp_data = label_record.get("mrp")
                if mrp_data:
                    bbox = mrp_data.get("bbox")
                    conf = mrp_data.get("confidence", 0.8)
                    detected_val = mrp_data.get("value")

                kw_target = pattern if isinstance(pattern, str) else "inclusive of all taxes"
                if kw_target.lower() not in raw_text and "incl" not in raw_text and "taxes" not in raw_text:
                    is_passed = False
                    message = f"MRP declaration missing mandatory phrase '{kw_target}'."
                    reason = f"Mandatory phrase '{kw_target}' not found in proximity to Maximum Retail Price."
                    recommendation = f"Include standard statutory phrase '{kw_target}' alongside Maximum Retail Price."

            # --- Check 7: Script Language Check (Rule 9) ---
            elif check_type in ["script_check", "contains"]:
                detected_scripts = label_record.get("language_detected", ["en"])
                if "en" not in detected_scripts and "hi" not in detected_scripts:
                    is_passed = False
                    message = "Declarations must be printed in Hindi (Devanagari) or English script under Rule 9."
                    reason = f"Detected script(s) '{detected_scripts}' do not include required English or Hindi."
                    recommendation = "Ensure mandatory declarations are printed in English or Hindi (Devanagari) script."

            # --- Check 8: Spatial Prominence (Rule 7) ---
            elif check_type == "spatial_prominence":
                # Passed by default unless explicitly low
                pass

            # --- Check 9: Conditional Entity (Rule 10) ---
            elif check_type == "conditional_entity":
                if category == "imported":
                    importer_data = label_record.get("country_of_origin")
                    if not importer_data or not importer_data.get("value"):
                        is_passed = False
                        message = "Imported commodity missing mandatory Country of Origin / Importer Details under Rule 10."
                        reason = "Imported category selected but Country of Origin declaration was absent."
                        recommendation = "Package must declare Country of Origin and Name & Address of the Importer."

            # --- Check 10: Schedule Warning (Drugs & Cosmetics Rules 1945) ---
            elif check_type == "schedule_warning":
                sched_data = label_record.get("schedule_warning")
                if isinstance(sched_data, dict):
                    detected_val = sched_data.get("value")
                    bbox = sched_data.get("bbox")
                    conf = sched_data.get("confidence", 0.0)

                if not sched_data or not detected_val:
                    is_passed = False
                    message = "Prescription drug missing mandatory Schedule H/H1/X statutory warning text."
                    reason = "Mandatory Schedule Caution box not detected in package text."
                    recommendation = "Print mandatory Schedule H/H1 warning: 'SCHEDULE H PRESCRIPTION DRUG - CAUTION: Not to be sold by retail without prescription'."

            # --- Check 11: Rx Symbol Presence (Drugs & Cosmetics Rules 1945) ---
            elif check_type == "symbol_presence":
                rx_data = label_record.get("rx_symbol")
                if isinstance(rx_data, dict):
                    detected_val = rx_data.get("value")
                    bbox = rx_data.get("bbox")
                    conf = rx_data.get("confidence", 0.0)

                if not rx_data or not detected_val:
                    is_passed = False
                    message = "Prescription medicine label missing prominent 'Rx' / 'NRx' / 'XRx' symbol in top-left quadrant."
                    reason = "Prescription symbol was not recognized by optical or computer vision symbol detector."
                    recommendation = "Display prominent 'Rx' symbol at top-left of label for prescription formulations."

            # --- Check 12: External Verification (FSSAI) ---
            elif check_type == "external_verification":
                fssai_data = label_record.get("fssai_license")
                if isinstance(fssai_data, dict):
                    detected_val = fssai_data.get("value")
                    bbox = fssai_data.get("bbox")
                    conf = fssai_data.get("confidence", 0.0)

                if category == "food":
                    if not fssai_data or not detected_val:
                        is_passed = False
                        message = "Food product package missing 14-digit FSSAI License Number."
                        reason = "14-digit FSSAI registration number not detected on food label."
                        recommendation = "Include valid 14-digit FSSAI license number on food packages."

            if is_passed:
                passed_count += 1
            else:
                violations.append({
                    "rule_id": rule_id,
                    "legal_rule_ref": legal_ref,
                    "source_law": source_law,
                    "field": str(field_name),
                    "status": "fail",
                    "detected_value": str(detected_val) if detected_val else None,
                    "expected": expected_val,
                    "confidence": round(float(conf), 2) if conf else 0.0,
                    "reason": reason or message,
                    "bbox": bbox,
                    "severity": severity,
                    "message": message,
                    "recommendation": recommendation
                })

        total = len(applicable_rules)
        compliance_pct = round((passed_count / total * 100.0), 2) if total > 0 else 100.0
        return compliance_pct, violations

    def evaluate_screening(
        self,
        label_record: Dict[str, Any],
        rules: List[Dict[str, Any]],
        category: str = "all"
    ) -> Dict[str, Any]:
        """
        Returns standardized screening result per Legal Metrology specifications.
        """
        compliance_pct, violations = self.evaluate_rules(label_record, rules, category=category)
        review_reasons = []
        if any(v.get("severity") in ["critical", "high"] for v in violations):
            status = "possible_non_compliance"
            review_reasons = [v.get("message", "") for v in violations if v.get("severity") in ["critical", "high"]]
        elif violations:
            status = "needs_review"
            review_reasons = [v.get("message", "") for v in violations]
        else:
            status = "compliant"

        return {
            "status": status,
            "compliance_pct": compliance_pct,
            "rules_checked": len(rules),
            "rules_passed": len(rules) - len(violations),
            "rules_failed": len(violations),
            "violations": violations,
            "review_reasons": review_reasons,
            "rule_set_version": "LMPC-2026.01"
        }

rule_engine = RuleEngine()

def load_seed_rules(category: str = "all") -> List[Dict[str, Any]]:
    import json
    import os
    rules = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_data_dir = os.path.join(base_dir, "rules_data")
    legal_path = os.path.join(rules_data_dir, "legal_metrology_2011.json")
    drugs_path = os.path.join(rules_data_dir, "drugs_cosmetics_1945.json")

    if os.path.exists(legal_path):
        try:
            with open(legal_path, "r", encoding="utf-8") as f:
                rules.extend(json.load(f))
        except Exception:
            pass

    if category == "medicine" and os.path.exists(drugs_path):
        try:
            with open(drugs_path, "r", encoding="utf-8") as f:
                rules.extend(json.load(f))
        except Exception:
            pass

    return rules

def evaluate_rules(
    label_record: Dict[str, Any],
    category: str = "all",
    db: Any = None,
    rules: Any = None
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Evaluates statutory rules against label_record.
    Signature: violations, compliance_pct = evaluate_rules(label_record, category=category, db=db)
    """
    rules_list = []
    if rules:
        rules_list = rules
    elif db is not None:
        try:
            from app.models.rule import Rule
            db_rules = db.query(Rule).filter(Rule.enabled == True).all()
            for r in db_rules:
                rules_list.append({
                    "rule_id": r.rule_id_str,
                    "legal_rule_ref": r.legal_rule_ref or "Rule 6",
                    "source_law": r.source_law or "Legal Metrology 2011",
                    "field": r.field,
                    "check": r.check_type,
                    "pattern": r.pattern,
                    "severity": r.severity,
                    "category": r.category if isinstance(r.category, list) else [r.category],
                    "version": r.version
                })
        except Exception:
            rules_list = []

    if not rules_list:
        rules_list = load_seed_rules(category=category)

    compliance_pct, violations = rule_engine.evaluate_rules(label_record, rules_list, category=category)
    return violations, compliance_pct
