class DocumentClassifier:

    def classify(self, text):

        text = text.lower()

        if (
            "driving" in text
            and (
                "licence" in text
                or "license" in text
                or "lic" in text
            )
        ):
            return "DRIVING_LICENSE"

        if (
            "registration" in text
            or "regisbration" in text
            or "certificate" in text
            or "certifkcate" in text
            or "vehicle registration" in text
        ):
            return "RC_BOOK"

        if (
            "invoice" in text
            or "tax invoice" in text
            or "bill" in text
        ):
            return "INVOICE"

        if (
            "insurance" in text
            and "policy" in text
        ):
            return "INSURANCE_POLICY"

        return "UNKNOWN"