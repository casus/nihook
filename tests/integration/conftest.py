import os
import pytest

@pytest.fixture(scope="session")
def env_config():
    """
    Fixture to load environment variables defined in .gitlab-ci.yml for integration tests.
    Returns a dictionary of the configuration.
    """
    return {
        "PUBLIC_URL": os.getenv("PUBLIC_URL", "127.0.0.1"),
        "HOOK_HOST": os.getenv("HOOK_HOST", "0.0.0.0"),
        "HOOK_PORT": os.getenv("HOOK_PORT", "5000"),
        "NOCODB_PORT": os.getenv("NOCODB_PORT", "8080"),
        "NOCODB_SSL_CERT": os.getenv("NOCODB_SSL_CERT", "false"),
        "DEBUG": os.getenv("DEBUG", "True"),
        "NOCODB_HOST": os.getenv("NOCODB_HOST", "http://127.0.0.1:8080"),
        "WEBHOOK_HOST": os.getenv("WEBHOOK_HOST", "http://127.0.0.1:5000"),
        "NOCODB_TOKEN": os.getenv("NOCODB_TOKEN", ""),
    }
