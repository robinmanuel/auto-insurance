import cv2
import numpy as np
from PIL import Image
import base64
from pdf2image import convert_from_path


# -----------------------------
# IMAGE UTILITIES
# -----------------------------

def load_image(image_file):
    """Convert Streamlit uploaded file to OpenCV image"""
    image = Image.open(image_file).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def resize_image(img, width=800):
    h, w = img.shape[:2]
    if w > width:
        ratio = width / w
        img = cv2.resize(img, (width, int(h * ratio)))
    return img


def preprocess_fast(img):
    """Light preprocessing for fast OCR/YOLO"""
    img = resize_image(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray


# -----------------------------
# PDF UTILITIES
# -----------------------------

def pdf_to_images(pdf_file):
    """
    Convert PDF to list of images (FAST mode)
    Requires poppler installed in system
    """
    images = convert_from_path(pdf_file)
    opencv_images = []

    for page in images:
        img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        opencv_images.append(img)

    return opencv_images


# -----------------------------
# YOLO HELPERS
# -----------------------------

def get_iou(box1, box2):
    """
    Intersection over Union (for YOLO fusion)
    box format: [x1, y1, x2, y2]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)

    box1_area = (box1[2]-box1[0]) * (box1[3]-box1[1])
    box2_area = (box2[2]-box2[0]) * (box2[3]-box2[1])

    union = box1_area + box2_area - inter_area

    if union == 0:
        return 0

    return inter_area / union


# -----------------------------
# VISUALIZATION HELPERS
# -----------------------------

def draw_box(img, box, label, color=(0, 255, 0)):
    """Draw bounding box on image"""
    x1, y1, x2, y2 = box

    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        img,
        label,
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2
    )

    return img


# -----------------------------
# STREAMLIT DISPLAY HELPERS
# -----------------------------

def encode_image(img):
    """Convert OpenCV image to base64 for Streamlit display"""
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8')