import logging
import numpy as np
from typing import List, Optional
from app.core.config import settings
from app.pipeline.ocr.base import BaseOCREngine
from app.pipeline.ocr.models import OCREngineResult, OCRBlock

logger = logging.getLogger("complyerg.ocr.paddleocr")


class PaddleOCREngine(BaseOCREngine):
    def __init__(self):
        self._reader = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "paddleocr"

    def is_available(self) -> bool:
        if not getattr(settings, "PADDLEOCR_ENABLED", True):
            return False
        try:
            import paddleocr  # noqa
            return True
        except ImportError:
            return False

    def _get_reader(self):
        if self._reader is None and self.is_available():
            try:
                from paddleocr import PaddleOCR
                # Initialize once with CPU execution for English/Hindi label metrology
                self._reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                self._initialized = True
            except Exception as e:
                logger.warning(f"Could not initialize PaddleOCR instance: {e}")
                self._reader = None
        return self._reader

    def extract(self, image_np: np.ndarray, **kwargs) -> OCREngineResult:
        if not self.is_available():
            return OCREngineResult(
                engine=self.name,
                available=False,
                raw_text="",
                blocks=[],
                warnings=["PaddleOCR is not installed in current Python environment."]
            )

        reader = self._get_reader()
        if reader is None:
            return OCREngineResult(
                engine=self.name,
                available=False,
                raw_text="",
                blocks=[],
                warnings=["PaddleOCR reader could not be initialized."]
            )

        try:
            ocr_result = reader.ocr(image_np, cls=True)
            blocks: List[OCRBlock] = []
            full_text_lines = []

            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    box, (text, conf) = line
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
                    clean_text = str(text).strip()
                    if clean_text:
                        blocks.append(OCRBlock(
                            text=clean_text,
                            confidence=round(float(conf), 3),
                            bbox=bbox,
                            source_variant="deskewed"
                        ))
                        full_text_lines.append(clean_text)

            avg_conf = float(np.mean([b.confidence for b in blocks])) if blocks else 0.0
            return OCREngineResult(
                engine=self.name,
                available=True,
                raw_text="\n".join(full_text_lines),
                blocks=blocks,
                average_confidence=round(avg_conf, 3),
                languages=["en"],
                warnings=[]
            )
        except Exception as exc:
            logger.error(f"PaddleOCR execution error: {exc}")
            return OCREngineResult(
                engine=self.name,
                available=True,
                raw_text="",
                blocks=[],
                warnings=[f"PaddleOCR processing error: {str(exc)}"]
            )
