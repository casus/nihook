

import os

def test_dummy():
    assert True

def test_gitlab_env_variables_passed():
    # This checks whether standard GitLab CI environment variables are available
    assert os.getenv("CI") == "true", "CI environment variable is not 'true'"
    assert "CI_JOB_ID" in os.environ, "CI_JOB_ID environment variable is missing"
    assert "NOCODB_HOST" in os.environ, "NOCODB_HOST environment variable is missing"
    assert "WEBHOOK_HOST" in os.environ, "WEBHOOK_HOST environment variable is missing"
    assert "NOCODB_TOKEN" in os.environ, "NOCODB_TOKEN environment variable is missing"
