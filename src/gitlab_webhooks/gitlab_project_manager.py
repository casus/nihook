from pathlib import Path
import json

from const import CONFIG_PATH
def load_gitlab_projects():
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f) or {}

    return config["projects"]


def save_gitlab_projects(projects: dict):
    config = {"projects": projects}
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)


def add_gitlab_project(url: str, token: str):
    projects = load_gitlab_projects()
    if url in projects:
        raise ValueError(f"Project '{url}' already exists.")

    projects[url] = token
    save_gitlab_projects(projects)


def remove_gitlab_project(url: str):
    projects = load_gitlab_projects()
    if url not in projects:
        raise ValueError(f"Project '{url}' not found.")

    del projects[url]
    save_gitlab_projects(projects)

def does_gitlab_project_exist(url: str) -> bool:
    projects = load_gitlab_projects()
    return url in projects


