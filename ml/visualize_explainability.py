import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Any, Optional

def generate_annotated_label_image(
    image_path: str,
    label_record: Dict[str, Any],
    violations: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Draws explainability bounding boxes on the original label image:
    - Green for passed statutory fields
    - Red for failed / violation fields
    - Yellow for warnings / manual review fields
    Each box is tagged with the field name, detected value, and statutory citation.
    """
    if not os.path.exists(image_path):
        return image_path

    try:
        pil_img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(pil_img)
        img_w, img_h = pil_img.size

        # Build map of violation fields
        violation_fields = {}
        for v in violations:
            fkey = v.get("field", "")
            violation_fields[fkey] = v

        # Colors (RGB)
        COLOR_PASS = (16, 185, 129)     # Emerald Green
        COLOR_FAIL = (239, 68, 68)      # Crimson Red
        COLOR_WARN = (245, 158, 11)     # Amber Yellow

        # Try loading standard font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", size=max(14, int(img_h * 0.025)))
        except Exception:
            font = ImageFont.load_default()

        if label_record:
            for fkey, fval in label_record.items():
                if isinstance(fval, dict) and fval.get("bbox"):
                    bbox = fval["bbox"]
                    if len(bbox) == 4 and sum(bbox) > 0:
                        x1, y1, x2, y2 = bbox
                        # Clamp to image bounds
                        x1 = max(0, min(x1, img_w - 1))
                        y1 = max(0, min(y1, img_h - 1))
                        x2 = max(x1 + 10, min(x2, img_w))
                        y2 = max(y1 + 10, min(y2, img_h))

                        # Determine status
                        if fkey in violation_fields:
                            v_info = violation_fields[fkey]
                            sev = v_info.get("severity", "high")
                            box_color = COLOR_FAIL if sev in ["critical", "high"] else COLOR_WARN
                            status_label = f"FAIL: {v_info.get('rule_id', fkey)}"
                        else:
                            box_color = COLOR_PASS
                            status_label = f"PASS: {fkey.replace('_', ' ').title()}"

                        # Draw thick rectangle
                        for offset in range(3):
                            draw.rectangle(
                                [x1 - offset, y1 - offset, x2 + offset, y2 + offset],
                                outline=box_color
                            )

                        # Draw text background banner
                        text_content = f"{status_label} ({fval.get('confidence', 0.9)*100:.0f}%)"
                        text_bbox = draw.textbbox((x1, max(0, y1 - 22)), text_content, font=font)
                        draw.rectangle(
                            [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
                            fill=box_color
                        )
                        draw.text((x1, max(0, y1 - 22)), text_content, fill=(255, 255, 255), font=font)

        if not output_path:
            dir_name = os.path.dirname(image_path)
            base_name = os.path.basename(image_path)
            output_path = os.path.join(dir_name, f"annotated_{base_name}")

        pil_img.save(output_path, quality=92)
        return output_path
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating annotated image: {e}")
        return image_path
