import os
import cv2
import logging
import numpy as np
from typing import List
from app.core.config import settings
from app.pipeline.ocr.base import BaseOCREngine
from app.pipeline.ocr.models import OCREngineResult, OCRBlock

logger = logging.getLogger("complyerg.ocr.google_vision")


class GoogleVisionEngine(BaseOCREngine):
    @property
    def name(self) -> str:
        return "google_vision"

    def is_available(self) -> bool:
        if not getattr(settings, "GOOGLE_VISION_ENABLED", False):
            return False
        
        creds_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", None)
        if not creds_env or not os.path.exists(creds_env):
            return False

        try:
            import google.cloud.vision  # noqa
            return True
        except ImportError:
            return False

    def extract(self, image_np: np.ndarray, **kwargs) -> OCREngineResult:
        if not self.is_available():
            return OCREngineResult(
                engine=self.name,
                available=False,
                raw_text="",
                blocks=[],
                warnings=["Google Cloud Vision is not enabled or credentials are not configured."]
            )

        try:
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()

            # Encode image to bytes
            success, encoded_image = cv2.imencode('.jpg', image_np)
            if not success:
                return OCREngineResult(
                    engine=self.name,
                    available=True,
                    raw_text="",
                    blocks=[],
                    warnings=["Failed to encode image to JPG for Google Vision API."]
                )

            content = encoded_image.tobytes()
            image = vision.Image(content=content)

            response = client.document_text_detection(image=image)
            if response.error.message:
                logger.warning(f"Google Cloud Vision API error code {response.error.code}: {response.error.message}")
                return OCREngineResult(
                    engine=self.name,
                    available=True,
                    raw_text="",
                    blocks=[],
                    warnings=[f"Google Vision API error: {response.error.message}"]
                )

            blocks: List[OCRBlock] = []
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            languages = []

            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    for lang in page.property.detected_languages:
                        if lang.language_code not in languages:
                            languages.append(lang.language_code)

                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            p_text = "".join([word_to_text(w) for w in paragraph.words]).strip()
                            if not p_text:
                                continue

                            vertices = paragraph.bounding_box.vertices
                            if len(vertices) >= 4:
                                xs = [v.x for v in vertices]
                                ys = [v.y for v in vertices]
                                bbox = [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
                            else:
                                bbox = [0, 0, 0, 0]

                            conf = float(paragraph.confidence) if paragraph.confidence else 0.85
                            blocks.append(OCRBlock(
                                text=p_text,
                                confidence=round(conf, 3),
                                bbox=bbox,
                                source_variant="original"
                            ))

            avg_conf = float(np.mean([b.confidence for b in blocks])) if blocks else 0.0
            return OCREngineResult(
                engine=self.name,
                available=True,
                raw_text=full_text,
                blocks=blocks,
                average_confidence=round(avg_conf, 3),
                languages=languages,
                warnings=[]
            )

        except Exception as exc:
            logger.error(f"Google Vision extraction exception: {exc}")
            return OCREngineResult(
                engine=self.name,
                available=False,
                raw_text="",
                blocks=[],
                warnings=[f"Google Cloud Vision processing failed: {str(exc)}"]
            )


def word_to_text(word) -> str:
    text = "".join([symbol.text for symbol in word.symbols])
    # Check break
    last_symbol = word.symbols[-1] if word.symbols else None
    if last_symbol and last_symbol.property and last_symbol.property.detected_break:
        text += " "
    return text
