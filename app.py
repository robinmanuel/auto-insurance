import streamlit as st
import numpy as np

from modules.damage_detector import CarPartDetector, DamageDetector
from modules.ocr_verifier import OCRVerifier
from modules.risk_engine import RiskEngine


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Auto Insurance Auto-Approval System", layout="wide")
st.title("SmartClaim AI 🚗")


# =========================================================
# LOAD SYSTEM
# =========================================================
@st.cache_resource
def load_system():

    part_model = "models/parts_segmentation.pt"
    damage_model = "models/trained.pt"

    part_detector = CarPartDetector(part_model)
    damage_detector = DamageDetector(damage_model)

    ocr = OCRVerifier()
    risk_engine = RiskEngine(config=None)

    return part_detector, damage_detector, ocr, risk_engine


part_detector, damage_detector, ocr_engine, risk_engine = load_system()


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.header("Customer Profile")

age = st.sidebar.number_input("Age", 18, 100, 30)
experience = st.sidebar.number_input("Driving Experience", 0, 60, 5)
previous_claims = st.sidebar.number_input("Previous Claims", 0, 20, 0)


st.sidebar.header("Upload Documents")

doc_files = st.sidebar.file_uploader(
    "Upload License / RC (multiple allowed)",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)


st.sidebar.header("Upload Vehicle Images")

vehicle_images = st.sidebar.file_uploader(
    "Upload Vehicle Images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)


run = st.sidebar.button("Run Auto-Approval")


# =========================================================
# PIPELINE
# =========================================================
if run:

    if not doc_files or not vehicle_images:
        st.error("Please upload documents and vehicle images")
        st.stop()

    profile = {
        "age": age,
        "experience": experience,
        "previous_claims": previous_claims
    }

    # =====================================================
    # OCR (FIXED: pass UploadedFile directly)
    # =====================================================
    with st.spinner("Running OCR..."):

        ocr_results = []
        for doc in doc_files:
            ocr_results.append(ocr_engine.process(doc))

        ocr_result = {
            "documents": ocr_results
        }

    # =====================================================
    # DAMAGE DETECTION
    # =====================================================
    all_results = []
    total_cost = 0

    with st.spinner("Analyzing vehicle images..."):

        import tempfile

        for img in vehicle_images:

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(img.read())
                img_path = tmp.name

            parts = part_detector.predict(img_path)
            damages = damage_detector.predict(img_path)

            for part in parts:

                best_damage = None
                best_iou = 0

                for dmg in damages:

                    x1 = max(part["bbox"][0], dmg["bbox"][0])
                    y1 = max(part["bbox"][1], dmg["bbox"][1])
                    x2 = min(part["bbox"][2], dmg["bbox"][2])
                    y2 = min(part["bbox"][3], dmg["bbox"][3])

                    inter = max(0, x2 - x1) * max(0, y2 - y1)

                    if inter > best_iou:
                        best_iou = inter
                        best_damage = dmg

                if best_damage and best_iou > 0:

                    damage_type = best_damage["damage_type"]
                    damage_conf = best_damage["confidence"]

                    cost_map = {
                        "scratch": 2500,
                        "dent": 4000,
                        "crack": 6000,
                        "broken_lamp": 7000,
                        "flat_tire": 5000,
                        "shattered_glass": 15000
                    }

                    cost = cost_map.get(damage_type, 0)

                else:
                    damage_type = "no_damage"
                    damage_conf = 0
                    cost = 0

                total_cost += cost

                all_results.append({
                    "part": part["class_name"],
                    "confidence": part["confidence"],
                    "damage": damage_type,
                    "damage_confidence": damage_conf,
                    "estimated_cost": cost
                })

    damage_result = {
        "risk_score": float(total_cost),
        "details": all_results
    }

    # =====================================================
    # RISK ENGINE
    # =====================================================
    with st.spinner("Calculating risk..."):

        final_result = risk_engine.evaluate(
            profile,
            ocr_result,
            damage_result
        )

    # =====================================================
    # OUTPUT
    # =====================================================
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Risk Score", final_result.get("risk_score", 0))

    with col2:
        decision = final_result.get("decision", "MANUAL_REVIEW")

        if decision == "APPROVE":
            st.success("APPROVED")
        elif decision == "MANUAL_REVIEW":
            st.warning("MANUAL REVIEW")
        else:
            st.error("REJECTED")

    with col3:
        st.metric("Estimated Claim Cost", damage_result["risk_score"])

    st.divider()
    st.subheader("📄 OCR Results")
    st.json(ocr_result)

    st.divider()
    st.subheader("🚗 Damage Details")
    st.json(damage_result["details"])

    st.divider()
    st.subheader("📌 Reasons")

    for r in final_result.get("reasons", []):
        st.write("•", r)