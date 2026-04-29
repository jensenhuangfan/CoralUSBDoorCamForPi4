# Face Gate Complete Documentation

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
