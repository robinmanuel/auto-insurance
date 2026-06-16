class ContextValidator:

    def __init__(self):
        pass

    def validate(self, document_type, entities, raw_text):
        """
        Adds consistency + sanity checks after OCR + extraction
        """

        issues = []
        score_boost = 0

        text = raw_text.lower()

        # -----------------------------
        # Global sanity checks
        # -----------------------------
        if len(text.strip()) < 20:
            issues.append("Very low text content")
            return {"issues": issues, "score_boost": -50}

        # -----------------------------
        # Document-type consistency
        # -----------------------------
        if document_type == "DRIVING_LICENSE":

            if "driving" not in text:
                issues.append("Document mismatch: not a DL")

            if entities["license_numbers"]:
                score_boost += 10

        elif document_type == "RC_BOOK":

            if "registration" not in text and "rc" not in text:
                issues.append("Document mismatch: not RC")

            if entities["chassis_numbers"]:
                score_boost += 10

        elif document_type == "INVOICE":

            if "invoice" not in text:
                issues.append("Document mismatch: not invoice")

            if entities["dates"]:
                score_boost += 5

        # -----------------------------
        # Noise penalty
        # -----------------------------
        noise_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)

        if noise_ratio < 0.5:
            issues.append("High OCR noise detected")
            score_boost -= 10

        return {
            "issues": issues,
            "score_boost": score_boost
        }