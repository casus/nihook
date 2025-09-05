import os
import json

from const import SETTINGS_FILE_PATH


def init_settings_file():
    """
    Create the settings.json file with an empty structure if it does not exist.
    Example structure:
    {
        "settings": []
    }
    """
    if not os.path.exists(SETTINGS_FILE_PATH):
        base_structure = {
            "settings": []
        }
        with open(SETTINGS_FILE_PATH, "w") as f:
            json.dump(base_structure, f, indent=2)
        print(f"Created new settings file: {SETTINGS_FILE_PATH}")
    else:
        print(f"Settings file already exists: {SETTINGS_FILE_PATH}")

def load_settings():
    """
    Load settings from the JSON file.
    Format:
    {
        "settings": [
            {
                "projectURL": "Your-Project-URL",
                "tableID": "Your-Project-Table-ID",
                "links": [
                    {
                        "ParentTableLinkFieldID": "...",
                        "ParentTableChildKeyStorageFieldID": "...",
                        "ChildTableID": "...",
                        "ChildTableLinkFieldID": "...",
                        "AutomaticallyCreateChildRecords": true
                    }
                ]
            }
        ]
    }
    """
    with open(SETTINGS_FILE_PATH, 'r') as f:
        return json.load(f)

def save_settings(settings):
    """
    Save settings to the JSON file.
    """
    with open(SETTINGS_FILE_PATH, 'w') as f:
        json.dump(settings, f, indent=2)

def find_project_by_table_id(table_id):
    try:
        with open(SETTINGS_FILE_PATH, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File {SETTINGS_FILE_PATH} not found.")
        return None

    settings = data.get("settings", [])
    for project in settings:
        if project.get("tableID") == table_id:
            return project

    return None


def save_relationship_settings(settings, table_id):
    try:
        data = load_settings()
    except FileNotFoundError:
        print(f"❌ File {SETTINGS_FILE_PATH} not found.")
        data = {"settings": []}

    existing_settings = find_project_by_table_id(table_id)

    # Remove existing settings for the same tableID
    if not existing_settings:
        raise ValueError(f"Project with tableID {table_id} not found.")

    if existing_settings.get("links") is None:
        existing_settings["links"] = []
    # Add new settings
    existing_settings["links"].append(settings)

    # Replace the existing project settings with the updated one
    for idx, project in enumerate(data.get("settings", [])):
        if project.get("tableID") == existing_settings.get("tableID"):
            data["settings"][idx] = existing_settings
            break

    save_settings(data)


def save_project_settings(project_settings):
    """
    Save project settings to the JSON file.
    """
    data = load_settings()

    # Check if the project already exists
    for project in data["settings"]:
        if project.get("projectURL") == project_settings.get("projectURL"):
            # Update existing project settings
            project.update(project_settings)
            break
    else:
        # Add new project settings
        data["settings"].append(project_settings)

    save_settings(data)


def get_all_projects():
    """
    Get all projects from the settings file.
    """
    try:
        data = load_settings()
    except FileNotFoundError:
        print(f"❌ File {SETTINGS_FILE_PATH} not found.")
        return []

    return data.get("settings", [])

init_settings_file()
