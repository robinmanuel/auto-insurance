from ultralytics import YOLO
import cv2
import numpy as np


# =========================================================
# BASE DETECTOR (FIXED)
# =========================================================
class BaseDetector:

    def __init__(self, weights):
        # ✅ CORRECT LOADER (NOT torch.load)
        self.model = YOLO(weights)

    def run(self, image_path):
        return self.model.predict(image_path, verbose=False)


# =========================================================
# CAR PART DETECTOR
# =========================================================
class CarPartDetector(BaseDetector):

    def predict(self, image_path):

        results = self.run(image_path)

        parts = []

        for r in results:

            if r.boxes is None:
                continue

            names = r.names

            for box in r.boxes:

                conf = float(box.conf[0])

                if conf < 0.5:
                    continue

                parts.append({
                    "class_id": int(box.cls[0]),
                    "class_name": names[int(box.cls[0])],
                    "confidence": conf,
                    "bbox": box.xyxy[0].tolist()
                })

        return parts


# =========================================================
# DAMAGE DETECTOR
# =========================================================
class DamageDetector(BaseDetector):

    def predict(self, image_path):

        results = self.run(image_path)

        damages = []

        for r in results:

            if r.boxes is None:
                continue

            names = r.names

            for box in r.boxes:

                conf = float(box.conf[0])

                if conf < 0.3:
                    continue

                damages.append({
                    "damage_type": names[int(box.cls[0])],
                    "confidence": conf,
                    "bbox": box.xyxy[0].tolist()
                })

        return damages