import json
import getpass
import hashlib
from pathlib import Path

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    print("\n--- Face Gate Configuration Wizard ---")
    
    # Password setup
    while True:
        pwd = getpass.getpass("Enter a new password to lock/exit the app: ")
        pwd2 = getpass.getpass("Confirm password: ")
        if pwd == pwd2 and len(pwd) > 0:
            break
        print("Passwords do not match or are empty. Try again.")
        
    print("\n[Camera Setup]")
    print("1. Pi Camera Module 3 (libcamera)")
    print("2. Standard USB Webcam")
    cam_choice = input("Select camera type (1-2) [default: 1]: ").strip()
    camera_type = "usbcam" if cam_choice == "2" else "picam3"

    unknown_label = input("\nLabel for unrecognized faces [default: Intruder]: ") or "Intruder"
    
    print("\n[Whitelists & Blacklists]")
    print("To add people to the system, create a folder with their name inside the 'whitelist' (or 'blacklist') directory.")
    print("Place clear photos of their face (.jpg, .jpeg, .png, .bmp) inside that folder.")
    print("Example: whitelist/John/photo1.jpg")
    
    Path("whitelist").mkdir(parents=True, exist_ok=True)
    
    print("\nDo you want a separate 'blacklist' folder to trap/restrict specific people?")
    print("1. Yes (default)")
    print("2. No")
    bl_choice = input("Select an option (1-2): ").strip()
    
    has_blacklist = (bl_choice != "2")
    if has_blacklist:
        Path("blacklist").mkdir(parents=True, exist_ok=True)

    config = {
        "password_hash": hash_password(pwd),
        "camera_type": camera_type,
        "unknown_label": unknown_label,
        "has_blacklist": has_blacklist,
        "whitelist_greeting": "Welcome {name}",
        "blacklist_greeting": "Warning, {name} is restricted",
        "default_known_greeting": "Hello {name}",
        "detection_threshold": 0.45,
        "unknown_threshold": 115.0,
        "intruder_cooldown": 3.0,
        "welcome_cooldown": 8.0,
        "speech_speed": 150
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
        
    Path("config.json").chmod(0o600)
    print("Configuration saved securely!")

if __name__ == "__main__":
    main()
