import json
import getpass
import hashlib
import time
import os
import subprocess
from pathlib import Path

def log_event(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open("admin_log.txt", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    print("\nConfiguration updated securely.")
    log_event("Updated config.json elements.")

def main():
    if not Path("config.json").exists():
        print("Error: config.json not found. Please run ./setup.sh first.")
        return

    with open("config.json", "r") as f:
        config = json.load(f)

    print("\n--- Face Gate Admin Tool ---")
    pwd = getpass.getpass("Enter Admin Password: ")
    pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()

    if pwd_hash != config.get("password_hash"):
        print("Access Denied.")
        log_event("Failed admin login attempt.")
        return

    log_event("Successful admin login.")
    print("\nAccess Granted.")

    while True:
        print("\n--- Admin Settings Menu ---")
        print("1. Change Target Camera Type")
        print("2. Change Unknown Face Label")
        print("3. Toggle Blacklist Folder Feature")
        print("4. Edit System Greetings")
        print("5. Change Admin Password")
        print("6. Check for App Updates (GitHub Sync)")
        print("7. Re-run Initial Setup Wizard")
        print("8. Uninstall Application")
        print("9. Exit Admin Tool")
        
        choice = input("Select an option (1-9): ").strip()
        
        if choice == "1":
            print("\n[Change Camera Type]")
            print(f"Current: {config.get('camera_type')}")
            print("1. Pi Camera Module 3 (libcamera)")
            print("2. Standard USB Webcam")
            cam_choice = input("Select new camera type (1-2): ").strip()
            if cam_choice == "1":
                config["camera_type"] = "picam3"
                save_config(config)
            elif cam_choice == "2":
                config["camera_type"] = "usbcam"
                save_config(config)
            else:
                print("Invalid choice, skipped.")

        elif choice == "2":
            print(f"\nCurrent Unknown Face Label: {config.get('unknown_label')}")
            new_lbl = input("Enter new label for unknown faces (leave blank to cancel): ").strip()
            if new_lbl:
                config["unknown_label"] = new_lbl
                save_config(config)

        elif choice == "3":
            current_status = config.get("has_blacklist", False)
            status_text = "Enabled" if current_status else "Disabled"
            print(f"\nCurrent Blacklist feature is: {status_text}")
            print("1. Enable Blacklist Feature")
            print("2. Disable Blacklist Feature")
            bl_choice = input("Select (1-2): ").strip()
            if bl_choice == "1":
                config["has_blacklist"] = True
                Path("blacklist").mkdir(parents=True, exist_ok=True)
                save_config(config)
            elif bl_choice == "2":
                config["has_blacklist"] = False
                save_config(config)

        elif choice == "4":
            print("\n[Edit System Greetings]")
            print("Use {name} inside the text where you want the person's name spoken.")
            
            print(f"1. Edit Whitelist Greeting (Current: {config.get('whitelist_greeting')})")
            print(f"2. Edit Blacklist Greeting (Current: {config.get('blacklist_greeting')})")
            print(f"3. Edit Default Known Greeting (Current: {config.get('default_known_greeting')})")
            print("4. Back to Main Menu")
            greet_choice = input("Select which to edit (1-4): ").strip()

            if greet_choice == "1":
                wg = input("New Whitelist Greeting: ").strip()
                if wg: 
                    config["whitelist_greeting"] = wg
                    save_config(config)
            elif greet_choice == "2":
                bg = input("New Blacklist Greeting: ").strip()
                if bg: 
                    config["blacklist_greeting"] = bg
                    save_config(config)
            elif greet_choice == "3":
                dg = input("New Default Greeting: ").strip()
                if dg: 
                    config["default_known_greeting"] = dg
                    save_config(config)

        elif choice == "5":
            print("\n[Change Password]")
            new_pwd = getpass.getpass("Enter new password: ")
            new_pwd2 = getpass.getpass("Confirm new password: ")
            if new_pwd == new_pwd2 and len(new_pwd) > 0:
                config["password_hash"] = hashlib.sha256(new_pwd.encode()).hexdigest()
                save_config(config)
            else:
                print("Passwords do not match or are empty. Aborted.")

        elif choice == "6":
            print("\n[Checking for GitHub update...]")
            log_event("Initiated manual git update check.")
            subprocess.run(["git", "pull", "origin", "main"])
            print("Update task finished.")

        elif choice == "7":
            print("\n[Re-run Setup Wizard]")
            log_event("Launched setup_app.py manually.")
            subprocess.run(["python3", "setup_app.py"])
            with open("config.json", "r") as f:
                config = json.load(f)

        elif choice == "8":
            print("\n[Uninstall Application]")
            print("1. YES, proceed with full uninstall.")
            print("2. Cancel uninstall.")
            confirm = input("Select an option (1-2): ").strip()
            if confirm == "1":
                log_event("Uninstalled application via Admin menu.")
                print("Removing autostart entry...")
                os.system("rm -f ~/.config/autostart/facegate.desktop")
                print("Note: To fully delete files, you must delete this directory manually or run: rm -rf " + os.getcwd())
                print("Uninstall hooks completed. Exiting Admin Tool.")
                break
            else:
                print("Uninstall cancelled.")

        elif choice == "9":
            print("Exiting tool.")
            break
        else:
            print("Invalid input.")

if __name__ == "__main__":
    main()
