import easyocr
import re
import numpy as np

from modules.utils import pdf_to_images, preprocess_fast, load_image


class OCRVerifier:

    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)

        self.patterns = {
            "license": r"[A-Z]{2}\d{2}[A-Z0-9]{11,13}",
            "vehicle": r"[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{3,4}",
            "date": r"\d{2}[/-]\d{2}[/-]\d{4}"
        }

    # =====================================================
    # MAIN
    # =====================================================
    def process(self, file):

        images = self._load_input(file)

        all_text = []
        all_conf = []

        for img in images:
            text, conf = self._run_ocr(img)
            all_text.extend(text)
            all_conf.extend(conf)

        full_text = " ".join(all_text)

        fields = self._extract_fields(full_text)
        validation = self._validate(fields, all_conf)

        return {
            "raw_text": full_text,
            "fields": fields,
            "validation": validation,
            "confidence_score": float(np.mean(all_conf)) if all_conf else 0.0,
            "risk_penalty": self._compute_penalty(validation)
        }

    # =====================================================
    # INPUT HANDLING (IMPORTANT FIX)
    # =====================================================
    def _load_input(self, file):

        if hasattr(file, "name") and file.name.lower().endswith(".pdf"):
            return pdf_to_images(file)

        return [load_image(file)]

    # =====================================================
    # OCR
    # =====================================================
    def _run_ocr(self, img):

        processed = preprocess_fast(img)
        results = self.reader.readtext(processed)

        texts, confs = [], []

        for _, text, conf in results:
            if text:
                texts.append(text)
                confs.append(float(conf))

        return texts, confs

    # =====================================================
    # EXTRACTION
    # =====================================================
    def _extract_fields(self, text):

        return {
            "license_number": re.search(self.patterns["license"], text).group(0)
            if re.search(self.patterns["license"], text) else None,

            "vehicle_number": re.search(self.patterns["vehicle"], text).group(0)
            if re.search(self.patterns["vehicle"], text) else None,

            "dates": re.findall(self.patterns["date"], text),

            "name": None
        }

    # =====================================================
    # VALIDATION
    # =====================================================
    def _validate(self, fields, confs):

        mean_conf = float(np.mean(confs)) if confs else 0.0

        return {
            "license_valid": fields["license_number"] is not None,
            "vehicle_valid": fields["vehicle_number"] is not None,
            "missing_fields": [k for k, v in fields.items() if not v],
            "low_confidence": mean_conf < 0.6,
            "date_detected": len(fields["dates"]) > 0
        }

    # =====================================================
    # PENALTY
    # =====================================================
    def _compute_penalty(self, validation):

        penalty = 0
        if validation["missing_fields"]:
            penalty += 30
        if not validation["license_valid"]:
            penalty += 40
        if validation["low_confidence"]:
            penalty += 20
        if not validation["date_detected"]:
            penalty += 10

        return penalty