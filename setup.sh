#!/bin/bash
echo "============================================="
echo " Face Gate Installer (Coral Edge TPU) "
echo "============================================="
echo "NOTE: The newest Raspberry Pi OS supported is 'Bullseye'."
echo "This is a strict requirement for Google Coral's Python packages."
echo "============================================="

# 1. Update and install dependencies
echo "[1/6] Installing APT dependencies and Google Coral drivers..."
# Add Google Coral repository
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

sudo apt-get update
sudo apt-get install -y espeak libespeak1 espeak-ng python3-opencv python3-pip libedgetpu1-std python3-pycoral

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
    wget -O models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite     https://github.com/google-coral/test_data/raw/master/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite
fi

# 4. OS lock
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
echo " Add your photos to whitelist/<Name>/ or blacklist/<Name>/"
echo " To run: ./run.sh"
echo " To configure later: python3 admin_tool.py"
echo " See DOCUMENTATION.md for details."
echo "============================================="
