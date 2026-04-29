#!/bin/bash
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
