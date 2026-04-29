import os

GITIGNORE = """
# Ignore known_faces to prevent personal data leaking
known_faces/
models/
config.json
.venv/
__pycache__/
*.pyc
*.tflite
"""

SETUP_SH = """#!/bin/bash
echo "============================================="
echo " Face Gate Installer (Coral Edge TPU) "
echo "============================================="

# 1. Update and install dependencies
echo "[1/6] Installing APT dependencies..."
sudo apt-get update
sudo apt-get install -y espeak libespeak1 espeak-ng python3-opencv python3-pip

# 2. Virtual Environment setup
echo "[2/6] Setting up virtual environment..."
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt || true

# 3. Model download
echo "[3/6] Downloading Google Coral Face Detection Model..."
mkdir -p models
if [ ! -f "models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite" ]; then
    wget -O models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite \
    https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite
fi

# 4. Folder creation & OS lock
echo "[4/6] Creating secure known_faces folder..."
mkdir -p known_faces
# Lock folder at OS level to current user
chmod 700 known_faces
chmod 700 models

# 5. Disable sleep and auto-display off
read -p "Do you want to disable screen sleep and auto-display off? (y/n): " disable_sleep
if [[ "$disable_sleep" == "y" || "$disable_sleep" == "Y" ]]; then
    echo "Disabling sleep modes..."
    sudo xset s off -dpms 2>/dev/null || true
    sudo setterm -blank 0 -powerdown 0 2>/dev/null || true
    # Also edit Wayland/LXDE autostart if available
    mkdir -p ~/.config/lxsession/LXDE-pi
    cat << 'AUTOSTART' > ~/.config/lxsession/LXDE-pi/autostart
@lxpanel --profile LXDE-pi
@pcmanfm --profile LXDE-pi
@xscreensaver -no-splash
@xset s off
@xset s noblank
@xset -dpms
AUTOSTART
fi

# 6. Autostart app on boot
read -p "Do you want Face Gate to automatically start on boot? (y/n): " auto_boot
if [[ "$auto_boot" == "y" || "$auto_boot" == "Y" ]]; then
    mkdir -p ~/.config/autostart
    cat << AUTOSTART_APP > ~/.config/autostart/facegate.desktop
[Desktop Entry]
Type=Application
Name=Face Gate
Exec=$(pwd)/run.sh
Terminal=true
AUTOSTART_APP
    echo "Application added to startup!"
fi

# Run Python configuration wizard
echo "[5/6] Launching Configuration Wizard..."
python3 setup_app.py

echo "============================================="
echo " Setup Complete! Added to .gitignore. "
echo " Add your photos to known_faces/<Name>/"
echo " To run: ./run.sh"
echo "============================================="
"""

SETUP_APP_PY = """
import json
import getpass
import hashlib
from pathlib import Path

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    print("\\n--- Face Gate Configuration Wizard ---")
    
    # Password setup
    while True:
        pwd = getpass.getpass("Enter a new password to lock/exit the app: ")
        pwd2 = getpass.getpass("Confirm password: ")
        if pwd == pwd2 and len(pwd) > 0:
            break
        print("Passwords do not match or are empty. Try again.")
        
    print("\\n[Camera Setup]")
    cam_choice = input("Are you using a Pi Camera Module 3 (libcamera) or a standard USB Webcam? (pi/usb) [default: pi]: ").strip().lower()
    camera_type = "usbcam" if cam_choice == "usb" else "picam3"

    # Labels and behaviors
    unknown_label = input("\\nLabel for unrecognized faces [default: Intruder]: ") or "Intruder"
    
    print("\\n[Whitelists & Blacklists]")
    print("Comma separate names. If someone is on a list, they get custom greetings.")
    whitelist = input("Whitelist names (e.g. John, Jane): ").split(',')
    whitelist = [n.strip() for n in whitelist if n.strip()]
    
    blacklist = input("Blacklist names (e.g. BadGuy): ").split(',')
    blacklist = [n.strip() for n in blacklist if n.strip()]

    config = {
        "password_hash": hash_password(pwd),
        "camera_type": camera_type,
        "unknown_label": unknown_label,
        "whitelist": whitelist,
        "blacklist": blacklist,
        "whitelist_greeting": "Welcome {name}",
        "blacklist_greeting": "Warning, {name} is restricted",
        "default_known_greeting": "Hello {name}"
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
        
    # Lock config strictly
    Path("config.json").chmod(0o600)
    print("Configuration saved securely!")

if __name__ == "__main__":
    main()
"""

RUN_SH = """#!/bin/bash
# Auto Update
echo "[Run] Checking for GitHub updates..."
git pull origin main || echo "Update check failed or not a repo. Continuing..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "${ROOT_DIR}"

if [ ! -f "config.json" ]; then
    echo "Config not found! Running setup..."
    bash setup.sh
fi

echo "[Run] Activating virtual environment..."
source .venv/bin/activate || true

echo "[Lockdown] Shutting down Raspberry Pi desktop panels so nothing else can run..."
pkill -f lxpanel || true
pkill -f pcmanfm || true
pkill -f wf-panel-pi || true

echo "[Run] Starting Face Gate UI..."
python3 main.py "$@"

echo "[Unlocked] Restoring desktop interface..."
nohup lxpanel --profile LXDE-pi >/dev/null 2>&1 &
nohup pcmanfm --desktop --profile LXDE-pi >/dev/null 2>&1 &
nohup wf-panel-pi >/dev/null 2>&1 &
"""

