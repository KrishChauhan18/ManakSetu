import os
from typing import Dict, Any
from app.core.config import settings
from app.pipeline.ocr.google_vision_engine import GoogleVisionEngine
from app.pipeline.ocr.paddleocr_engine import PaddleOCREngine
from app.pipeline.ocr.tesseract_engine import TesseractEngine


def get_ocr_diagnostics() -> Dict[str, Any]:
    google_engine = GoogleVisionEngine()
    paddle_engine = PaddleOCREngine()
    tess_engine = TesseractEngine()

    return {
        "google_vision": {
            "enabled": bool(getattr(settings, "GOOGLE_VISION_ENABLED", False)),
            "available": google_engine.is_available(),
            "credentials_set": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", None)),
        },
        "paddleocr": {
            "enabled": bool(getattr(settings, "PADDLEOCR_ENABLED", True)),
            "available": paddle_engine.is_available(),
        },
        "tesseract": {
            "enabled": bool(getattr(settings, "TESSERACT_ENABLED", True)),
            "available": tess_engine.is_available(),
            "executable_path": tess_engine._cmd_path,
            "installed_languages": tess_engine.get_installed_languages(),
        },
        "cascade_order": ["google_vision", "paddleocr", "tesseract"]
    }
