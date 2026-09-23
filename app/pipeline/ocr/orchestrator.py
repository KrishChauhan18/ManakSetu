import logging
import numpy as np
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.pipeline.ocr.models import OrchestratedOCRResult, OCREngineResult, OCRBlock
from app.pipeline.ocr.google_vision_engine import GoogleVisionEngine
from app.pipeline.ocr.paddleocr_engine import PaddleOCREngine
from app.pipeline.ocr.tesseract_engine import TesseractEngine

logger = logging.getLogger("complyerg.ocr.orchestrator")


class OCROrchestrator:
    def __init__(self):
        self.google_engine = GoogleVisionEngine()
        self.paddle_engine = PaddleOCREngine()
        self.tesseract_engine = TesseractEngine()

    def process(self, image_np: np.ndarray, category: str = "food") -> OrchestratedOCRResult:
        min_conf = getattr(settings, "OCR_MIN_CONFIDENCE", 0.70)
        agreement_threshold = getattr(settings, "OCR_ENGINE_AGREEMENT_THRESHOLD", 0.75)

        engine_results: Dict[str, OCREngineResult] = {}
        review_reasons: List[str] = []
        warnings: List[str] = []

        # ── 1. Attempt Primary: Google Cloud Vision ───────────────────────────
        if self.google_engine.is_available():
            logger.info("Executing Primary OCR Tier: Google Cloud Vision...")
            res_google = self.google_engine.extract(image_np)
            engine_results[self.google_engine.name] = res_google
            if res_google.warnings:
                warnings.extend(res_google.warnings)

            # If confident and extracted text, we can use it
            if res_google.available and res_google.average_confidence >= min_conf and len(res_google.blocks) > 0:
                return OrchestratedOCRResult(
                    selected_engine=self.google_engine.name,
                    raw_text=res_google.raw_text,
                    blocks=res_google.blocks,
                    average_confidence=res_google.average_confidence,
                    engine_results=engine_results,
                    engine_agreement=1.0,
                    human_review_required=False,
                    review_reasons=[],
                    status="done",
                    warnings=warnings
                )

        # ── 2. Attempt Local Fallback 1: PaddleOCR ────────────────────────────
        if self.paddle_engine.is_available():
            logger.info("Executing Secondary OCR Tier: PaddleOCR Local Fallback...")
            res_paddle = self.paddle_engine.extract(image_np)
            engine_results[self.paddle_engine.name] = res_paddle
            if res_paddle.warnings:
                warnings.extend(res_paddle.warnings)

            if res_paddle.available and res_paddle.average_confidence >= min_conf and len(res_paddle.blocks) > 0:
                return OrchestratedOCRResult(
                    selected_engine=self.paddle_engine.name,
                    raw_text=res_paddle.raw_text,
                    blocks=res_paddle.blocks,
                    average_confidence=res_paddle.average_confidence,
                    engine_results=engine_results,
                    engine_agreement=1.0,
                    human_review_required=False,
                    review_reasons=[],
                    status="done",
                    warnings=warnings
                )

        # ── 3. Attempt Tertiary Fallback: Tesseract ───────────────────────────
        if self.tesseract_engine.is_available():
            logger.info("Executing Tertiary OCR Tier: Tesseract Local Fallback...")
            res_tess = self.tesseract_engine.extract(image_np)
            engine_results[self.tesseract_engine.name] = res_tess
            if res_tess.warnings:
                warnings.extend(res_tess.warnings)

            if res_tess.available and len(res_tess.blocks) > 0:
                is_marginal = res_tess.average_confidence < min_conf
                if is_marginal:
                    review_reasons.append(
                        f"Tesseract OCR confidence ({res_tess.average_confidence*100:.1f}%) is below minimum statutory threshold ({min_conf*100:.0f}%)."
                    )

                return OrchestratedOCRResult(
                    selected_engine=self.tesseract_engine.name,
                    raw_text=res_tess.raw_text,
                    blocks=res_tess.blocks,
                    average_confidence=res_tess.average_confidence,
                    engine_results=engine_results,
                    engine_agreement=0.85 if not is_marginal else 0.60,
                    human_review_required=is_marginal,
                    review_reasons=review_reasons,
                    status="needs_review" if is_marginal else "done",
                    next_action="Review package text manually if OCR quality is degraded." if is_marginal else None,
                    warnings=warnings
                )

        # ── 4. If No Engine Succeeded in Extracting Text ───────────────────────
        best_candidate: Optional[OCREngineResult] = None
        for res in engine_results.values():
            if res.blocks and (best_candidate is None or len(res.blocks) > len(best_candidate.blocks)):
                best_candidate = res

        if best_candidate and best_candidate.blocks:
            return OrchestratedOCRResult(
                selected_engine=best_candidate.engine,
                raw_text=best_candidate.raw_text,
                blocks=best_candidate.blocks,
                average_confidence=best_candidate.average_confidence,
                engine_results=engine_results,
                engine_agreement=0.50,
                human_review_required=True,
                review_reasons=["Low OCR confidence across available engines."],
                status="needs_review",
                next_action="Capture a closer image with improved lighting and reduced glare.",
                warnings=warnings
            )

        # Total failure: No readable text detected
        return OrchestratedOCRResult(
            selected_engine=None,
            raw_text="",
            blocks=[],
            average_confidence=0.0,
            engine_results=engine_results,
            engine_agreement=0.0,
            human_review_required=True,
            review_reasons=["No readable text detected across all available OCR engines."],
            status="needs_review",
            next_action="Capture a closer image with improved lighting and reduced glare.",
            warnings=warnings or ["All OCR engines failed or were unavailable."]
        )


ocr_orchestrator = OCROrchestrator()
