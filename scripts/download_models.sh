#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"
MODEL_FILE="ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite"
CASCADE_FILE="haarcascade_frontalface_default.xml"

mkdir -p "${MODELS_DIR}"

# Download Haar Cascade (always needed as fallback)
echo "[1/2] Downloading Haar Cascade classifier..."
if [[ ! -f "${MODELS_DIR}/${CASCADE_FILE}" ]]; then
    curl -fsSL "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/${CASCADE_FILE}" \
        -o "${MODELS_DIR}/${CASCADE_FILE}" || \
    curl -fsSL "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/${CASCADE_FILE}" \
        -o "${MODELS_DIR}/${CASCADE_FILE}" || {
        echo "WARNING: Could not download Haar Cascade"
    }
    if [[ -f "${MODELS_DIR}/${CASCADE_FILE}" ]]; then
        echo "✓ Haar Cascade ready"
    fi
else
    echo "✓ Haar Cascade already present"
fi

# Download Coral model (optional but preferred)
echo "[2/2] Downloading Coral Edge TPU model (optional)..."
cd "${MODELS_DIR}"
rm -f "${MODEL_FILE}" 2>/dev/null || true

# Try multiple sources
download_coral() {
    local url="$1"
    echo "  Trying: ${url}"
    if curl -fsSL --connect-timeout 5 --max-time 30 "${url}" -o "${MODEL_FILE}"; then
        if [[ -f "${MODEL_FILE}" ]] && [[ $(stat -f%z "${MODEL_FILE}" 2>/dev/null || stat -c%s "${MODEL_FILE}") -gt 100000 ]]; then
            echo "  ✓ Coral model downloaded"
            return 0
        fi
        rm -f "${MODEL_FILE}"
    fi
    return 1
}

# Try sources
download_coral "https://dl.google.com/coral/test_data/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite" || \
download_coral "https://raw.githubusercontent.com/google-coral/test_data/master/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite" || \
{
    echo "  INFO: Coral model not available, will use Haar Cascade"
}

echo "Models setup complete"
