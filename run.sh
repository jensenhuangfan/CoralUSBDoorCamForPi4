#!/bin/bash
# Auto Update
echo "[Run] Checking for GitHub updates..."
git stash || true
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

echo "[Cleanup] Freeing up Coral TPU from zombie processes..."
pkill -f "python3 main.py" || true

echo "[Run] Starting Face Gate UI..."
while true; do
    python3 main.py "$@"
    EXIT_CODE=$?
    
    # If the user typed the correct password during normal operation, main.py returns exit code 0
    if [ $EXIT_CODE -eq 0 ]; then
        break
    fi

    # If the user typed the password during tamper mode to reconnect devices, it returns 42
    if [ $EXIT_CODE -eq 42 ]; then
        echo "[Security] Admin authorized reconnect. Reloading application..."
        sleep 1
        continue
    fi
    
    # If the script crashed (e.g. C++ aborts from TPU unplug or Segfault), auto-restart it
    echo "[Security] Critical application crash detected! Attempting immediate lock restart..."
    sleep 1
done

echo "[Unlocked] Restoring desktop interface..."
nohup lxpanel --profile LXDE-pi >/dev/null 2>&1 &
disown
nohup pcmanfm --desktop --profile LXDE-pi >/dev/null 2>&1 &
disown
nohup wf-panel-pi >/dev/null 2>&1 &
disown
