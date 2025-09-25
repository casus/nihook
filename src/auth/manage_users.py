#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from auth import Auth  

USER_BASE_DIR = Path(__file__).resolve().parent
# CONTAINER_ID = str(int(time.time()))

USER_FILE = ""

# Load existing users
def load_users():
    if USER_FILE.exists():
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return []

# Save users to file
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)


# Main loop
def main():
    # users = load_users()

    if len(sys.argv) < 2:
        print("❌ Please provide the container folder path as an argument.")
        sys.exit(1)

    container_path = Path(sys.argv[1])
    if not container_path.exists():
        print(f"❌ Directory '{container_path}' not found.")
        sys.exit(1)

    USER_FILE = container_path / "auth.json"    
    auth = Auth(filename=str(USER_FILE))

    while True:
        print("🛠️  User Management Menu")
        print("------------------------")
        print("1) Add a new user")
        print("2) Delete existing user")
        print("3) List users")
        print("4) Exit")
        choice = input("Choose an option [1-4]: ").strip()

        if choice == "1":
            name = input("👤 Enter new username: ").strip()
            size_input = input("🔐 Enter secret size (default 32): ").strip()
            size = int(size_input) if size_input.isdigit() else 32

            secret = auth.add(name, size)
            if secret:
                print(f"✅ User '{name}' added with secret:\n{secret}\n")
            else:
                print("❌ Failed to add user.")
        elif choice == "2":
            auth.list_users()
            name = input("🗑️  Enter username to delete: ").strip()
            auth.delete_user(name)
        elif choice == "3":
            auth.list_users()
        elif choice == "4":
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice.\n")
    print(f"\n📁 User data saved in: {USER_FILE}")

if __name__ == "__main__":
    main()
