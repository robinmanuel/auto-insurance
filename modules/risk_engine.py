import numpy as np


class RiskEngine:
    def __init__(self, config):
        self.config = config

    # -----------------------------
    # MAIN ENTRY
    # -----------------------------
    def evaluate(self, profile, ocr_result, damage_result):
        """
        profile = age, experience, claims
        ocr_result = OCRVerifier output
        damage_result = DamageDetector output
        """

        profile_risk = self._profile_risk(profile)
        ocr_risk = ocr_result.get("risk_penalty", 0)
        damage_risk = damage_result.get("risk_score", 0)

        total_score = self._normalize(
            profile_risk + ocr_risk + damage_risk
        )

        decision, reasons = self._decide(
            total_score,
            ocr_result,
            damage_result,
            profile
        )

        return {
            "risk_score": total_score,
            "decision": decision,
            "breakdown": {
                "profile_risk": profile_risk,
                "ocr_risk": ocr_risk,
                "damage_risk": damage_risk
            },
            "reasons": reasons
        }

    # -----------------------------
    # PROFILE RISK (CUSTOMER)
    # -----------------------------
    def _profile_risk(self, profile):
        age = profile.get("age", 30)
        exp = profile.get("experience", 5)
        claims = profile.get("previous_claims", 0)

        risk = 0

        # Age risk
        if age < 25:
            risk += 25
        elif age < 40:
            risk += 10
        else:
            risk += 5

        # Experience risk
        if exp < 2:
            risk += 25
        elif exp < 5:
            risk += 10
        else:
            risk += 5

        # Claims history
        risk += claims * 15

        return risk

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    def _normalize(self, score):
        return float(min(100, max(0, score)))

    # -----------------------------
    # DECISION ENGINE
    # -----------------------------
    def _decide(self, score, ocr, damage, profile):
        reasons = []

        # OCR reasons
        if ocr.get("validation", {}).get("missing_fields"):
            reasons.append("Missing required document fields")

        if ocr.get("validation", {}).get("low_confidence"):
            reasons.append("Low OCR confidence detected")

        # Damage reasons
        fused = damage.get("fused_results", [])
        for d in fused:
            if d["severity"] >= 80:
                reasons.append(f"Severe damage detected: {d['damage']} on {d['part']}")
            elif d["severity"] >= 50:
                reasons.append(f"Moderate damage detected: {d['damage']}")

        # Profile reasons
        if profile.get("age", 0) < 25:
            reasons.append("High-risk age group (<25)")

        if profile.get("experience", 10) < 2:
            reasons.append("Low driving experience")

        # Decision thresholds (realistic insurance logic)
        if score <= 35:
            decision = "APPROVE"
        elif score <= 65:
            decision = "MANUAL_REVIEW"
        else:
            decision = "REJECT"

        return decision, reasons