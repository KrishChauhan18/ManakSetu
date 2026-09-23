import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

class MultiTierOCREngine:
    def __init__(self):
        self.google_enabled = os.getenv("GOOGLE_VISION_ENABLED", "false").lower() == "true"
        self.paddle_enabled = os.getenv("PADDLEOCR_ENABLED", "true").lower() == "true"
        self.tesseract_enabled = os.getenv("TESSERACT_ENABLED", "true").lower() == "true"
        
        # Lazy load or initialize models safely
        self._paddle_reader = None

    def _get_paddle_reader(self):
        if self._paddle_reader is None and self.paddle_enabled:
            try:
                from paddleocr import PaddleOCR
                # Initialize for English and Hindi as per legal metrology labels
                self._paddle_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            except Exception as e:
                print(f"Warning: Could not initialize PaddleOCR: {e}")
                self.paddle_enabled = False
        return self._paddle_reader

    def extract_lines(self, image_np: np.ndarray) -> Dict[str, Any]:
        """
        Executes the 3-tier OCR cascade:
        1. Google Cloud Vision (Primary)
        2. PaddleOCR (Secondary Local Fallback)
        3. Tesseract (Tertiary Fallback)
        """
        results = {
            "selected_engine": None,
            "raw_text": "",
            "blocks": [],
            "average_confidence": 0.0,
            "warnings": []
        }

        # --- Tier 1: Google Cloud Vision ---
        if self.google_enabled:
            try:
                # Requires google-cloud-vision and credentials configured
                from google.cloud import vision
                client = vision.ImageAnnotatorClient()
                success, encoded_image = cv2.imencode('.jpg', image_np)
                if success:
                    content = encoded_image.tobytes()
                    image = vision.Image(content=content)
                    response = client.document_text_detection(image=image)
                    if not response.error.message and response.full_text_annotation:
                        text = response.full_text_annotation.text
                        blocks = []
                        for page in response.full_text_annotation.pages:
                            for block in page.blocks:
                                for paragraph in block.paragraphs:
                                    p_text = "".join([s.text for s in paragraph.words])
                                    # Normalize box vertices to [x1, y1, x2, y2]
                                    vertices = paragraph.bounding_box.vertices
                                    if len(vertices) >= 4:
                                        x_coords = [v.x for v in vertices]
                                        y_coords = [v.y for v in vertices]
                                        bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                                    else:
                                        bbox = [0, 0, 0, 0]
                                    blocks.append({
                                        "text": p_text,
                                        "confidence": paragraph.confidence if paragraph.confidence else 0.85,
                                        "bbox": bbox
                                    })
                        results.update({
                            "selected_engine": "google_vision",
                            "raw_text": text,
                            "blocks": blocks,
                            "average_confidence": sum([b["confidence"] for b in blocks]) / len(blocks) if blocks else 0.0
                        })
                        return results
            except Exception as e:
                results["warnings"].append(f"Google Vision failed: {str(e)}")

        # --- Tier 2: PaddleOCR Fallback ---
        if self.paddle_enabled:
            try:
                reader = self._get_paddle_reader()
                if reader:
                    # PaddleOCR expects RGB or BGR numpy array
                    ocr_result = reader.ocr(image_np, cls=True)
                    if ocr_result and ocr_result[0]:
                        blocks = []
                        full_text_parts = []
                        confidences = []
                        for line in ocr_result[0]:
                            box, (text, conf) = line
                            # Convert 4-point polygon to [x1, y1, x2, y2]
                            x_coords = [p[0] for p in box]
                            y_coords = [p[1] for p in box]
                            bbox = [int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords))]
                            
                            blocks.append({
                                "text": text,
                                "confidence": float(conf),
                                "bbox": bbox
                            })
                            full_text_parts.append(text)
                            confidences.append(float(conf))
                        
                        results.update({
                            "selected_engine": "paddleocr",
                            "raw_text": "\n".join(full_text_parts),
                            "blocks": blocks,
                            "average_confidence": sum(confidences) / len(confidences) if confidences else 0.0
                        })
                        return results
            except Exception as e:
                results["warnings"].append(f"PaddleOCR failed: {str(e)}")

        # --- Tier 3: Tesseract Final Fallback ---
        if self.tesseract_enabled:
            try:
                import pytesseract
                from PIL import Image
                pil_img = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
                custom_config = r'--psm 11'
                data = pytesseract.image_to_data(pil_img, config=custom_config, output_type=pytesseract.Output.DICT)
                
                blocks = []
                full_text_parts = []
                confidences = []
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    txt = data['text'][i].strip()
                    if txt:
                        conf = float(data['conf'][i]) / 100.0 if data['conf'][i] != -1 else 0.5
                        bbox = [data['left'][i], data['top'][i], data['left'][i] + data['width'][i], data['top'][i] + data['height'][i]]
                        blocks.append({"text": txt, "confidence": conf, "bbox": bbox})
                        full_text_parts.append(txt)
                        confidences.append(conf)

                results.update({
                    "selected_engine": "tesseract",
                    "raw_text": " ".join(full_text_parts),
                    "blocks": blocks,
                    "average_confidence": sum(confidences) / len(confidences) if confidences else 0.0
                })
                return results
            except Exception as e:
                results["warnings"].append(f"Tesseract failed: {str(e)}")

        results["warnings"].append("All OCR engines failed or were disabled.")
        return results

    def extract_and_parse(self, image_np: np.ndarray, category: str = "all") -> dict:
        """
        High-level method used by scan pipeline:
        1. Runs OCR cascade to get raw text + blocks
        2. Passes raw text to field_extractor to parse labelled fields
        Returns a unified label_record dict.
        """
        from app.pipeline.field_extractor import extract_fields

        ocr_result = self.extract_lines(image_np)
        raw_text = ocr_result.get("raw_text", "")
        blocks = ocr_result.get("blocks", [])

        # Extract structured fields from OCR text
        label_record = extract_fields(raw_text, blocks=blocks, category=category)

        # Attach OCR metadata for audit trail
        label_record["_ocr_meta"] = {
            "engine": ocr_result.get("selected_engine"),
            "avg_confidence": ocr_result.get("average_confidence", 0.0),
            "warnings": ocr_result.get("warnings", []),
            "block_count": len(blocks),
        }

        return label_record


# Module-level singleton — imported by scan.py as `from app.pipeline.ocr_engine import ocr_engine`
ocr_engine = MultiTierOCREngine()