#!/bin/bash
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
    wget -O models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite     https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite
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
