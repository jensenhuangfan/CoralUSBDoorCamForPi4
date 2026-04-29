#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Run this script as a normal user (not root)."
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/5] Installing Coral apt repo..."
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/coral-archive-keyring.gpg || true
echo "deb [signed-by=/usr/share/keyrings/coral-archive-keyring.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" | \
  sudo tee /etc/apt/sources.list.d/coral-edgetpu.list >/dev/null

echo "[2/5] Installing OS dependencies..."
sudo apt-get update || true
sudo apt-get install -y \
  libedgetpu1-std \
  python3-pycoral \
  python3-opencv \
  python3-pip \
  python3-numpy \
  python3-pil \
  curl \
  python3-pyttsx3 \
  espeak \
  espeak-ng || true

echo "[3/5] Installing pip packages (with fallbacks)..."
python3 -m pip install --upgrade pip || python3 -m pip install --upgrade --break-system-packages pip || true
python3 -m pip install Pillow || python3 -m pip install --break-system-packages Pillow || true

echo "[4/5] Downloading Coral model..."
bash "${ROOT_DIR}/scripts/download_models.sh" || true

echo "[5/5] Setup complete."
echo "Run: cd ${ROOT_DIR} && python3 main.py"
