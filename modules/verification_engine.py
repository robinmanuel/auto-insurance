import re
from datetime import datetime


class VerificationEngine:

    # =====================================================
    # DOCUMENT CLASSIFICATION (IMPROVED)
    # =====================================================
    def classify_document(self, text):

        if not text:
            return "UNKNOWN"

        t = text.lower()

        if "driving" in t and ("licence" in t or "license" in t):
            return "DRIVING_LICENSE"

        rc_keywords = ["registration", "rc book", "chassis", "engine", "regn", "rogn", "fitness", "vehicle class"]
        if any(k in t for k in rc_keywords):
            return "RC_BOOK"

        invoice_keywords = ["invoice", "subtotal", "total", "amount", "tax"]
        if any(k in t for k in invoice_keywords):
            return "INVOICE"

        if "insurance" in t or "policy" in t:
            return "INSURANCE_POLICY"

        return "UNKNOWN"

    # =====================================================
    # OCR CLEANING (SMART NORMALIZATION)
    # =====================================================
    def clean_text(self, text):

        if not text:
            return ""

        text = text.upper()

        corrections = {
            "VEHICK": "VEHICLE",
            "REGISBRATION": "REGISTRATION",
            "CERTIFKCATE": "CERTIFICATE",
            "DATC": "DATE",
            "DRVING": "DRIVING",
            "LICENCEE": "LICENSE",
            "COMMERCKAL": "COMMERCIAL",
            "WHLICLE": "VEHICLE",
            "NUMBOR": "NUMBER",
            "ROGN": "REGN",
            "HSTEDABOVE": "",
            "APARTMENTS": "",
            "GENCRATEDINVOICE": "INVOICE",
            "CHASSLS": "CHASSIS",
            "CHASIS": "CHASSIS",
            "CHASS1S": "CHASSIS",
            "ENG1NE": "ENGINE",
            "VEH1CLE": "VEHICLE"
        }

        for w, c in corrections.items():
            text = text.replace(w, c)

        return text

    # =====================================================
    # HELPERS
    # =====================================================
    def _dedup(self, arr):
        return list(dict.fromkeys(arr))

    def _valid_mix(self, s):
        return bool(re.search(r"[A-Z]", s)) and bool(re.search(r"\d", s))

    # =====================================================
    # ENTITY EXTRACTION (ROBUST + REAL-WORLD READY)
    # =====================================================
    def extract_entities(self, text):

        text = self.clean_text(text)

        entities = {
            "license_numbers": [],
            "vehicle_numbers": [],
            "dates": [],
            "engine_numbers": [],
            "chassis_numbers": [],
            "policy_numbers": [],
            "persons": [],
            "organizations": [],
            "locations": [],
            "raw_text": text
        }

        # -------------------------
        # LICENSE NUMBER (DL)
        # -------------------------
        entities["license_numbers"] = re.findall(
            r"\b[A-Z]{2}\d{2}\s?\d{10,13}\b",
            text
        )

        # -------------------------
        # VEHICLE NUMBER (SMART HYBRID EXTRACTION)
        # -------------------------
        vehicle_candidates = []

        # Standard formats (TN99AB1234)
        vehicle_candidates += re.findall(
            r"\b[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{3,6}\b",
            text
        )

        # OCR broken formats (PZOZP3507 etc.)
        vehicle_candidates += re.findall(
            r"\b[A-Z]{5,10}\d{2,6}\b",
            text
        )

        # label-based extraction
        vehicle_candidates += re.findall(
            r"(?:REGN|REGISTRATION|VEHICLE NO|NO|NUMBER)\s*[:\-]?\s*([A-Z0-9]{6,15})",
            text
        )

        # FILTERING (IMPORTANT FIX)
        vehicle_filtered = []
        blacklist = {
            "CERTIFICATE", "ENGINE", "CHASSIS", "INVOICE",
            "PRADESH482003", "COMMERCIAL", "INDIVIDUAL"
        }

        for v in vehicle_candidates:
            v = v.strip()

            if v in blacklist:
                continue

            if not self._valid_mix(v):
                continue

            if 6 <= len(v) <= 15:
                vehicle_filtered.append(v)

        entities["vehicle_numbers"] = self._dedup(vehicle_filtered)

        # -------------------------
        # DATES (SMARTER)
        # -------------------------
        date_patterns = [
            r"\b\d{2}[/-]\d{2}[/-]\d{2,4}\b",
            r"\b\d{1,2}-[A-Z]{3}-\d{2,4}\b",
            r"\b\d{1,2}[.-]\d{1,2}[.-]\d{2,4}\b"
        ]

        for p in date_patterns:
            entities["dates"] += re.findall(p, text)

        entities["dates"] = self._dedup(entities["dates"])

        # -------------------------
        # CHASSIS NUMBER (STRICT)
        # -------------------------
        chassis = re.findall(r"\b[A-Z0-9]{15,25}\b", text)

        blacklist2 = {
            "REGISTRATION", "CERTIFICATE", "COMMERCIAL",
            "INDIVIDUAL", "MADHYA", "PRADESH",
            "INVOICE", "ENGINE"
        }

        entities["chassis_numbers"] = [
            x for x in chassis
            if len(x) >= 17 and not any(b in x for b in blacklist2)
        ]

        entities["chassis_numbers"] = self._dedup(entities["chassis_numbers"])

        # -------------------------
        # ENGINE NUMBER
        # -------------------------
        engine = re.findall(r"\b[A-Z0-9]{8,20}\b", text)

        entities["engine_numbers"] = [
            x for x in engine
            if not x.isalpha()
        ]

        entities["engine_numbers"] = self._dedup(entities["engine_numbers"])

        # -------------------------
        # POLICY
        # -------------------------
        entities["policy_numbers"] = re.findall(
            r"POLICY[\s:-]*([A-Z0-9\-]+)",
            text
        )

        return entities

    # =====================================================
    # SMART VERIFICATION ENGINE (IMPROVED LOGIC)
    # =====================================================
    def verify(self, document_type, entities, **kwargs):

        score = 0
        issues = []

        ocr_conf = kwargs.get("confidence_score", 0.7)

        # =====================================================
        # DRIVING LICENSE
        # =====================================================
        if document_type == "DRIVING_LICENSE":

            if entities["license_numbers"]:
                score += 60
            else:
                issues.append("License number missing")

            if len(entities["dates"]) >= 2:
                score += 30
            else:
                issues.append("Issue/Expiry dates missing")

        # =====================================================
        # RC BOOK (SMART CHECKS)
        # =====================================================
        elif document_type == "RC_BOOK":

            chassis_ok = bool(entities["chassis_numbers"])
            engine_ok = bool(entities["engine_numbers"])
            vehicle_ok = bool(entities["vehicle_numbers"])

            if chassis_ok:
                score += 35
            else:
                issues.append("Chassis number missing")

            if engine_ok:
                score += 35
            else:
                issues.append("Engine number missing")

            if vehicle_ok:
                score += 25
            else:
                issues.append("Vehicle number missing")

            # CROSS VALIDATION BOOST
            if chassis_ok and engine_ok and vehicle_ok:
                score += 10

            # OCR confidence boost (smart fix)
            if ocr_conf > 0.8:
                score += 5

        # =====================================================
        # INVOICE (SMART LOGIC)
        # =====================================================
        elif document_type == "INVOICE":

            if entities["dates"]:
                score += 40
            else:
                issues.append("Invoice date missing")

            if entities["vehicle_numbers"]:
                score += 20

            if entities["engine_numbers"]:
                score += 10

            # base reliability
            score += 20

            # OCR confidence adjustment
            score += int(10 * ocr_conf)

        # =====================================================
        # INSURANCE POLICY
        # =====================================================
        elif document_type == "INSURANCE_POLICY":

            if entities["policy_numbers"]:
                score += 60
            else:
                issues.append("Policy number missing")

            if entities["dates"]:
                score += 30

        # =====================================================
        # UNKNOWN
        # =====================================================
        else:
            score = 10
            issues.append("Unknown document")

        # final cap
        score = min(100, score)

        return {
            "verified": score >= 60,
            "verification_score": score,
            "issues": issues
        }