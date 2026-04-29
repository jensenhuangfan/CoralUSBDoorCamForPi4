#!/usr/bin/env python3
"""Coral USB + Raspberry Pi 4 face identification pipeline.

Detection is accelerated on the Coral Edge TPU.
Identity matching is done locally with OpenCV LBPH trained from known_faces/<person>/* images.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
from PIL import Image
from pycoral.adapters import common, detect
from pycoral.utils.edgetpu import make_interpreter

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class SpeechEngine:
    """Handles TTS with separate cooldowns for intruder alerts and welcomes."""

    def __init__(self, intruder_cooldown: float = 3.0, welcome_cooldown: float = 8.0) -> None:
        self.intruder_cooldown = intruder_cooldown
        self.welcome_cooldown = welcome_cooldown
        self.last_intruder_alert_time = 0.0
        self.last_welcome_time: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.engine = None

        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 150)
            except Exception as e:
                print(f"[Warn] TTS init failed: {e}")
                self.engine = None

    def speak(self, text: str) -> None:
        """Speak text in background thread."""
        
        # Make a direct system call to espeak which is often more reliable
        # than initializing pyttsx3 repeatedly across multithreading boundaries.
        def _speak_bg() -> None:
            with self.lock:
                try:
                    subprocess.run(["espeak", "-s", "150", text], check=False)
                except Exception as e:
                    print(f"Audio Error: {e}")

        thread = threading.Thread(target=_speak_bg, daemon=True)
        thread.start()

    def alert_intruder(self) -> None:
        """Alert intruder, respecting cooldown."""
        now = time.time()
        if now - self.last_intruder_alert_time >= self.intruder_cooldown:
            self.last_intruder_alert_time = now
            self.speak("Intruder alert. Intruder alert.")

    def welcome_person(self, name: str) -> None:
        """Welcome person by name, respecting per-person cooldown."""
        now = time.time()
        last_time = self.last_welcome_time.get(name, 0.0)
        if now - last_time >= self.welcome_cooldown:
            self.last_welcome_time[name] = now
            self.speak(f"Welcome {name}")


@dataclass
class DetectionResult:
    bbox: Tuple[int, int, int, int]
    score: float


class CoralFaceDetector:
    def __init__(self, model_path: Path, threshold: float = 0.45) -> None:
        self.model_path = model_path
        self.threshold = threshold
        self.interpreter = None
        self.input_w = None
        self.input_h = None
        self.use_coral = False

        if model_path.exists():
            try:
                self.interpreter = make_interpreter(str(model_path))
                self.interpreter.allocate_tensors()
                self.input_w, self.input_h = common.input_size(self.interpreter)
                self.use_coral = True
                print("[Init] Coral Edge TPU strictly required, detected and loaded")
            except Exception as e:
                raise RuntimeError(f"CRITICAL ERROR: Coral Edge TPU failed to load: {e}")
        else:
            raise RuntimeError(f"CRITICAL ERROR: Coral model not found at: {model_path}")

    def detect_faces(self, frame_bgr: np.ndarray) -> List[DetectionResult]:
        if not self.use_coral or self.interpreter is None:
            return []

        frame_h, frame_w = frame_bgr.shape[:2]

        # Coral Edge TPU path
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Fast cross-version PIL compatibility for resizing
        try:
            resample_filter = Image.Resampling.BILINEAR
        except AttributeError:
            resample_filter = Image.BILINEAR
            
        pil_img = Image.fromarray(frame_rgb).resize(
            (self.input_w, self.input_h), resample_filter
        )
        common.set_input(self.interpreter, pil_img)
        self.interpreter.invoke()

        objs = detect.get_objects(self.interpreter, score_threshold=self.threshold)

        scale_x = frame_w / self.input_w
        scale_y = frame_h / self.input_h

        results: List[DetectionResult] = []
        for obj in objs:
            x1 = int(max(0, min(frame_w - 1, obj.bbox.xmin * scale_x)))
            y1 = int(max(0, min(frame_h - 1, obj.bbox.ymin * scale_y)))
            x2 = int(max(0, min(frame_w - 1, obj.bbox.xmax * scale_x)))
            y2 = int(max(0, min(frame_h - 1, obj.bbox.ymax * scale_y)))

            if x2 <= x1 or y2 <= y1:
                continue

            results.append(DetectionResult((x1, y1, x2, y2), float(obj.score)))
        return results


    def detect_largest_face(self, frame_bgr: np.ndarray) -> Optional[DetectionResult]:
        detections = self.detect_faces(frame_bgr)
        if not detections:
            return None

        return max(
            detections,
            key=lambda d: (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]),
        )


def preprocess_face(frame_bgr: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    x1, y1, x2, y2 = bbox

    # Add margin so crops are less sensitive to minor detector drift.
    w = x2 - x1
    h = y2 - y1
    mx = int(w * 0.15)
    my = int(h * 0.2)

    x1 = max(0, x1 - mx)
    y1 = max(0, y1 - my)
    x2 = min(frame_bgr.shape[1] - 1, x2 + mx)
    y2 = min(frame_bgr.shape[0] - 1, y2 + my)

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return cv2.resize(gray, (160, 160), interpolation=cv2.INTER_AREA)


class FaceDatabase:
    def __init__(self, unknown_threshold: float = 70.0) -> None:
        if not hasattr(cv2, "face"):
            raise RuntimeError(
                "OpenCV contrib modules are missing (cv2.face not available). "
                "Install python3-opencv from apt on Raspberry Pi OS."
            )

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.unknown_threshold = unknown_threshold
        self.label_to_name: Dict[int, str] = {}
        self.is_trained = False

    def train(self, known_faces_dir: Path, detector: CoralFaceDetector) -> None:
        if not known_faces_dir.exists():
            raise FileNotFoundError(f"Photo database not found: {known_faces_dir}")

        samples: List[np.ndarray] = []
        labels: List[int] = []

        person_dirs = sorted([p for p in known_faces_dir.iterdir() if p.is_dir()])
        if not person_dirs:
            raise RuntimeError("No person folders found in known_faces directory.")

        for label, person_dir in enumerate(person_dirs):
            self.label_to_name[label] = person_dir.name

            image_paths = sorted(
                [
                    p
                    for p in person_dir.rglob("*")
                    if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
                ]
            )

            accepted = 0
            for image_path in image_paths:
                img = cv2.imread(str(image_path))
                if img is None:
                    continue

                detection = detector.detect_largest_face(img)
                if detection is None:
                    continue

                processed = preprocess_face(img, detection.bbox)
                if processed is None:
                    continue

                samples.append(processed)
                labels.append(label)
                accepted += 1

            print(f"[DB] {person_dir.name}: accepted {accepted}/{len(image_paths)} images")

        if len(samples) < 2:
            raise RuntimeError(
                "Not enough trainable face samples found. "
                "Check that person photos are clear and face-forward."
            )

        self.recognizer.train(samples, np.array(labels, dtype=np.int32))
        self.is_trained = True
        print(f"[DB] Training complete: {len(samples)} samples across {len(person_dirs)} identities")

    def predict(self, face_crop: np.ndarray) -> Tuple[str, float]:
        if not self.is_trained:
            return "Unknown", 999.0

        label, confidence = self.recognizer.predict(face_crop)
        confidence = float(confidence)
        if confidence <= self.unknown_threshold and label in self.label_to_name:
            return self.label_to_name[label], confidence

        return "Unknown", confidence


def draw_result(
    frame: np.ndarray,
    bbox: Tuple[int, int, int, int],
    name: str,
    score: float,
    confidence: float,
) -> None:
    x1, y1, x2, y2 = bbox
    known = name != "Unknown"

    color = (0, 200, 0) if known else (0, 0, 255)
    label = (
        f"{name} | det:{score:.2f} rec:{confidence:.1f}"
        if known
        else f"Unknown | det:{score:.2f} rec:{confidence:.1f}"
    )

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.rectangle(frame, (x1, max(0, y1 - 24)), (x2, y1), color, -1)
    cv2.putText(
        frame,
        label,
        (x1 + 4, max(12, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Face gate built for Coral USB Accelerator + Raspberry Pi 4"
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument(
        "--picam3",
        action="store_true",
        help="Use Pi Camera 3 (libcamera/GStreamer) instead of a standard USB webcam",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite"),
        help="Path to Edge TPU face detection model",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("known_faces"),
        help="Path to known faces directory",
    )
    parser.add_argument(
        "--det-threshold",
        type=float,
        default=0.45,
        help="Detection score threshold",
    )
    parser.add_argument(
        "--unknown-threshold",
        type=float,
        default=115.0,
        help="LBPH threshold, lower is stricter (try 90-120)",
    )
    parser.add_argument(
        "--detect-every",
        type=int,
        default=2,
        help="Run Edge TPU detection every N frames",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("[Init] Loading Coral model...")
    detector = CoralFaceDetector(args.model, threshold=args.det_threshold)

    print("[Init] Building face database from photos...")
    face_db = FaceDatabase(unknown_threshold=args.unknown_threshold)
    face_db.train(args.database, detector)

    print("[Init] Initializing speech engine...")
    speech = SpeechEngine(intruder_cooldown=3.0, welcome_cooldown=8.0)

    if args.picam3:
        print("[Init] Connecting to Raspberry Pi Camera 3 via libcamera...")
        # GStreamer pipeline for libcamera module (Pi Cam 3)
        pipeline = (
            "libcamerasrc ! "
            "video/x-raw, width=1280, height=720, framerate=30/1 ! "
            "videoconvert ! appsink"
        )
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    else:
        print(f"[Init] Connecting to USB Camera index {args.camera}...")
        # Use explicit V4L2 for better Pi compatibility, fallback to default
        cap = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print("[Error] Camera could not be opened.")
        return 1

    if not args.picam3:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[Run] Press Q to quit.")
    frame_idx = 0
    cached_detections: List[DetectionResult] = []
    last_known_faces: Set[str] = set()

    # Setup fullscreen window
    cv2.namedWindow("Coral Face Gate", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Coral Face Gate", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Allow double-clicking anywhere to exit
    quit_flag = [False]
    def on_mouse_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDBLCLK:
            quit_flag[0] = True
            
    cv2.setMouseCallback("Coral Face Gate", on_mouse_click)

    try:
        while not quit_flag[0]:
            ok, frame = cap.read()
            if not ok:
                print("[Warn] Camera frame read failed.")
                break

            frame_idx += 1
            if frame_idx % max(1, args.detect_every) == 0:
                cached_detections = detector.detect_faces(frame)

            known_faces_this_frame: Set[str] = set()
            has_unknown = False

            for detection in cached_detections:
                processed = preprocess_face(frame, detection.bbox)
                if processed is None:
                    continue

                name, confidence = face_db.predict(processed)
                draw_result(frame, detection.bbox, name, detection.score, confidence)

                if name == "Unknown":
                    has_unknown = True
                else:
                    known_faces_this_frame.add(name)

            # Trigger audio alerts
            if has_unknown:
                speech.alert_intruder()

            # Welcome new known faces (not seen in previous frame)
            for name in known_faces_this_frame:
                if name not in last_known_faces:
                    speech.welcome_person(name)

            last_known_faces = known_faces_this_frame

            fps_text = f"Faces: {len(cached_detections)} | DBL-CLICK TO EXIT"
            cv2.putText(
                frame,
                fps_text,
                (12, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # Scale the frame matrix itself up to standard 1080p (1920x1080) to fix the Raspberry Pi 
            # Wayland/X11 rendering bug where the frame gets stuck in the corner of a white screen.
            display_frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
            
            cv2.imshow("Coral Face Gate", display_frame)
            key = cv2.waitKey(1) & 0xFF
            if key in [ord("q"), 27]:  # 27 is ESC key
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
