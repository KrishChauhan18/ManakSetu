import re
from datetime import datetime
from typing import Dict, Any, List, Tuple

class MetrologyRuleValidator:
    """
    Rule 6 Metrology Validator according to Indian Legal Metrology (Packaged Commodities) Rules, 2011.
    Evaluates mandatory statutory declarations and chronological date logic.
    """
    MANDATORY_FIELDS = {
        "manufacturer": "Rule 6(1)(a) - Name & address of Manufacturer / Packer / Importer",
        "net_quantity": "Rule 6(1)(b) - Net quantity in standard metric units",
        "mrp": "Rule 6(1)(e) - Maximum Retail Price (inclusive of all taxes)",
        "mfg_date": "Rule 6(1)(d) - Month and year of manufacture / packaging",
        "consumer_care": "Rule 6(1)(f) - Consumer care phone/email/address details"
    }

    def validate(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates extracted label record against Rule 6 statutory rules.
        Returns:
        {
          "is_compliant": bool,
          "compliance_score": float,
          "violations": [list of violation dicts],
          "total_penalty": int
        }
        """
        violations = []
        total_penalty = 0

        # 1. Check Mandatory Rule 6(1) Declarations
        for field_key, rule_desc in self.MANDATORY_FIELDS.items():
            field_val = extracted_fields.get(field_key)
            if not field_val or not field_val.get("value"):
                total_penalty += 25
                violations.append({
                    "rule_id": f"LM2011-R6-MISSING-{field_key.upper()}",
                    "rule_name": f"Rule 6(1) Missing Declaration: {field_key.replace('_', ' ').title()}",
                    "field": field_key,
                    "severity": "CRITICAL",
                    "penalty": 25,
                    "description": f"Mandatory declaration '{field_key}' is absent from the packaging label. Statutory reference: {rule_desc}.",
                    "recommendation": f"Ensure '{field_key}' is prominently printed in legible font matching Rule 6 font size standards."
                })

        # 2. Check Chronological Consistency (Manufacturing Date <= Expiry Date)
        mfg_data = extracted_fields.get("mfg_date")
        exp_data = extracted_fields.get("expiry_date")

        if mfg_data and mfg_data.get("value") and exp_data and exp_data.get("value"):
            try:
                m_str = str(mfg_data["value"]).strip()
                e_str = str(exp_data["value"]).strip()
                
                m_dt = self._parse_date(m_str)
                e_dt = self._parse_date(e_str)

                if m_dt and e_dt and m_dt > e_dt:
                    total_penalty += 25
                    violations.append({
                        "rule_id": "LM2011-R6-INVALID-DATE-ORDER",
                        "rule_name": "Rule 6 Date Logic Failure: Mfg Date Exceeds Expiry",
                        "field": "expiry_date",
                        "severity": "CRITICAL",
                        "penalty": 25,
                        "description": f"Manufacturing date ({m_str}) is chronologically later than Expiry date ({e_str}).",
                        "recommendation": "Correct printed manufacturing and expiration dates for statutory logical consistency."
                    })
            except Exception:
                pass

        compliance_score = float(max(0, 100 - total_penalty))
        is_compliant = (len(violations) == 0)

        return {
            "is_compliant": is_compliant,
            "compliance_score": compliance_score,
            "violations": violations,
            "total_penalty": total_penalty
        }

    def _parse_date(self, date_str: str) -> Any:
        for fmt in ("%m/%Y", "%d/%m/%Y", "%m-%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                pass
        return None

metrology_validator = MetrologyRuleValidator()
