class DocumentClassifier:

    def classify(self, text):

        if not text:
            return "UNKNOWN"

        t = text.lower()

        scores = {
            "DRIVING_LICENSE": 0,
            "RC_BOOK": 0,
            "INVOICE": 0,
            "INSURANCE_POLICY": 0
        }

        # =====================================================
        # DRIVING LICENSE (STRONG STRUCTURE SIGNAL)
        # =====================================================
        if "driving" in t:
            scores["DRIVING_LICENSE"] += 2

        if any(k in t for k in ["licence", "license", "lic"]):
            scores["DRIVING_LICENSE"] += 2

        # =====================================================
        # RC BOOK (STRICTER + VEHICLE STRUCTURE DEPENDENT)
        # =====================================================
        rc_strong = [
            "registration certificate",
            "rc book",
            "vehicle registration",
            "chassis",
            "engine",
            "rto"
        ]

        rc_weak = [
            "registration",
            "fitness",
            "ownership",
            "vehicle class",
            "regn"
        ]

        for k in rc_strong:
            if k in t:
                scores["RC_BOOK"] += 3

        for k in rc_weak:
            if k in t:
                scores["RC_BOOK"] += 1

        # IMPORTANT DISAMBIGUATION:
        # invoices often contain "vehicle" but NOT chassis/engine patterns
        if "invoice" in t:
            scores["INVOICE"] += 1
            scores["RC_BOOK"] -= 1   # reduce RC bias

        # =====================================================
        # INVOICE (STRUCTURE-BASED, NOT JUST KEYWORDS)
        # =====================================================
        inv_strong = [
            "invoice no",
            "tax invoice",
            "bill to",
            "subtotal",
            "total amount"
        ]

        inv_weak = [
            "invoice",
            "bill",
            "amount",
            "services",
            "tax"
        ]

        for k in inv_strong:
            if k in t:
                scores["INVOICE"] += 3

        for k in inv_weak:
            if k in t:
                scores["INVOICE"] += 1

        # =====================================================
        # INSURANCE POLICY
        # =====================================================
        if "insurance" in t:
            scores["INSURANCE_POLICY"] += 2

        if "policy" in t:
            scores["INSURANCE_POLICY"] += 2

        # =====================================================
        # FINAL DECISION (WITH SAFETY THRESHOLD)
        # =====================================================
        best = max(scores, key=scores.get)

        if scores[best] < 3:
            return "UNKNOWN"

        return best