#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def load_projects(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        data = json.load(f) or {}
    return data.get("projects", {})

def save_projects(config_path: Path, projects: dict):
    with open(config_path, "w") as f:
        json.dump({"projects": projects}, f, indent=2)

def add_project(config_path: Path, url: str, token: str):
    projects = load_projects(config_path)
    if url in projects:
        raise ValueError(f"Project '{url}' already exists.")
    projects[url] = token
    save_projects(config_path, projects)

def remove_project(config_path: Path, url: str):
    projects = load_projects(config_path)
    if url not in projects:
        raise ValueError(f"Project '{url}' not found.")
    del projects[url]
    save_projects(config_path, projects)

def list_projects(config_path: Path):
    projects = load_projects(config_path)
    if not projects:
        print("No projects configured.")
    else:
        print("Configured projects:")
        for url, token in projects.items():
            print(f" - {url}: {token}")

def interactive_menu(config_path: Path):
    while True:
        print("\nChoose an action:")
        print("1) List projects")
        print("2) Add project")
        print("3) Remove project")
        print("4) Quit")
        choice = input("Enter choice [1-4]: ").strip()

        try:
            if choice == "1":
                list_projects(config_path)
            elif choice == "2":
                url = input("Enter GitLab project URL: ").strip()
                token = input("Enter API token: ").strip()
                add_project(config_path, url, token)
                print(f"✅ Added project {url}")
            elif choice == "3":
                url = input("Enter GitLab project URL to remove: ").strip()
                remove_project(config_path, url)
                print(f"🗑 Removed project {url}")
            elif choice == "4":
                print("Bye 👋")
                break
            else:
                print("Invalid choice, try again.")
        except Exception as e:
            print(f"⚠️ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage GitLab projects in projects.json")
    parser.add_argument("directory", help="Path to instance directory (must contain projects.json)")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    config_path = directory / "projects.json"

    if not directory.exists():
        print(f"❌ Directory {directory} does not exist.")
        return

    # ensure file exists
    if not config_path.exists():
        with open(config_path, "w") as f:
            json.dump({"projects": {}}, f, indent=2)

    interactive_menu(config_path)

if __name__ == "__main__":
    main()
