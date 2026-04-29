# Coral Face Gate (Raspberry Pi 4)

This project was rebuilt from scratch for:
- Raspberry Pi 4
- Coral USB Accelerator (with automatic fallback to Haar Cascade if model unavailable)
- Existing photo database in `known_faces/<person_name>/...`

## What This Build Uses

- Face detection: Coral Edge TPU model (primary) or Haar Cascade (fallback)
- Face identification: OpenCV LBPH recognizer trained from your photo folders
- Audio alerts: pyttsx3 text-to-speech with eSpeak
- Runtime: Python 3 on Raspberry Pi OS in a virtual environment (.venv)
- Camera: Supports standard USB Webcams AND Pi Camera v3 (libcamera)

## Folder Layout

- `known_faces/` (your preserved photo database)
- `models/` (Coral Edge TPU models)
- `.venv/` (Python virtual environment)
- `scripts/setup_rpi4_coral.sh` (system setup)
- `scripts/download_models.sh` (model downloader)
- `run.sh` (app launcher with venv activation)
- `main.py` (live camera app)

## Quick Start

**Just run:**
```bash
chmod +x run.sh
./run.sh
```

The app will automatically:
- Activate your .venv
- Load the Coral model (or fall back to Haar Cascade)
- Start the camera in fullscreen mode
- Say "Intruder alert" for unknown faces (repeating every 3 seconds)
- Say "Welcome [name]" for recognized people

Press `q` to exit.

## Virtual Environment

Your `.venv` already exists. You can:

**Activate manually:**
```bash
source .venv/bin/activate
# Now use: pip install, python, etc.
deactivate  # when done
```

**Or just use the launcher:**
```bash
./run.sh
```

## 1) Hardware Setup

1. Plug the Coral USB Accelerator into a USB 3.0 port on the Pi 4
2. Connect your camera
3. Ensure each person has a separate folder in `known_faces/`

## 2) Run

**Easiest way:**
```bash
./run.sh
```

**Using Pi Camera 3 (uses libcamera GStreamer plugin instead of standard V4L2):**
```bash
./run.sh --picam3
```

**With custom options:**
```bash
./run.sh --camera 0 --unknown-threshold 70 --detect-every 2
```

## Command-Line Options

- `--picam3`: Use Raspberry Pi camera 3 via libcamera
- `--camera`: USB camera index (default: 0)
- `--det-threshold`: detector confidence for Coral (default: 0.45)
- `--unknown-threshold`: LBPH recognition threshold (lower = stricter, default: 70)
- `--detect-every`: run detection every N frames (default: 2)

## Troubleshooting

**"Model identifier should be 'TFL3'"**
- The Coral model is unavailable. App will use Haar Cascade instead (slower but works).

**No audio alerts**
- Ensure espeak is installed: `sudo apt-get install espeak espeak-ng`

**Camera not found**
- Try: `./run.sh --camera 1`
- List available: `ls -la /dev/video*`

**Face recognition not working**
- Add more clear, front-facing photos per person to `known_faces/`
- Adjust `--unknown-threshold` (try 50 for stricter matching)

**cv2.face module missing**
- Install: `sudo apt-get install python3-opencv`

## Technical Details

- Detection: Coral Edge TPU (if available) or OpenCV Haar Cascade
- Recognition: OpenCV Local Binary Patterns Histograms (LBPH)
- Audio: pyttsx3 with espeak backend
- Display: Fullscreen OpenCV window
