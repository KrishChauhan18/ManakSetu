from abc import ABC, abstractmethod
import numpy as np
from app.pipeline.ocr.models import OCREngineResult


class BaseOCREngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the OCR engine."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the engine is installed, configured, and usable."""
        pass

    @abstractmethod
    def extract(self, image_np: np.ndarray, **kwargs) -> OCREngineResult:
        """Performs OCR and returns a standardized OCREngineResult."""
        pass
