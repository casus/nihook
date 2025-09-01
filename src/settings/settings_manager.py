import os
import yaml

SETTINGS_FILE = 'settings.yaml'


def init_settings_file():
    """
    Create the settings.yaml file with an empty structure if it does not exist.
    Example structure:
    settings:
      - projectURL: Your-Project-URL
        tableID: Your-Project-Table-ID
        links: []
    """
    if not os.path.exists(SETTINGS_FILE):
        base_structure = {
            "settings": []
        }
        with open(SETTINGS_FILE, "w") as f:
            yaml.safe_dump(base_structure, f, sort_keys=False)
        print(f"Created new settings file: {SETTINGS_FILE}")
    else:
        print(f"Settings file already exists: {SETTINGS_FILE}")

def load_settings():
    """
    Load settings from the YAML file.
    Format:
    settings:
    - projectURL: Your-Project-URL
        tableID: Your-Project-Table-ID
        links:
        - ParentTableLinkFieldID: Parent-Table-Link-Field-ID-1a
          ParentTableChildKeyStorageFieldID: Parent-Table-Child-Key-Storage-Field-ID-1a
          ChildTableID: Child-Table-ID-1a
          ChildTableLinkFieldID: Child-Table-Link-Field-ID-1a
          AutomaticallyCreateChildRecords: True
        - ParentTableLinkFieldID: Parent-Table-Link-Field-ID-1b
          ParentTableChildKeyStorageFieldID: Parent-Table-Child-Key-Storage-Field-ID-1b
          ChildTableID: Child-Table-ID-1b
          ChildTableLinkFieldID: Child-Table-Link-Field-ID-1b
          AutomaticallyCreateChildRecords: False
    """
    with open(SETTINGS_FILE, 'r') as f:
        return yaml.safe_load(f)

def save_settings(settings):
    """
    Save settings to the YAML file.
    """
    with open(SETTINGS_FILE, 'w') as f:
        yaml.dump(settings, f)

def find_project_by_table_id(table_id):
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ File {SETTINGS_FILE} not found.")
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
        print(f"❌ File {SETTINGS_FILE} not found.")
        data = {"settings": []}

    existing_settings = find_project_by_table_id(table_id)

    # Remove existing settings for the same tableID
    if (not existing_settings):
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
    Save project settings to the YAML file.
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
        print(f"❌ File {SETTINGS_FILE} not found.")
        return []

    return data.get("settings", [])

init_settings_file()
