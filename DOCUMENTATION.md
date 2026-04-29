# Face Gate Complete Documentation

## Supported OS
**Raspberry Pi OS Bullseye** (Legacy) is the absolute newest OS version supported. Google Coral Edge TPU pycoral libraries require Python 3.9/3.10 and fail to compile natively on Bookworm's Python 3.11 environment. 

## Application Security & Lock-Down
This app is designed to be an impenetrable kiosk security app.
1. **File Permissions**: The setup script recursively runs `chmod 700` and `chown` on the entire project folder. ONLY the physical Raspberry Pi account owner who authenticates with the OS password can view, modify, or delete the app config, known faces, and code files.
2. **Kiosk Mode UI Lock**: During execution (`run.sh`), the script literally terminates the OS graphical panels (`lxpanel`, `pcmanfm`). User cannot click out, open terminals, or close the app via X button.
3. **Password Unlock**: To exit the app, the user must type the secret wizard password directly into the camera window. A wrong password triggers an automated volume-maxed audible looping alarm.

## Configuration (config.json) & Admin Tool
The `setup.sh` script runs `setup_app.py`, producing `config.json`.
- `password_hash`: Kept secure, used to validate the exit command.
- `camera_type`: Set to `picam3` (libcamera) or `usbcam` (V4L2).
- `unknown_label`: What to call unrecognized individuals (default: "Intruder").
- `whitelist_greeting`, `blacklist_greeting`, `default_known_greeting`: The text to feed into the pyttsx3/eSpeak TTS engine.

**Admin Tool / Uninstaller (`admin_tool.py`)**:
Run `python3 admin_tool.py` (or `./.venv/bin/python3 admin_tool.py`) anytime after setup to:
1. Re-run the configuration wizard (requires app password).
2. Uninstall the application safely (removes autostart hooks).
All admin actions are securely logged to `admin_log.txt`.

## Intelligent Volume Control
The system tracks the exact master volume percentage when started. If it's fully muted, it overrides to 50%. If an intruder or blacklisted person appears (or bad password entered), the script temporarily cranks the Raspberry Pi volume to 100% to maximize alarm visibility, then politely restores it back to your original volume immediately after.

## Adding Faces
Create folders inside `whitelist/` or `blacklist/` named exactly what you want the system to call the person. Add clear, face-forward pictures (jpg, png).
Example:
`whitelist/John Swanson/1.jpg`
`blacklist/BadGuy/1.jpg`

## Python Environment
During setup, you are prompted to use a `.venv` (Virtual Environment). **It is highly recommended** to say yes (Y). This isolates all PIP modules from the rest of your system packages, cleanly bridging hardware and UI dependencies safely.

## Hardware Acceleration
Runs exclusively on the **Google Coral USB Edge TPU Accelerator**, which hardware-accelerates MobileNet SSD models out to 60+ FPS. Legacy OpenCV Haar cascade methods have been completely removed.
