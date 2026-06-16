import easyocr
import numpy as np
import traceback

from modules.utils import (
    pdf_to_images,
    preprocess_fast,
    load_image
)

from modules.verification_engine import VerificationEngine
from modules.context_validator import ContextValidator


class OCRVerifier:

    def __init__(self):

        print("Loading EasyOCR...")

        self.reader = easyocr.Reader(
            ['en'],
            gpu=False
        )

        self.verifier = VerificationEngine()
        self.context = ContextValidator()

        print("OCRVerifier Ready")

    # =====================================
    # MAIN PIPELINE
    # =====================================
    def process(self, file):

        try:

            images = self._load_input(file)

            if not images:
                return self._empty_result("No images loaded")

            all_text = []
            all_conf = []

            for img in images:

                texts, confs = self._run_ocr(img)

                all_text.extend(texts)
                all_conf.extend(confs)

            full_text = " ".join(all_text).strip()

            if not full_text:
                return self._empty_result("OCR returned empty text")

            # =====================================
            # STEP 1: CLASSIFY
            # =====================================
            document_type = self.verifier.classify_document(full_text)

            # =====================================
            # STEP 2: EXTRACT
            # =====================================
            entities = self.verifier.extract_entities(full_text)
            entities["raw_text"] = full_text

            # =====================================
            # STEP 3: CONTEXT VALIDATION (NEW FIX)
            # =====================================
            context_result = self.context.validate(
                document_type,
                entities,
                full_text
            )

            # =====================================
            # STEP 4: VERIFICATION (FINAL SCORE)
            # =====================================
            verification = self.verifier.verify(
                document_type,
                entities,
                context_boost=context_result["score_boost"]
            )

            # =====================================
            # CONFIDENCE SCORE
            # =====================================
            confidence_score = (
                float(np.mean(all_conf))
                if all_conf else 0.0
            )

            # =====================================
            # RISK SCORE
            # =====================================
            risk_penalty = max(
                0,
                100 - verification["verification_score"]
            )

            return {
                "document_type": document_type,
                "verified": verification["verified"],
                "verification_score": verification["verification_score"],
                "confidence_score": confidence_score,
                "entities": entities,
                "issues": verification["issues"] + context_result["issues"],
                "risk_penalty": risk_penalty,
                "raw_text": full_text
            }

        except Exception as e:

            print("OCR PIPELINE ERROR")
            print(traceback.format_exc())

            return self._empty_result(str(e))

    # =====================================
    # INPUT LOADING
    # =====================================
    def _load_input(self, file):

        images = []

        try:

            # Streamlit upload
            if hasattr(file, "name"):

                if file.name.lower().endswith(".pdf"):
                    images = pdf_to_images(file)
                else:
                    img = load_image(file)
                    if img is not None:
                        images.append(img)

            # file path
            elif isinstance(file, str):

                if file.lower().endswith(".pdf"):
                    images = pdf_to_images(file)
                else:
                    img = load_image(file)
                    if img is not None:
                        images.append(img)

        except Exception as e:
            print("INPUT ERROR:", e)
            print(traceback.format_exc())

        return images

    # =====================================
    # OCR ENGINE
    # =====================================
    def _run_ocr(self, img):

        try:

            processed = preprocess_fast(img)

            results = self.reader.readtext(
                processed,
                detail=1
            )

            texts = []
            confs = []

            for item in results:

                if len(item) < 3:
                    continue

                _, text, conf = item

                text = str(text).strip()

                if not text:
                    continue

                texts.append(text)

                try:
                    confs.append(float(conf))
                except:
                    confs.append(0.5)

            return texts, confs

        except Exception as e:

            print("OCR ERROR:", e)
            return [], []

    # =====================================
    # EMPTY RESULT
    # =====================================
    def _empty_result(self, reason):

        return {
            "document_type": "UNKNOWN",
            "verified": False,
            "verification_score": 0,
            "confidence_score": 0.0,
            "entities": {
                "license_numbers": [],
                "vehicle_numbers": [],
                "dates": [],
                "engine_numbers": [],
                "chassis_numbers": [],
                "policy_numbers": [],
                "persons": [],
                "organizations": [],
                "locations": [],
                "raw_text": ""
            },
            "issues": [
                reason,
                "Low OCR confidence"
            ],
            "risk_penalty": 100,
            "raw_text": ""
        }