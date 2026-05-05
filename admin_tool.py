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
    print("\n[+] Configuration updated securely.")
    log_event("Updated config.json elements.")

def input_int(prompt, default, min_val, max_val):
    val = input(f"{prompt} [{default}]: ").strip()
    if not val: return default
    try:
        num = int(val)
        if min_val <= num <= max_val: return num
        print(f"Must be between {min_val} and {max_val}.")
    except: pass
    return default

def input_float(prompt, default, min_val, max_val):
    val = input(f"{prompt} [{default}]: ").strip()
    if not val: return default
    try:
        num = float(val)
        if min_val <= num <= max_val: return num
        print(f"Must be between {min_val} and {max_val}.")
    except: pass
    return default

def input_bool(prompt, default):
    val = input(f"{prompt} (y/n) [{'y' if default else 'n'}]: ").strip().lower()
    if not val: return default
    return val == 'y'

def menu_hardware(config):
    while True:
        print("\n--- 1. Camera & Hardware Configuration ---")
        print(f"1. Target Camera Type      [{config.get('camera_type', 'picam3')}]")
        print("0. Back to Main Menu")
        c = input("Select: ").strip()
        if c == '1':
            cam = input("1 for pi camera (libcamera), 2 for usbcam: ").strip()
            if cam == '1': config["camera_type"] = "picam3"
            elif cam == '2': config["camera_type"] = "usbcam"
            save_config(config)
        elif c == '0': break

def menu_audio_tts(config):
    while True:
        print("\n--- 2. Audio & Speech Configuration ---")
        print(f"1. Speech Voice Variant (e.g. m1-m7, f1-f5)   [{config.get('voice_variant', 'm1')}]")
        print(f"2. Speech Speed in WPM (60-400)               [{config.get('speech_speed', 150)}]")
        print(f"3. Speech Pitch (0-99)                        [{config.get('speech_pitch', 50)}]")
        print(f"4. Enable Whitelist Greetings (y/n)           [{config.get('enable_whitelist_greetings', True)}]")
        print(f"5. Enable Blacklist Warnings (y/n)            [{config.get('enable_blacklist_warnings', True)}]")
        print(f"6. Enable Intruder Alerts (y/n)               [{config.get('enable_intruder_alerts', True)}]")
        print(f"7. Base System Volume Percentage (0-100)      [{config.get('base_volume', 50)}]")
        print(f"8. Tamper Alarm Volume Percentage (0-100)     [{config.get('tamper_volume', 100)}]")
        print("0. Back to Main Menu")
        c = input("Select: ").strip()
        
        if c == '1': config['voice_variant'] = input(f"Voice (m1-m7, f1-f5) [{config.get('voice_variant', 'm1')}]: ") or config.get('voice_variant', 'm1')
        elif c == '2': config['speech_speed'] = input_int("Speed WPM", config.get('speech_speed', 150), 60, 400)
        elif c == '3': config['speech_pitch'] = input_int("Pitch", config.get('speech_pitch', 50), 0, 99)
        elif c == '4': config['enable_whitelist_greetings'] = input_bool("Play Whitelist Greetings?", config.get('enable_whitelist_greetings', True))
        elif c == '5': config['enable_blacklist_warnings'] = input_bool("Play Blacklist Warnings?", config.get('enable_blacklist_warnings', True))
        elif c == '6': config['enable_intruder_alerts'] = input_bool("Play Intruder Alerts?", config.get('enable_intruder_alerts', True))
        elif c == '7': config['base_volume'] = input_int("Base Volume %", config.get('base_volume', 50), 0, 100)
        elif c == '8': config['tamper_volume'] = input_int("Tamper Volume %", config.get('tamper_volume', 100), 0, 100)
        elif c == '0': break
        
        if c != '0': save_config(config)

def menu_ai_tuning(config):
    while True:
        print("\n--- 3. AI Recognition & Timers Tuning ---")
        print(f"1. Coral Face Detection Confidence Threshold    [{config.get('detection_threshold', 0.45)}]")
        print(f"2. Strictness/LBPH Distance Threshold            [{config.get('unknown_threshold', 115.0)}]")
        print(f"3. Intruder Alarm Cooldown (seconds)             [{config.get('intruder_cooldown', 3.0)}]")
        print(f"4. Welcome Greeting Cooldown (seconds)           [{config.get('welcome_cooldown', 8.0)}]")
        print("0. Back to Main Menu")
        c = input("Select: ").strip()
        
        if c == '1': config['detection_threshold'] = input_float("Detection Threshold", config.get('detection_threshold', 0.45), 0.1, 0.99)
        elif c == '2': config['unknown_threshold'] = input_float("LBPH Distance Limit", config.get('unknown_threshold', 115.0), 10.0, 250.0)
        elif c == '3': config['intruder_cooldown'] = input_float("Intruder Cooldown", config.get('intruder_cooldown', 3.0), 0.5, 60.0)
        elif c == '4': config['welcome_cooldown'] = input_float("Welcome Cooldown", config.get('welcome_cooldown', 8.0), 1.0, 300.0)
        elif c == '0': break
        
        if c != '0': save_config(config)

