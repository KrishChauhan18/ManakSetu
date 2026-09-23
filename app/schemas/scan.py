from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from datetime import datetime

class FieldExtractionDetail(BaseModel):
    value: Optional[str] = None
    unit: Optional[str] = None
    confidence: float = 0.0
    bbox: Optional[List[int]] = None
    source: str = "unknown"

class ViolationSchema(BaseModel):
    id: Optional[int] = None
    rule_id: str
    legal_rule_ref: Optional[str] = "Rule 6"
    source_law: Optional[str] = "Legal Metrology 2011"
    field: str
    severity: str
    status: Optional[str] = "fail"
    detected_value: Optional[str] = None
    expected: Optional[str] = None
    confidence: float = 0.0
    reason: Optional[str] = None
    bbox: Optional[List[int]] = None
    message: str
    recommendation: Optional[str] = None

    class Config:
        from_attributes = True

class ScanResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    image_path: str
    image_url: Optional[str] = None
    annotated_image_url: Optional[str] = None
    pdf_report_url: Optional[str] = None
    category: str
    status: str
    compliance_pct: float = 0.0
    label_record: Optional[Dict[str, Any]] = None
    violations: List[ViolationSchema] = []
    created_at: datetime
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

    class Config:
        from_attributes = True

class ScanUploadResponse(BaseModel):
    scan_id: int
    status: str
    message: str
    image_url: str
    annotated_image_url: str
    pdf_report_url: str
    compliance_pct: float
    violations: List[ViolationSchema] = []
    label_record: Optional[Dict[str, Any]] = None

class OverrideFieldRequest(BaseModel):
    field: str
    new_value: Any
    reason: str
