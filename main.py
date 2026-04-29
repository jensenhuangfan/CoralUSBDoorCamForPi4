import sys
import threading
import time
import subprocess
import argparse
import os
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set

import cv2
import numpy as np
from PIL import Image

try:
    import tflite_runtime.interpreter as tflite
    from pycoral.utils import edgetpu
    from pycoral.adapters import common, detect
except ImportError:
    print("[Error] pycoral or tflite_runtime not installed.")
    sys.exit(1)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}

with open("config.json", "r") as f:
    CONFIG = json.load(f)

def get_display_resolution() -> Tuple[int, int]:
    try:
        out = subprocess.check_output("xrandr | grep '\*' | head -n 1", shell=True).decode()
        res = out.strip().split()[0]
        w, h = map(int, res.split('x'))
        return w, h
    except Exception:
        return 1920, 1080

class SpeechEngine:
    def __init__(self, intruder_cooldown: float = 3.0, welcome_cooldown: float = 8.0) -> None:
        self.intruder_cooldown = intruder_cooldown
        self.welcome_cooldown = welcome_cooldown
        self.last_intruder_alert_time = 0.0
        self.last_welcome_time: Dict[str, float] = {}
        self.lock = threading.Lock()

    def speak(self, text: str) -> None:
        def _speak_bg() -> None:
            with self.lock:
                try:
                    subprocess.run(["espeak", "-s", "150", text], check=False)
                except Exception as e:
                    print(f"Audio Error: {e}")

        thread = threading.Thread(target=_speak_bg, daemon=True)
        thread.start()

    def alert_intruder(self) -> None:
        now = time.time()
        if now - self.last_intruder_alert_time >= self.intruder_cooldown:
            self.last_intruder_alert_time = now
            self.speak(CONFIG.get("unknown_label", "Intruder") + " alert.")

    def process_person(self, name: str, list_type: str) -> None:
        now = time.time()
        last_time = self.last_welcome_time.get(name, 0.0)
        if now - last_time >= self.welcome_cooldown:
            self.last_welcome_time[name] = now
            
            if list_type == "whitelist":
                self.speak(CONFIG["whitelist_greeting"].replace("{name}", name))
            elif list_type == "blacklist":
                self.speak(CONFIG["blacklist_greeting"].replace("{name}", name))
            else:
                self.speak(CONFIG["default_known_greeting"].replace("{name}", name))

@dataclass
class DetectionResult:
    bbox: Tuple[int, int, int, int]
    score: float

class CoralFaceDetector:
    def __init__(self, model_path: Path, threshold: float = 0.45) -> None:
        self.threshold = threshold
        if not model_path.exists():
            raise RuntimeError(f"CRITICAL: Coral model missing at {model_path}")
        
        self.interpreter = edgetpu.make_interpreter(str(model_path))
        self.interpreter.allocate_tensors()
        self.input_w, self.input_h = common.input_size(self.interpreter)
        self.use_coral = True
        print("[Init] Coral Edge TPU detected and locked")

    def detect_faces(self, frame_bgr: np.ndarray) -> List[DetectionResult]:
        frame_h, frame_w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        try:
            resample_filter = Image.Resampling.BILINEAR
        except AttributeError:
            resample_filter = Image.BILINEAR
            
        pil_img = Image.fromarray(frame_rgb).resize((self.input_w, self.input_h), resample_filter)
        common.set_input(self.interpreter, pil_img)
        self.interpreter.invoke()

        objs = detect.get_objects(self.interpreter, score_threshold=self.threshold)
        scale_x = frame_w / self.input_w
        scale_y = frame_h / self.input_h

        results = []
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
        return max(detections, key=lambda d: (d.bbox[2] - d.bbox[0]) * (d.bbox[3] - d.bbox[1]))

