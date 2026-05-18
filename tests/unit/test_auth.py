import os
import json
import pytest
from pathlib import Path
from auth import Auth

# We use a fixture to create a temporary auth.json file for testing.
@pytest.fixture
def auth_file(tmp_path):
    filepath = tmp_path / "test_auth.json"
    return filepath

@pytest.fixture
def auth_instance(auth_file):
    return Auth(filepath=auth_file)

def test_init_creates_new_file(auth_file):
    assert not auth_file.exists()
    auth = Auth(filepath=auth_file)
    assert auth_file.exists()
    assert auth.auth == {}

def test_init_loads_existing_file(auth_file):
    initial_data = {"testuser": {"salt": "testsalt", "hash": "testhash", "size": 32}}
    with open(auth_file, "w") as f:
        json.dump(initial_data, f)
    
    auth = Auth(filepath=auth_file)
    assert auth.auth == initial_data

def test_add_user(auth_instance):
    secret = auth_instance.add("newuser", size=32)
    assert secret != ""
    assert "newuser" in auth_instance.auth
    assert "salt" in auth_instance.auth["newuser"]
    assert "hash" in auth_instance.auth["newuser"]
    assert auth_instance.auth["newuser"]["size"] == 32

def test_add_existing_user(auth_instance):
    auth_instance.add("existinguser", size=32)
    # Trying to add the same user should return empty string (or raise ValueError in api_add)
    secret = auth_instance.add("existinguser", size=32)
    assert secret == ""

def test_add_small_size(auth_instance):
    secret = auth_instance.add("smalluser", size=16)
    assert secret == ""
    assert "smalluser" not in auth_instance.auth

def test_check_valid_credentials(auth_instance):
    secret = auth_instance.add("validuser", size=32)
    assert auth_instance.check("validuser", secret) is True

def test_check_invalid_secret(auth_instance):
    auth_instance.add("validuser", size=32)
    assert auth_instance.check("validuser", "wrongsecret") is False

def test_check_invalid_user(auth_instance):
    assert auth_instance.check("unknownuser", "somesecret") is False

def test_check_none_credentials(auth_instance):
    assert auth_instance.check(None, "somesecret") is False
    assert auth_instance.check("validuser", None) is False

def test_api_add_user(auth_instance):
    secret = auth_instance.api_add("apiuser", size=32)
    assert secret != ""
    assert "apiuser" in auth_instance.auth
    assert auth_instance.check("apiuser", secret) is True

def test_api_add_existing_user(auth_instance):
    auth_instance.api_add("apiuser", size=32)
    with pytest.raises(ValueError, match="User 'apiuser' already exists."):
        auth_instance.api_add("apiuser", size=32)

def test_api_add_small_size(auth_instance):
    with pytest.raises(ValueError, match="Size must be >= 32."):
        auth_instance.api_add("smalluser", size=16)

def test_delete_user(auth_instance):
    auth_instance.add("todelete", size=32)
    assert "todelete" in auth_instance.auth
    
    result = auth_instance.delete_user("todelete")
    assert result is True
    assert "todelete" not in auth_instance.auth

def test_delete_nonexistent_user(auth_instance):
    result = auth_instance.delete_user("nonexistent")
    assert result is False

def test_api_delete_user(auth_instance):
    auth_instance.add("todelete_api", size=32)
    result = auth_instance.api_delete_user("todelete_api")
    assert result == "User '{user_name}' deleted"
    assert "todelete_api" not in auth_instance.auth

def test_api_delete_nonexistent_user(auth_instance):
    result = auth_instance.api_delete_user("nonexistent")
    assert result == "'nonexistent' not found."

def test_api_users_list(auth_instance):
    auth_instance.add("user1", size=32)
    auth_instance.add("user2", size=32)
    users = auth_instance.api_users_list()
    assert "user1" in users
    assert "user2" in users
    assert len(users) == 2
