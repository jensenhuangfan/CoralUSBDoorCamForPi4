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
    cam_choice = input("Are you using a Pi Camera Module 3 (libcamera) or a standard USB Webcam? (pi/usb) [default: pi]: ").strip().lower()
    camera_type = "usbcam" if cam_choice == "usb" else "picam3"

    unknown_label = input("\nLabel for unrecognized faces [default: Intruder]: ") or "Intruder"
    
    print("\n[Whitelists & Blacklists]")
    print("To add people to the system, create a folder with their name inside the 'whitelist' (or 'blacklist') directory.")
    print("Place clear photos of their face (.jpg, .jpeg, .png, .bmp) inside that folder.")
    print("Example: whitelist/John/photo1.jpg")
    
    Path("whitelist").mkdir(parents=True, exist_ok=True)
    
    use_blacklist = input("Do you want a separate 'blacklist' folder to trap/restrict specific people? (y/n) [default: y]: ").strip().lower()
    if use_blacklist != "n":
        Path("blacklist").mkdir(parents=True, exist_ok=True)
        has_blacklist = True
    else:
        has_blacklist = False

    config = {
        "password_hash": hash_password(pwd),
        "camera_type": camera_type,
        "unknown_label": unknown_label,
        "has_blacklist": has_blacklist,
        "whitelist_greeting": "Welcome {name}",
        "blacklist_greeting": "Warning, {name} is restricted",
        "default_known_greeting": "Hello {name}"
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
        
    Path("config.json").chmod(0o600)
    print("Configuration saved securely!")

if __name__ == "__main__":
    main()
