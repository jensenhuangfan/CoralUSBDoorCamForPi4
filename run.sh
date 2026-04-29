#!/usr/bin/env bash
set -euo pipefail

# This script activates the .venv and runs the Coral face gate app

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
MODEL_DIR="${ROOT_DIR}/models"
MODEL_FILE="${MODEL_DIR}/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite"

# Activate virtual environment
if [[ -d "${VENV_DIR}" ]]; then
    echo "[Init] Activating virtual environment..."
    source "${VENV_DIR}/bin/activate"
else
    echo "[Error] Virtual environment not found at ${VENV_DIR}"
    echo "Create one with: python3 -m venv .venv"
    exit 1
fi

# Download model if missing
if [[ ! -f "${MODEL_FILE}" ]]; then
    echo "[Init] Downloading Edge TPU model..."
    bash "${ROOT_DIR}/scripts/download_models.sh" || {
        echo "[Error] Failed to download model"
        exit 1
    }
fi

# Run the app
echo "[Run] Starting Coral Face Gate (fullscreen mode)"
echo "Press Q to quit"
cd "${ROOT_DIR}"

# Ensure no zombie python processes are hogging the Coral USB
echo "[Init] Releasing any hung Coral USB connections..."
pkill -f "python3 main.py" || true

# Determine if we should attempt picam3 mode if no camera specified
if [[ "$*" == *"--picam3"* ]]; then
    python3 main.py "$@"
else
    echo "Tip: using a Pi Camera 3? Add --picam3 flag."
    python3 main.py "$@"
fi