def menu_ui_display(config):
    while True:
        print("\n--- 4. UI Overlay & Display Options ---")
        print(f"1. Window Title String                   [{config.get('window_title', 'Coral Face Gate')}]")
        print(f"2. Force Fullscreen Kiosk Mode (y/n)     [{config.get('kiosk_fullscreen', True)}]")
        print(f"3. Draw Facial Bounding Boxes (y/n)      [{config.get('draw_boxes', True)}]")
        print(f"4. Draw Live Names above Boxes (y/n)     [{config.get('draw_names', True)}]")
        print("0. Back to Main Menu")
        c = input("Select: ").strip()
        
        if c == '1': config['window_title'] = input("Window Title: ").strip() or config.get('window_title', 'Coral Face Gate')
        elif c == '2': config['kiosk_fullscreen'] = input_bool("Fullscreen?", config.get('kiosk_fullscreen', True))
        elif c == '3': config['draw_boxes'] = input_bool("Draw Boxes?", config.get('draw_boxes', True))
        elif c == '4': config['draw_names'] = input_bool("Draw Names?", config.get('draw_names', True))
        elif c == '0': break
        
        if c != '0': save_config(config)

def main():
    if not Path("config.json").exists():
        print("Error: config.json not found. Please run ./setup.sh first.")
        return

    with open("config.json", "r") as f: config = json.load(f)

    print("\n--- Face Gate Enterprise Admin Terminal ---")
    pwd = getpass.getpass("Enter Admin Password: ")
    if hashlib.sha256(pwd.encode()).hexdigest() != config.get("password_hash"):
        print("Access Denied.")
        log_event("Failed admin login attempt.")
        return

    log_event("Successful admin login.")
    
    while True:
        print("\n=== Enterprise Admin Dashboard ===")
        print("1. Camera & Hardware Configuration")
        print("2. Audio & Speech Configuration (Volumes, Voices, TTS)")
        print("3. AI Recognition & Timers Tuning")
        print("4. UI Overlay & Display Options")
        print("5. Phrases & Greetings Customization")
        print("6. List Config (Labels, Blacklist enable)")
        print("7. Security (Logging & Password)")
        print("8. Check for Software Updates")
        print("9. Uninstall Application")
        print("0. Quit Admin Panel")
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1': menu_hardware(config)
        elif choice == '2': menu_audio_tts(config)
        elif choice == '3': menu_ai_tuning(config)
        elif choice == '4': menu_ui_display(config)
        elif choice == '5':
            print("\n[Phrases & Greetings]")
            print(f"1. Whitelist: {config.get('whitelist_greeting')}")
            print(f"2. Blacklist: {config.get('blacklist_greeting')}")
            print(f"3. Default:   {config.get('default_known_greeting')}")
            c = input("Edit which one (1-3) or 0 to go back: ").strip()
            if c == '1': config['whitelist_greeting'] = input("New: ").strip() or config['whitelist_greeting']
            elif c == '2': config['blacklist_greeting'] = input("New: ").strip() or config['blacklist_greeting']
            elif c == '3': config['default_known_greeting'] = input("New: ").strip() or config['default_known_greeting']
            save_config(config)
        elif choice == '6':
            print("\n[Lists & Labels]")
            print(f"1. Unknown Face Name Label [{config.get('unknown_label')}]")
            print(f"2. Enable Blacklist Folder [{config.get('has_blacklist', False)}]")
            c = input("Select (1-2) or 0: ").strip()
            if c == '1': 
                config['unknown_label'] = input("Label: ").strip() or config['unknown_label']
                save_config(config)
            elif c == '2':
                config['has_blacklist'] = input_bool("Enable Blacklist Directory?", config.get('has_blacklist', False))
                save_config(config)
        elif choice == '7':
            print("\n[Security Operations]")
            print("1. Change Admin Password")
            print("2. Toggle Output Logging")
            print("3. Change Target Log File")
            print("4. View Current Log File")
            c = input("Select (1-4) or 0: ").strip()
            if c == '1':
                new_pwd = getpass.getpass("Enter new password: ")
                if new_pwd == getpass.getpass("Confirm: ") and new_pwd:
                    config["password_hash"] = hashlib.sha256(new_pwd.encode()).hexdigest()
                    save_config(config)
            elif c == '2':
                config['enable_logging'] = input_bool("Enable Logging?", config.get('enable_logging', True))
                save_config(config)
            elif c == '3':
                config['log_file'] = input("Log file path: ").strip() or config.get('log_file', 'security_log.txt')
                save_config(config)
            elif c == '4':
                lf = config.get('log_file', 'security_log.txt')
                if Path(lf).exists(): os.system(f"tail -n 20 {lf}")
                else: print("Log file not found.")
        elif choice == '8':
            subprocess.run(["git", "pull", "origin", "main"])
        elif choice == '9':
            if input("Type 'YES' to totally uninstall: ").strip() == 'YES':
                os.system("rm -f ~/.config/autostart/facegate.desktop")
                print("Uninstall tasks queued. Directory can now be deleted.")
                break
        elif choice == '0':
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
