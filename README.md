# Coral Face Gate

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
