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
        print("1. Camera & System Setup")
        print("2. Display & Label Preferences")
        print("3. Detection & Blacklist Tools")
        print("4. Greeting Phrases")
        print("5. Audio, Speech, & Volume Tuner")
        print("6. AI Recognition Thresholds")
        print("7. Event Logging & Diagnostics")
        print("8. Change Admin Master Password")
        print("9. Uninstall & Setup Management")
        print("10. Exit Admin Tool")
        
        choice = input("Select an option (1-10): ").strip()
        
        if choice == "1":
            print("\n[Camera & System Setup]")
            print(f"Current Camera: {config.get('camera_type')}")
            print("1. Pi Camera Module 3 (libcamera)")
            print("2. Standard USB Webcam")
            print("3. Back to Main Menu")
            cam_choice = input("Select an option (1-3): ").strip()
            if cam_choice == "1":
                config["camera_type"] = "picam3"
                save_config(config)
            elif cam_choice == "2":
                config["camera_type"] = "usbcam"
                save_config(config)

        elif choice == "2":
            print("\n[Display & Label Preferences]")
            print(f"1. Change Unknown Face Label (Current: {config.get('unknown_label')})")
            print(f"2. Toggle Bounding Box Rendering (Current: {'ON' if config.get('draw_boxes', True) else 'OFF'})")
            print(f"3. Draw Text Overlays on Faces (Current: {'ON' if config.get('draw_text', True) else 'OFF'})")
            disp_choice = input("Select option (1-3): ").strip()
            if disp_choice == "1":
                new_lbl = input("Enter new label for unknown faces (leave blank to cancel): ").strip()
                if new_lbl:
                    config["unknown_label"] = new_lbl
                    save_config(config)
            elif disp_choice == "2":
                config["draw_boxes"] = not config.get("draw_boxes", True)
                save_config(config)
            elif disp_choice == "3":
                config["draw_text"] = not config.get("draw_text", True)
                save_config(config)

        elif choice == "3":
            print("\n[Detection & Blacklist Tools]")
            status_text = "Enabled" if config.get("has_blacklist", False) else "Disabled"
            print(f"Current Blacklist feature is: {status_text}")
            print("1. Enable Blacklist Feature")
            print("2. Disable Blacklist Feature")
            print("3. Back to Main Menu")
            bl_choice = input("Select (1-3): ").strip()
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
            print("\n[Audio, Speech, & Volume Tuner]")
            print(f"1. AI Speech Rate in WPM (Current: {config.get('speech_speed', 150)})")
            print(f"2. Disable/Enable Speech Engine (Current: {'ON' if config.get('enable_speech', True) else 'OFF'})")
            print(f"3. eSpeak Voice Language/Type (Current: {config.get('espeak_voice', 'en-us')})")
            print(f"4. Override System Volume Controls (Current: {'ON' if config.get('manage_volume', True) else 'OFF'})")
            print(f"5. Maximum Alarm Volume Percent (Current: {config.get('max_volume_pct', 100)}%)")
            print(f"6. Standard Idle Volume Percent (Current: {config.get('idle_volume_pct', 50)}%)")
            print("7. Back to Main Menu")
            aud_choice = input("Select which to edit (1-7): ").strip()
            
            if aud_choice == "1":
                try:
                    config["speech_speed"] = int(input("New speed WPM (e.g. 150): "))
                    save_config(config)
                except ValueError: print("Invalid number.")
            elif aud_choice == "2":
                config["enable_speech"] = not config.get("enable_speech", True)
                save_config(config)
            elif aud_choice == "3":
                nv = input("Enter new eSpeak voice code (e.g. en-us, en-gb, f1, m1): ").strip()
                if nv:
                    config["espeak_voice"] = nv
                    save_config(config)
            elif aud_choice == "4":
                config["manage_volume"] = not config.get("manage_volume", True)
                save_config(config)
            elif aud_choice == "5":
                try:
                    config["max_volume_pct"] = int(input("New alarm volume percent (0-100): "))
                    save_config(config)
                except ValueError: print("Invalid number.")
            elif aud_choice == "6":
                try:
                    config["idle_volume_pct"] = int(input("New idle system volume percent (0-100): "))
                    save_config(config)
                except ValueError: print("Invalid number.")

        elif choice == "6":
            print("\n[AI Recognition Thresholds]")
            print(f"1. Face Detection Threshold (Current: {config.get('detection_threshold', 0.45)})")
            print(f"2. Recognition Strictness/LBPH Distance (Current: {config.get('unknown_threshold', 115.0)})")
            print(f"3. Intruder Alarm Cooldown in seconds (Current: {config.get('intruder_cooldown', 3.0)})")
            print(f"4. Welcome Greeting Cooldown in seconds (Current: {config.get('welcome_cooldown', 8.0)})")
            print("5. Back to Main Menu")
            tune_choice = input("Select which to edit (1-5): ").strip()
            
            if tune_choice == "1":
                try: 
                    config["detection_threshold"] = float(input("New value (e.g. 0.45): "))
                    save_config(config)
                except ValueError: print("Invalid number.")
            elif tune_choice == "2":
                try:
                    config["unknown_threshold"] = float(input("New value (lower=stricter, e.g. 110.0): "))
                    save_config(config)
                except ValueError: print("Invalid number.")
            elif tune_choice == "3":
                try:
                    config["intruder_cooldown"] = float(input("New cooldown in seconds: "))
                    save_config(config)
                except ValueError: print("Invalid number.")
            elif tune_choice == "4":
                try:
                    config["welcome_cooldown"] = float(input("New cooldown in seconds: "))
                    save_config(config)
                except ValueError: print("Invalid number.")

        elif choice == "7":
            print("\n[Event Logging & Diagnostics]")
            log_enabled = config.get("enable_logging", True)
            print(f"1. Toggle Logging (Currently: {'ON' if log_enabled else 'OFF'})")
            print(f"2. Change Log Target File (Currently: {config.get('log_file', 'security_log.txt')})")
            print("3. View Recent Logs")
            
            sub = input("Select an option (1-3): ").strip()
            if sub == "1":
                config["enable_logging"] = not log_enabled
                save_config(config)
            elif sub == "2":
                new_file = input("Enter new file path (e.g. security_log.txt): ").strip()
                if new_file: 
                    config["log_file"] = new_file
                    save_config(config)
            elif sub == "3":
                lf = config.get("log_file", "security_log.txt")
                if Path(lf).exists():
                    print("\n--- RECENT LOGS ---")
                    os.system(f"tail -n 20 {lf}")
                    print("-------------------\n")
                else:
                    print("Log file not found.")

        elif choice == "8":
            print("\n[Change Admin Master Password]")
            new_pwd = getpass.getpass("Enter new password: ")
            new_pwd2 = getpass.getpass("Confirm new password: ")
            if new_pwd == new_pwd2 and len(new_pwd) > 0:
                config["password_hash"] = hashlib.sha256(new_pwd.encode()).hexdigest()
                save_config(config)
            else:
                print("Passwords do not match or are empty. Aborted.")

        elif choice == "9":
            print("\n[Uninstall & Setup Management]")
            print("1. Check for App Updates (GitHub Sync)")
            print("2. Re-run Initial Setup Wizard")
            print("3. Uninstall Application")
            print("4. Back to Main Menu")
            sys_ops = input("Select option (1-4): ").strip()

            if sys_ops == "1":
                log_event("Initiated manual git update check.")
                subprocess.run(["git", "pull", "origin", "main"])
                print("Update task finished.")
            elif sys_ops == "2":
                log_event("Launched setup_app.py manually.")
                subprocess.run(["python3", "setup_app.py"])
                with open("config.json", "r") as f:
                    config = json.load(f)
            elif sys_ops == "3":
                print("WARNING: This will initiate system-level uninstalls.")
                confirm = input("Type 'YES' to proceed with full uninstall: ").strip()
                if confirm == "YES":
                    log_event("Uninstalled application via Admin menu.")
                    os.system("rm -f ~/.config/autostart/facegate.desktop")
                    print("Uninstall hooks completed. Terminating program.")
                    break

        elif choice == "10":
            print("Exiting Admin Tool.")
            break
        else:
            print("Invalid input.")

if __name__ == "__main__":
    main()
