import os
import cv2
import logging
import numpy as np
from PIL import Image
from typing import List, Set
from app.core.config import settings
from app.pipeline.ocr.base import BaseOCREngine
from app.pipeline.ocr.models import OCREngineResult, OCRBlock

logger = logging.getLogger("complyerg.ocr.tesseract")

# Standard Windows Tesseract paths
DEFAULT_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]


class TesseractEngine(BaseOCREngine):
    def __init__(self):
        self._cmd_path = None
        self._available_langs: Set[str] = set()
        self._detect_installation()

    @property
    def name(self) -> str:
        return "tesseract"

    def _detect_installation(self):
        # 1. Config override
        config_cmd = getattr(settings, "TESSERACT_CMD", None)
        if config_cmd and os.path.exists(config_cmd):
            self._cmd_path = config_cmd
        else:
            for p in DEFAULT_TESSERACT_PATHS:
                if os.path.exists(p):
                    self._cmd_path = p
                    break

        if self._cmd_path:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self._cmd_path
                # Check available languages
                langs_output = pytesseract.get_languages(config="")
                self._available_langs = set(langs_output)
            except Exception as e:
                logger.warning(f"Failed to query Tesseract languages: {e}")

    def is_available(self) -> bool:
        if not getattr(settings, "TESSERACT_ENABLED", True):
            return False
        try:
            import pytesseract  # noqa
            if self._cmd_path and os.path.exists(self._cmd_path):
                return True
            # Check if tesseract is in PATH
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def get_installed_languages(self) -> List[str]:
        return sorted(list(self._available_langs))

    def extract(self, image_np: np.ndarray, **kwargs) -> OCREngineResult:
        if not self.is_available():
            return OCREngineResult(
                engine=self.name,
                available=False,
                raw_text="",
                blocks=[],
                warnings=["Tesseract executable or 'pytesseract' library not available."]
            )

        try:
            import pytesseract
            from pytesseract import Output

            if self._cmd_path:
                pytesseract.pytesseract.tesseract_cmd = self._cmd_path

            # Convert BGR to RGB
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                rgb_img = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            else:
                rgb_img = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)

            pil_img = Image.fromarray(rgb_img)

            # Determine best language combination
            configured_lang = getattr(settings, "TESSERACT_LANG", "eng")
            lang_to_use = "eng"
            if "hin" in self._available_langs and "hin" in configured_lang:
                lang_to_use = "eng+hin"
            elif configured_lang in self._available_langs:
                lang_to_use = configured_lang

            psm = getattr(settings, "TESSERACT_PSM", 11)
            config = f"--psm {psm}"

            try:
                data = pytesseract.image_to_data(pil_img, lang=lang_to_use, output_type=Output.DICT, config=config)
            except Exception:
                # Fallback to pure English with standard psm
                data = pytesseract.image_to_data(pil_img, lang="eng", output_type=Output.DICT, config="--psm 6")
                lang_to_use = "eng"

            blocks: List[OCRBlock] = []
            words_by_line = {}
            n_boxes = len(data["text"])

            for i in range(n_boxes):
                text = str(data["text"][i]).strip()
                conf_val = float(data["conf"][i])

                if text and conf_val > 5.0:
                    key = (data["block_num"][i], data["line_num"][i])
                    x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                    conf_norm = min(max(conf_val / 100.0, 0.0), 1.0)

                    if key not in words_by_line:
                        words_by_line[key] = {
                            "words": [text],
                            "confs": [conf_norm],
                            "bbox": [x, y, x + w, y + h]
                        }
                    else:
                        words_by_line[key]["words"].append(text)
                        words_by_line[key]["confs"].append(conf_norm)
                        b = words_by_line[key]["bbox"]
                        words_by_line[key]["bbox"] = [
                            min(b[0], x), min(b[1], y), max(b[2], x + w), max(b[3], y + h)
                        ]

            full_text_lines = []
            for item in words_by_line.values():
                line_text = " ".join(item["words"]).strip()
                if line_text:
                    line_conf = float(np.mean(item["confs"]))
                    blocks.append(OCRBlock(
                        text=line_text,
                        confidence=round(line_conf, 3),
                        bbox=item["bbox"],
                        source_variant="original"
                    ))
                    full_text_lines.append(line_text)

            avg_conf = float(np.mean([b.confidence for b in blocks])) if blocks else 0.0

            return OCREngineResult(
                engine=self.name,
                available=True,
                raw_text="\n".join(full_text_lines),
                blocks=blocks,
                average_confidence=round(avg_conf, 3),
                languages=[lang_to_use],
                warnings=[]
            )

        except Exception as exc:
            logger.error(f"Tesseract extraction error: {exc}")
            return OCREngineResult(
                engine=self.name,
                available=True,
                raw_text="",
                blocks=[],
                warnings=[f"Tesseract processing error: {str(exc)}"]
            )
