import streamlit as st
import numpy as np

from modules.damage_detector import CarPartDetector, DamageDetector
from modules.ocr_verifier import OCRVerifier
from modules.risk_engine import RiskEngine
from modules.utils import get_iou
from modules.damage_rules import is_damage_valid_for_part

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

age = st.sidebar.number_input(
    "Age",
    min_value=18,
    max_value=100,
    value=30
)

experience = st.sidebar.number_input(
    "Driving Experience (Years)",
    min_value=0,
    max_value=60,
    value=5
)

previous_claims = st.sidebar.number_input(
    "Previous Claims",
    min_value=0,
    max_value=20,
    value=0
)

vehicle_age = st.sidebar.number_input(
    "Vehicle Age (Years)",
    min_value=0,
    max_value=30,
    value=5
)

accidents_last_5_years = st.sidebar.number_input(
    "Accidents (Last 5 Years)",
    min_value=0,
    max_value=20,
    value=0
)

annual_mileage = st.sidebar.number_input(
    "Annual Mileage (km)",
    min_value=0,
    max_value=200000,
    value=15000,
    step=1000
)

commercial_use = st.sidebar.checkbox(
    "Commercial Vehicle Use",
    value=False
)
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
        "previous_claims": previous_claims,
        "vehicle_age": vehicle_age,
        "accidents_last_5_years": accidents_last_5_years,
        "annual_mileage": annual_mileage,
        "commercial_use": commercial_use
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
                best_iou = 0.0

                for dmg in damages:

                    if not is_damage_valid_for_part(
                        part["class_name"],
                        dmg["damage_type"]
                    ):
                        continue

                    iou = get_iou(
                        part["bbox"],
                        dmg["bbox"]
                    )

                    if iou > best_iou:
                        best_iou = iou
                        best_damage = dmg

    #    Require meaningful overlap
                if best_damage and best_iou >= 0.15:

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
                    continue



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