def preprocess_face(frame_bgr: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    mx, my = int(w * 0.15), int(h * 0.2)
    x1, y1 = max(0, x1 - mx), max(0, y1 - my)
    x2, y2 = min(frame_bgr.shape[1] - 1, x2 + mx), min(frame_bgr.shape[0] - 1, y2 + my)
    
    if x2 <= x1 or y2 <= y1: return None
    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0: return None
    
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return cv2.resize(cv2.equalizeHist(gray), (160, 160), interpolation=cv2.INTER_AREA)

class FaceDatabase:
    def __init__(self, unknown_threshold: float = 115.0) -> None:
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.unknown_threshold = unknown_threshold
        self.label_to_name: Dict[int, str] = {}
        self.label_to_type: Dict[int, str] = {}
        self.is_trained = False

    def train(self, directories: List[Path], detector: CoralFaceDetector) -> None:
        samples, labels = [], []
        current_label = 0
        
        for directory in directories:
            if not directory.exists(): continue
            list_type = directory.name # 'whitelist' or 'blacklist'
            
            for person_dir in sorted([p for p in directory.iterdir() if p.is_dir()]):
                self.label_to_name[current_label] = person_dir.name
                self.label_to_type[current_label] = list_type
                
                for image_path in person_dir.rglob("*"):
                    if image_path.is_file() and image_path.suffix.lower() in IMAGE_SUFFIXES:
                        img = cv2.imread(str(image_path))
                        if img is None: continue
                        detection = detector.detect_largest_face(img)
                        if detection:
                            processed = preprocess_face(img, detection.bbox)
                            if processed is not None:
                                samples.append(processed)
                                labels.append(current_label)
                current_label += 1
                
        if len(samples) > 1:
            self.recognizer.train(samples, np.array(labels, dtype=np.int32))
            self.is_trained = True

    def predict(self, face_crop: np.ndarray) -> Tuple[str, float, str]:
        if not self.is_trained:
            return CONFIG.get("unknown_label", "Intruder"), 999.0, "unknown"
        label, confidence = self.recognizer.predict(face_crop)
        if confidence <= self.unknown_threshold and label in self.label_to_name:
            return self.label_to_name[label], float(confidence), self.label_to_type[label]
        return CONFIG.get("unknown_label", "Intruder"), float(confidence), "unknown"

def draw_result(frame: np.ndarray, bbox: Tuple[int, int, int, int], name: str, score: float, conf: float) -> None:
    x1, y1, x2, y2 = bbox
    known = name != CONFIG.get("unknown_label", "Intruder")
    color = (0, 200, 0) if known else (0, 0, 255)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.rectangle(frame, (x1, max(0, y1 - 24)), (x2, y1), color, -1)
    cv2.putText(frame, f"{name}", (x1 + 4, max(12, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--usbcam", action="store_true")
    args, _ = parser.parse_known_args()

    detector = CoralFaceDetector(Path("models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite"))
    face_db = FaceDatabase()
    
    train_dirs = [Path("whitelist")]
    if CONFIG.get("has_blacklist"):
        train_dirs.append(Path("blacklist"))
    face_db.train(train_dirs, detector)
    
    speech = SpeechEngine(intruder_cooldown=3.0, welcome_cooldown=8.0)

    use_usbcam = args.usbcam or (CONFIG.get("camera_type") == "usbcam")
    if use_usbcam:
        print(f"[Init] Connecting to USB Camera index {args.camera}...")
        cap = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
    else:
        print("[Init] Connecting to Raspberry Pi Camera 3 via libcamera...")
        cap = cv2.VideoCapture("libcamerasrc ! video/x-raw, width=1280, height=720, framerate=30/1 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)

    cv2.namedWindow("Coral Face Gate", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.setWindowProperty("Coral Face Gate", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    screen_w, screen_h = get_display_resolution()
    print(f"[Init] Forcing custom fullscreen rendering at {screen_w}x{screen_h}")

    key_buffer = ""
    alarm_mode = False
    
    frame_idx = 0
    cached_detections = []
    last_known_faces = set()

    try:
        while True:
            ok, frame = cap.read()
            if not ok: break

            frame_idx += 1
            if frame_idx % 2 == 0:
                cached_detections = detector.detect_faces(frame)

            known_faces_this_frame = set()
            known_faces_types = {}
            has_unknown = False

            for detection in cached_detections:
                processed = preprocess_face(frame, detection.bbox)
                if processed is None: continue

                name, confidence, list_type = face_db.predict(processed)
                draw_result(frame, detection.bbox, name, detection.score, confidence)

                if name == CONFIG.get("unknown_label", "Intruder"):
                    has_unknown = True
                else:
                    known_faces_this_frame.add(name)
                    known_faces_types[name] = list_type

            if has_unknown:
                speech.alert_intruder()
            
            for name in known_faces_this_frame:
                if name not in last_known_faces:
                    speech.process_person(name, known_faces_types[name])

            last_known_faces = known_faces_this_frame

            if alarm_mode:
                if has_unknown or len(cached_detections) > 0:
                    os.system("amixer sset Master 100% 2>/dev/null")
                    speech.speak("Alert Alert")
                else:
                    alarm_mode = False

            display_frame = cv2.resize(frame, (screen_w, screen_h), interpolation=cv2.INTER_LINEAR)
            cv2.imshow("Coral Face Gate", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                if key in [10, 13]: 
                    if hashlib.sha256(key_buffer.encode()).hexdigest() == CONFIG.get("password_hash"):
                        break
                    else:
                        alarm_mode = True
                        key_buffer = ""
                elif key == 8 and len(key_buffer) > 0:
                    key_buffer = key_buffer[:-1]
                else:
                    key_buffer += chr(key)

    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0

if __name__ == "__main__":
    main()
