import numpy as np


class RiskEngine:

    def __init__(self, config):
        self.config = config

    # =====================================================
    # MAIN ENTRY
    # =====================================================
    def evaluate(self, profile, ocr_result, damage_result):

        profile_risk = self._profile_risk(profile)

        # OCR handled separately
        ocr_risk = 0

        damage_risk = self._damage_risk(
            damage_result.get("risk_score", 0)
        )

        total_score = self._normalize(
            profile_risk +
            damage_risk
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
                "damage_risk": damage_risk
            },
            "reasons": reasons
        }

    # =====================================================
    # PROFILE RISK
    # =====================================================
    def _profile_risk(self, profile):

        age = profile.get("age", 30)
        exp = profile.get("experience", 5)
        claims = profile.get("previous_claims", 0)

        vehicle_age = profile.get(
            "vehicle_age",
            5
        )

        accidents = profile.get(
            "accidents_last_5_years",
            0
        )

        annual_mileage = profile.get(
            "annual_mileage",
            15000
        )

        commercial_use = profile.get(
            "commercial_use",
            False
        )

        years_insured = profile.get(
            "years_insured",
            1
        )

        risk = 0

        # ------------------
        # Driver Age
        # ------------------
        if age < 25:
            risk += 15
        elif age < 40:
            risk += 5

        # ------------------
        # Driving Experience
        # ------------------
        if exp < 2:
            risk += 15
        elif exp < 5:
            risk += 8

        # ------------------
        # Previous Claims
        # ------------------
        risk += min(
            claims * 8,
            25
        )

        # ------------------
        # Accident History
        # ------------------
        risk += min(
            accidents * 8,
            25
        )

        # ------------------
        # Vehicle Age
        # ------------------
        if vehicle_age > 15:
            risk += 10
        elif vehicle_age > 10:
            risk += 5

        # ------------------
        # Mileage
        # ------------------
        if annual_mileage > 50000:
            risk += 10
        elif annual_mileage > 25000:
            risk += 5

        # ------------------
        # Commercial Usage
        # ------------------
        if commercial_use:
            risk += 10

        # ------------------
        # Insurance History
        # ------------------
        if years_insured < 1:
            risk += 10
        elif years_insured < 3:
            risk += 5

        return risk

    # =====================================================
    # DAMAGE COST -> RISK
    # =====================================================
    def _damage_risk(self, claim_cost):

        if claim_cost <= 0:
            return 0

        elif claim_cost < 10000:
            return 5

        elif claim_cost < 25000:
            return 15

        elif claim_cost < 50000:
            return 30

        elif claim_cost < 100000:
            return 45

        else:
            return 60

    # =====================================================
    # NORMALIZATION
    # =====================================================
    def _normalize(self, score):

        return float(
            min(
                100,
                max(
                    0,
                    score
                )
            )
        )

    # =====================================================
    # DECISION ENGINE
    # =====================================================
    def _decide(
        self,
        score,
        ocr,
        damage,
        profile
    ):

        reasons = []

        docs = ocr.get("documents", [])

        claim_cost = damage.get(
            "risk_score",
            0
        )

        age = profile.get("age", 30)
        experience = profile.get("experience", 5)
        claims = profile.get("previous_claims", 0)
        accidents = profile.get(
            "accidents_last_5_years",
            0
        )

        commercial = profile.get(
            "commercial_use",
            False
        )

        # ==================================
        # OCR / DOCUMENTS
        # ==================================

        verified_docs = sum(
            1 for d in docs
            if d.get("verified", False)
        )

        total_docs = len(docs)

        if total_docs > 0:

            if verified_docs == total_docs:
                reasons.append(
                    "All uploaded documents verified successfully"
                )

            elif verified_docs > 0:
                reasons.append(
                    "Some documents require manual verification"
                )

            else:
                reasons.append(
                    "Document verification failed"
                )

        # ==================================
        # DAMAGE
        # ==================================

        if claim_cost == 0:

            reasons.append(
                "No valid vehicle damage detected"
            )

        elif claim_cost < 15000:

            reasons.append(
                "Low repair cost estimate"
            )

        elif claim_cost < 50000:

            reasons.append(
                "Moderate repair cost estimate"
            )

        else:

            reasons.append(
                "High repair cost estimate"
            )

        # ==================================
        # DRIVER PROFILE
        # ==================================

        if age < 25:

            reasons.append(
                "Young driver risk"
            )

        elif age > 60:

            reasons.append(
                "Senior driver profile"
            )

        else:

            reasons.append(
                "Standard driver age profile"
            )

        if experience < 2:

            reasons.append(
                "Limited driving experience"
            )

        elif experience >= 5:

            reasons.append(
                "Experienced driver"
            )

        if claims == 0:

            reasons.append(
                "No previous claims history"
            )

        elif claims <= 2:

            reasons.append(
                "Previous claims detected"
            )

        else:

            reasons.append(
                "Multiple previous claims"
            )

        if accidents == 0:

            reasons.append(
                "No recent accident history"
            )

        elif accidents <= 2:

            reasons.append(
                "Recent accidents reported"
            )

        else:

            reasons.append(
                "Multiple recent accidents"
            )

        if commercial:

            reasons.append(
                "Commercial vehicle usage"
            )

        # ==================================
        # DECISION
        # ==================================

        if score <= 35:

            decision = "APPROVE"

        elif score <= 65:

            decision = "MANUAL_REVIEW"

        else:

            decision = "REJECT"

        return decision, reasons