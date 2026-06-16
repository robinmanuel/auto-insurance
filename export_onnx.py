from ultralytics import YOLO

# -----------------------------
# CONFIG
# -----------------------------
PART_MODEL_PATH = "models/parts_segmentation.pt"
DAMAGE_MODEL_PATH = "models/trained.pt"

# -----------------------------
# EXPORT FUNCTION
# -----------------------------
def export_model(pt_path):
    print(f"Exporting: {pt_path}")

    model = YOLO(pt_path)

    model.export(
        format="onnx",
        opset=12,
        simplify=True,
        imgsz=640
    )

    print(f"Done: {pt_path}")

# -----------------------------
# RUN EXPORTS
# -----------------------------
if __name__ == "__main__":
    export_model(PART_MODEL_PATH)
    export_model(DAMAGE_MODEL_PATH)

    print("\n✅ All models exported to ONNX successfully")