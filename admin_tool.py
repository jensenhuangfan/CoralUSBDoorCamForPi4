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
    print("1. Re-run Configuration Wizard")
    print("2. Uninstall Application")
    print("3. Exit")
    
    choice = input("Select an option (1-3): ").strip()
    
    if choice == "1":
        log_event("Triggered re-configuration wizard.")
        print("Launching setup_app.py...")
        subprocess.run(["python3", "setup_app.py"])
    elif choice == "2":
        confirm = input("Are you absolutely sure you want to uninstall and delete Face Gate? (YES/no): ")
        if confirm == "YES":
            log_event("Uninstalled application.")
            print("Removing autostart entry...")
            os.system("rm -f ~/.config/autostart/facegate.desktop")
            print("Note: To fully delete files, you must delete this directory manually or run: rm -rf " + os.getcwd())
            print("Uninstall tasks completed.")
        else:
            print("Uninstall cancelled.")
    else:
        print("Exiting.")

if __name__ == "__main__":
    main()