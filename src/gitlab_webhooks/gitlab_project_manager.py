from pathlib import Path
import yaml

CONFIG_PATH = Path("/app/config/projects.yml")

def load_gitlab_projects():
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f) or {}

    return config.get("projects", {})


def save_gitlab_projects(projects: dict):
    config = {"projects": projects}
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


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


