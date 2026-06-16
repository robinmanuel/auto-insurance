import easyocr
import numpy as np
import traceback

from modules.utils import (
    pdf_to_images,
    preprocess_fast,
    load_image
)

from modules.verification_engine import VerificationEngine


class OCRVerifier:

    def __init__(self):

        print("Loading EasyOCR...")

        self.reader = easyocr.Reader(
            ['en'],
            gpu=False
        )

        self.verifier = VerificationEngine()

        print("OCRVerifier Ready")

    # =====================================
    # MAIN
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

            if len(full_text) == 0:
                return self._empty_result("OCR returned no text")

            # ============================
            # PIPELINE
            # ============================
            document_type = self.verifier.classify_document(full_text)

            entities = self.verifier.extract_entities(full_text)
            entities["raw_text"] = full_text

            verification = self.verifier.verify(
                document_type,
                entities
            )

            confidence_score = (
                float(np.mean(all_conf)) if all_conf else 0.0
            )

            risk_penalty = max(
                0,
                100 - verification["verification_score"]
            )

            # ============================
            # LOGGING ONLY (NOT UI)
            # ============================
            print("\n========== INTERNAL DEBUG ==========")
            print("DOC TYPE:", document_type)
            print("ENTITIES:", entities)
            print("ISSUES:", verification["issues"])
            print("RISK:", risk_penalty)
            print("RAW TEXT:", full_text[:300], "...")
            print("===================================\n")

            # ============================
            # CLEAN OUTPUT (STREAMLIT ONLY)
            # ============================
            return {
                "document_type": document_type,
                "verified": verification["verified"],
                "verification_score": verification["verification_score"],
                "confidence_score": confidence_score
            }

        except Exception as e:

            print("OCR ERROR")
            print(traceback.format_exc())

            return self._empty_result(str(e))

    # =====================================
    # INPUT LOADING
    # =====================================
    def _load_input(self, file):

        images = []

        try:

            if hasattr(file, "name"):

                if file.name.lower().endswith(".pdf"):
                    images = pdf_to_images(file)
                else:
                    img = load_image(file)
                    if img is not None:
                        images.append(img)

            elif isinstance(file, str):

                if file.lower().endswith(".pdf"):
                    images = pdf_to_images(file)
                else:
                    img = load_image(file)
                    if img is not None:
                        images.append(img)

        except Exception as e:
            print("LOAD INPUT ERROR:", e)
            print(traceback.format_exc())

        return images

    # =====================================
    # OCR
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
            print("OCR RUN ERROR:", e)
            return [], []

    # =====================================
    # EMPTY RESULT
    # =====================================
    def _empty_result(self, reason):

        return {
            "document_type": "UNKNOWN",
            "verified": False,
            "verification_score": 0,
            "confidence_score": 0
        }