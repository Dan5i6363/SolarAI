"""OpenCV panel monitoring with webcam, image, and deterministic demo support."""
from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np


def create_demo_image() -> np.ndarray:
    image = np.full((480, 720, 3), (190, 220, 235), dtype=np.uint8)
    corners = np.array([[145, 100], [565, 70], [620, 365], [105, 395]], dtype=np.int32)
    cv2.fillConvexPoly(image, corners, (65, 55, 35))
    cv2.polylines(image, [corners], True, (225, 225, 225), 4)
    for t in np.linspace(0.2, 0.8, 4):
        a = corners[0] * (1-t) + corners[3] * t; b = corners[1] * (1-t) + corners[2] * t
        cv2.line(image, tuple(a.astype(int)), tuple(b.astype(int)), (180, 160, 110), 1)
    for t in np.linspace(0.2, 0.8, 5):
        a = corners[0] * (1-t) + corners[1] * t; b = corners[3] * (1-t) + corners[2] * t
        cv2.line(image, tuple(a.astype(int)), tuple(b.astype(int)), (180, 160, 110), 1)
    return image


def analyze_panel(image: np.ndarray | None = None, image_path: str | Path | None = None) -> dict:
    """Locate the largest likely panel-like quadrilateral and assess visible brightness.

    This is a heuristic visual aid, not a safety or fault diagnosis system.
    """
    if image is None and image_path is not None: image = cv2.imread(str(image_path))
    if image is None: image = create_demo_image()
    annotated = image.copy(); gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    best = None; image_area = image.shape[0] * image.shape[1]
    for contour in contours:
        perimeter = cv2.arcLength(contour, True); polygon = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        area = cv2.contourArea(polygon)
        if len(polygon) == 4 and area > image_area * 0.04 and (best is None or area > best[0]): best = (area, polygon)
    if best is None:
        return {"panel_detected": False, "visual_condition": "PANEL NOT LOCATED", "message": "No panel-like region detected.", "annotated_image": annotated}
    _, polygon = best; mask = np.zeros(gray.shape, dtype=np.uint8); cv2.fillPoly(mask, [polygon], 255)
    brightness = float(cv2.mean(gray, mask=mask)[0]); visual = "VISUALLY DIM" if brightness < 65 else "PANEL REGION LOCATED"
    cv2.polylines(annotated, [polygon], True, (0, 255, 0), 3)
    cv2.putText(annotated, visual, tuple(polygon[0][0]), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 255, 0), 2)
    return {"panel_detected": True, "visual_condition": visual, "mean_brightness": round(brightness, 1), "message": "Heuristic image analysis only.", "annotated_image": annotated}


def capture_webcam(camera_index: int = 0) -> np.ndarray | None:
    camera = cv2.VideoCapture(camera_index)
    ok, frame = camera.read(); camera.release()
    return frame if ok else None