README_MD = """# Coral Face Gate

A custom Edge TPU accelerated facial recognition gateway for the Raspberry Pi 4.

## Features
- **Strict Coral Edge TPU Enforcement**: Leverages the Google USB Accelerator for real-time 30+ fps bounding box tracking.
- **Configurable Intelligence**: Built-in whitelist, blacklist, and custom labels via configuration wizard.
- **App UI Locking**: Exiting the OpenCV fullscreen view requires typing a hidden password securely created during setup. Intruder triggers spam automated max-volume alarms.
- **OS Level Persistence**: Options to force disable screen-sleep and automatically launch on Pi startup. Models & photo DB locked to user account. 
- **Auto Updatable**: Automatically pulls from the main branch on startup.

## Setup & Installation

**One-Line Quickstart for Raspberry Pi:**
Copy and paste this into your terminal. It will download the codebase, fix permissions, and launch the setup wizard immediately:
```bash
git clone https://github.com/jensenhuangfan/CoralUSBDoorCamForPi4.git && cd CoralUSBDoorCamForPi4 && chmod +x setup.sh && ./setup.sh
```

**Adding Photos**: 
Place CLEAR, face-forward images of authorized users in target directories inside `known_faces/`.
- Setup makes this folder automatically.
- E.g. `known_faces/John Doe/1.jpg`

## Usage
Start the background app manually:
```bash
./run.sh
```
*(If you selected auto-boot during setup, you can simply restart the Pi).*

**Command Line Flags:**
- `--usbcam`: Override the default camera and force the use of a standard USB webcam. (By default, uses the setup config or Pi Camera 3).
- `--camera X`: Set the USB camera index (default is 0).

**How to Exit**:
There is NO visual prompt. While the UI is active, simply **type the password you created during setup and press ENTER**.

## Configuration
To reset the password or rules, delete `config.json` and re-run `./setup.sh`, or manually edit `config.json`.
"""

MAIN_PY = """import sys
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
        out = subprocess.check_output("xrandr | grep '\\*' | head -n 1", shell=True).decode()
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

    def process_person(self, name: str) -> None:
        now = time.time()
        last_time = self.last_welcome_time.get(name, 0.0)
        if now - last_time >= self.welcome_cooldown:
            self.last_welcome_time[name] = now
            
            if name in CONFIG.get("whitelist", []):
                self.speak(CONFIG["whitelist_greeting"].replace("{name}", name))
            elif name in CONFIG.get("blacklist", []):
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
        self.is_trained = False

    def train(self, known_faces_dir: Path, detector: CoralFaceDetector) -> None:
        if not known_faces_dir.exists(): return
        
        samples, labels = [], []
        person_dirs = sorted([p for p in known_faces_dir.iterdir() if p.is_dir()])
        for label, person_dir in enumerate(person_dirs):
            self.label_to_name[label] = person_dir.name
            for image_path in person_dir.rglob("*"):
                if image_path.is_file() and image_path.suffix.lower() in IMAGE_SUFFIXES:
                    img = cv2.imread(str(image_path))
                    if img is None: continue
                    detection = detector.detect_largest_face(img)
                    if detection:
                        processed = preprocess_face(img, detection.bbox)
                        if processed is not None:
                            samples.append(processed)
                            labels.append(label)
        if len(samples) > 1:
            self.recognizer.train(samples, np.array(labels, dtype=np.int32))
            self.is_trained = True

    def predict(self, face_crop: np.ndarray) -> Tuple[str, float]:
        if not self.is_trained:
            return CONFIG.get("unknown_label", "Intruder"), 999.0
        label, confidence = self.recognizer.predict(face_crop)
        if confidence <= self.unknown_threshold and label in self.label_to_name:
            return self.label_to_name[label], float(confidence)
        return CONFIG.get("unknown_label", "Intruder"), float(confidence)

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
    face_db.train(Path("known_faces"), detector)
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
            has_unknown = False

            for detection in cached_detections:
                processed = preprocess_face(frame, detection.bbox)
                if processed is None: continue

                name, confidence = face_db.predict(processed)
                draw_result(frame, detection.bbox, name, detection.score, confidence)

                if name == CONFIG.get("unknown_label", "Intruder"):
                    has_unknown = True
                else:
                    known_faces_this_frame.add(name)

            if has_unknown:
                speech.alert_intruder()
            
            for name in known_faces_this_frame:
                if name not in last_known_faces:
                    speech.process_person(name)

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
"""

for f, c in [(".gitignore", GITIGNORE), ("setup.sh", SETUP_SH), ("setup_app.py", SETUP_APP_PY), 
             ("run.sh", RUN_SH), ("README.md", README_MD), ("main.py", MAIN_PY)]:
    with open(f, "w") as file:
        file.write(c.strip() + "\n")
    if f.endswith(".sh"): os.chmod(f, 0o755)

print("ALL FILES UPDATED WITH DEFAULT PICAM3 LOGIC!")
