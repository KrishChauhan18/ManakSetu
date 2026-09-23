from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OCRBlock(BaseModel):
    text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    bbox: List[int] = Field(default_factory=lambda: [0, 0, 0, 0])  # [x1, y1, x2, y2]
    source_variant: str = "original"


class OCREngineResult(BaseModel):
    engine: str
    available: bool = True
    raw_text: str = ""
    blocks: List[OCRBlock] = Field(default_factory=list)
    average_confidence: float = 0.0
    languages: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class OrchestratedOCRResult(BaseModel):
    selected_engine: Optional[str] = None
    raw_text: str = ""
    blocks: List[OCRBlock] = Field(default_factory=list)
    average_confidence: float = 0.0
    engine_results: Dict[str, OCREngineResult] = Field(default_factory=dict)
    engine_agreement: float = 1.0
    human_review_required: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    status: str = "processing"
    next_action: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
