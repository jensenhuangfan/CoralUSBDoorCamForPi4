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
echo "NOTE: The newest Raspberry Pi OS supported is 'Bullseye'."
echo "This is a strict requirement for Google Coral's Python packages."
echo "============================================="

# 1. Update and install dependencies
echo "[1/6] Installing APT dependencies..."
sudo apt-get update
sudo apt-get install -y espeak libespeak1 espeak-ng python3-opencv python3-pip

# 2. Virtual Environment setup
echo "[2/6] Python Environment Setup..."
read -p "Create a Python virtual environment (.venv)? [Y/n] (Highly Recommended to avoid system conflicts): " use_venv
if [[ -z "$use_venv" || "$use_venv" == "y" || "$use_venv" == "Y" ]]; then
    python3 -m venv .venv --system-site-packages
    source .venv/bin/activate
    pip install -r requirements.txt || true
    echo 'USE_VENV=true' > .env
else
    pip3 install -r requirements.txt || true
    echo 'USE_VENV=false' > .env
fi

# 3. Model download
echo "[3/6] Downloading Google Coral Face Detection Model..."
mkdir -p models
if [ ! -f "models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite" ]; then
    wget -O models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite \
    https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite
fi

# 4. Folder creation & OS lock
echo "[4/6] Creating secure directories..."
mkdir -p known_faces

# 5. Disable sleep and auto-display off
read -p "Do you want to disable screen sleep and auto-display off? (y/n): " disable_sleep
if [[ "$disable_sleep" == "y" || "$disable_sleep" == "Y" ]]; then
    echo "Disabling sleep modes..."
    sudo xset s off -dpms 2>/dev/null || true
    sudo setterm -blank 0 -powerdown 0 2>/dev/null || true
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
if [ -f ".venv/bin/python3" ]; then
    .venv/bin/python3 setup_app.py
else
    python3 setup_app.py
fi

# 7. Secure the entire project folder
echo "[6/6] Locking down application files..."
APP_DIR=$(pwd)
chmod -R 700 "$APP_DIR"
chown -R $USER:$USER "$APP_DIR"

echo "============================================="
echo " Setup Complete! "
echo " Add your photos to known_faces/<Name>/"
echo " To run: ./run.sh"
echo " See DOCUMENTATION.md for details."
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

if [ -f ".env" ]; then
    source .env
fi

if [ "$USE_VENV" != "false" ]; then
    echo "[Run] Activating virtual environment..."
    source .venv/bin/activate || echo "No .venv found, continuing without it..."
fi

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
**IMPORTANT OS REQUIREMENT:** The newest Raspberry Pi OS supported is **Bullseye**. 
Newer OS versions (Bookworm) broke compatibility with the Google Coral python packages.

## Setup & Installation

**One-Line Quickstart for Raspberry Pi:**
Copy and paste this into your terminal:
```bash
git clone https://github.com/jensenhuangfan/CoralUSBDoorCamForPi4.git && cd CoralUSBDoorCamForPi4 && chmod +x setup.sh && ./setup.sh
```

Please refer to **DOCUMENTATION.md** for a complete breakdown of configuration, UI locking, kiosk-mode logic, and file security.
"""

DOCUMENTATION_MD = """# Face Gate Complete Documentation

## Supported OS
**Raspberry Pi OS Bullseye** (Legacy) is the absolute newest OS version supported. Google Coral Edge TPU pycoral libraries require Python 3.9/3.10 and fail to compile natively on Bookworm's Python 3.11 environment. 

## Application Security & Lock-Down
This app is designed to be an impenetrable kiosk security app.
1. **File Permissions**: The setup script recursively runs `chmod 700` and `chown` on the entire project folder. ONLY the physical Raspberry Pi account owner who authenticates with the OS password can view, modify, or delete the app config, known faces, and code files.
2. **Kiosk Mode UI Lock**: During execution (`run.sh`), the script literally terminates the OS graphical panels (`lxpanel`, `pcmanfm`). User cannot click out, open terminals, or close the app via X button.
3. **Password Unlock**: To exit the app, the user must type the secret wizard password directly into the camera window. A wrong password triggers an automated volume-maxed audible looping alarm.

## Configuration (config.json)
The `setup.sh` script runs `setup_app.py`, producing `config.json`.
- `password_hash`: Kept secure, used to validate the exit command.
- `camera_type`: Set to `picam3` (libcamera) or `usbcam` (V4L2).
- `unknown_label`: What to call unrecognized individuals (default: "Intruder").
- `whitelist`: Comma separated array of `known_faces` names that get a special greeting.
- `blacklist`: Comma separated array of `known_faces` names that trigger a restrictive warning alarm.
- `whitelist_greeting`, `blacklist_greeting`, `default_known_greeting`: The text to feed into the pyttsx3/eSpeak TTS engine.

## Adding Faces
Create a folder inside `known_faces/` named exactly what you want the system to call the person. Add 5-10 well-lit face-forward pictures (jpg, png).
Example:
`known_faces/John Swanson/1.jpg`
`known_faces/John Swanson/2.jpg`

## Python Environment
During setup, you are prompted to use a `.venv` (Virtual Environment). **It is highly recommended** to say yes (Y). This isolates all PIP modules from the rest of your system packages, cleanly bridging hardware and UI dependencies safely.

## Hardware Acceleration
Runs exclusively on the **Google Coral USB Edge TPU Accelerator**, which hardware-accelerates MobileNet SSD models out to 60+ FPS. Legacy OpenCV Haar cascade methods have been completely removed.
"""

for f, c in [(".gitignore", GITIGNORE), ("setup.sh", SETUP_SH), ("setup_app.py", SETUP_APP_PY), 
             ("run.sh", RUN_SH), ("README.md", README_MD), ("DOCUMENTATION.md", DOCUMENTATION_MD)]:
    with open(f, "w") as file:
        file.write(c.strip() + "\n")
    if f.endswith(".sh"): os.chmod(f, 0o755)

print("ALL FILES WRITTEN SUCCESSFULLY.")
