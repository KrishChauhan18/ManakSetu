import re
from typing import Dict, Any

class FieldExtractor:
    """
    Robust regex and pattern-based field extractor for Legal Metrology labels.
    """
    def extract_fields(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        raw_text = ocr_result.get("raw_text", "")
        # Normalize text for easier matching
        clean_text = re.sub(r'\s+', ' ', raw_text)
        
        extracted = {}

        # 1. MRP Extraction (Matches: MRP, M.R.P., Max. Retail Price followed by Rs, ₹, or numbers)
        mrp_match = re.search(r'(?:MRP|M\.R\.P\.?|Max\.?\s*Retail\s*Price)[:\s]*(?:Rs\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)', clean_text, re.IGNORECASE)
        if mrp_match:
            extracted["mrp"] = {
                "value": mrp_match.group(1),
                "confidence": 0.90,
                "source": ocr_result.get("selected_engine", "tesseract")
            }
        else:
            # Fallback: look for standalone currency symbols with numbers
            curr_match = re.search(r'(?:Rs\.?|₹)\s*([0-9]+(?:\.[0-9]{1,2})?)', clean_text, re.IGNORECASE)
            if curr_match:
                extracted["mrp"] = {
                    "value": curr_match.group(1),
                    "confidence": 0.75,
                    "source": ocr_result.get("selected_engine", "tesseract")
                }
            else:
                extracted["mrp"] = {"value": None, "confidence": 0.0, "source": "none"}

        # 2. Net Quantity Extraction (Matches: Net Qty, Net Weight, Net Volume + numbers + units like g, kg, ml, l, pcs)
        qty_match = re.search(r'(?:Net\s*(?:Qty|Quantity|Weight|Contents|Content)|Contents)[:\s]*([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|gms|kg|kilograms|ml|L|ltr|litres|pcs|pieces))', clean_text, re.IGNORECASE)
        if qty_match:
            extracted["net_quantity"] = {
                "value": qty_match.group(1).strip(),
                "confidence": 0.88,
                "source": ocr_result.get("selected_engine", "tesseract")
            }
        else:
            # Fallback: search for numbers with standard units anywhere in text
            unit_match = re.search(r'\b([0-9]+(?:\.[0-9]+)?\s*(?:g|gm|kg|ml|L|pcs))\b', clean_text, re.IGNORECASE)
            if unit_match:
                extracted["net_quantity"] = {
                    "value": unit_match.group(1).strip(),
                    "confidence": 0.70,
                    "source": ocr_result.get("selected_engine", "tesseract")
                }
            else:
                extracted["net_quantity"] = {"value": None, "confidence": 0.0, "source": "none"}

        # 3. Manufacturer / Packer Details
        mfg_match = re.search(r'(?:Manufactured|Mfd\.?|Packed|Marketed)\s*(?:by|and\s*marketed\s*by)?[:\s]*([A-Za-z0-9\s,\.-]{3,50})', clean_text, re.IGNORECASE)
        if mfg_match:
            extracted["manufacturer"] = {
                "value": mfg_match.group(1).strip(),
                "confidence": 0.80,
                "source": ocr_result.get("selected_engine", "tesseract")
            }
        else:
            extracted["manufacturer"] = {"value": None, "confidence": 0.0, "source": "none"}

        # 4. Manufacturing / Packing Date
        date_match = re.search(r'(?:Mfg\.?|Packed\s*(?:on)?|Date\s*of\s*Mfg)[:\s]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{2,4}|[0-9]{2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[0-9]{2,4})', clean_text, re.IGNORECASE)
        if date_match:
            extracted["mfg_date"] = {
                "value": date_match.group(1).strip(),
                "confidence": 0.85,
                "source": ocr_result.get("selected_engine", "tesseract")
            }
        else:
            extracted["mfg_date"] = {"value": None, "confidence": 0.0, "source": "none"}

        # 5. Consumer Care / Helpline
        care_match = re.search(r'(?:Consumer\s*Care|Helpline|Customer\s*Support|Email)[:\s]*([A-Za-z0-9@\.\-\s]{5,40})', clean_text, re.IGNORECASE)
        if care_match:
            extracted["consumer_care"] = {
                "value": care_match.group(1).strip(),
                "confidence": 0.80,
                "source": ocr_result.get("selected_engine", "tesseract")
            }
        else:
            extracted["consumer_care"] = {"value": None, "confidence": 0.0, "source": "none"}

        return extracted


field_extractor = FieldExtractor()


def extract_fields(raw_text: str, blocks: list = None, category: str = "all") -> dict:
    """
    Module-level convenience wrapper for use by ocr_engine.extract_and_parse().
    Adapts raw text + blocks into the ocr_result dict format that FieldExtractor expects.
    """
    ocr_result = {
        "raw_text": raw_text,
        "blocks": blocks or [],
        "selected_engine": "unknown",
    }
    return field_extractor.extract_fields(ocr_result)