import os
import requests
import pytest

def test_add_auth_data(env_config):
    """Test creating a new auth user"""
    base_url = env_config["WEBHOOK_HOST"].rstrip('/')
    url = f"{base_url}/api/auth-data"
    payload = {
        "user_name": "integration_test_user",
        "size": 32
    }
    response = requests.post(url, json=payload)
    
    # Should be 200 OK or 409 if it already exists
    assert response.status_code in [200, 409], f"Unexpected status code: {response.status_code} - {response.text}"
    
    if response.status_code == 200:
        data = response.json()
        assert "secret" in data
        assert len(data["secret"]) > 0
    else:
        # If user already exists, we should probably delete it and try again to ensure a clean test
        assert "error" in response.json()

def test_get_auth_data(env_config):
    """Test retrieving all users"""
    base_url = env_config["WEBHOOK_HOST"].rstrip('/')
    url = f"{base_url}/api/auth-data"
    response = requests.get(url)
    
    assert response.status_code == 200, f"Unexpected status code: {response.status_code} - {response.text}"
    data = response.json()
    assert isinstance(data, dict)
    
    # We should have at least the integration_test_user we created (or already existed)
    assert "integration_test_user" in data, "integration_test_user not found in auth data"

def test_delete_auth_data(env_config):
    """Test deleting the auth user"""
    base_url = env_config["WEBHOOK_HOST"].rstrip('/')
    url = f"{base_url}/api/auth-data"
    params = {"name": "integration_test_user"}
    response = requests.delete(url, params=params)
    
    assert response.status_code == 200, f"Unexpected status code: {response.status_code} - {response.text}"
    data = response.json()
    assert "deleted" in data.get("message", "")

def test_delete_auth_data_not_found(env_config):
    """Test deleting a non-existent auth user"""
    base_url = env_config["WEBHOOK_HOST"].rstrip('/')
    url = f"{base_url}/api/auth-data"
    params = {"name": "non_existent_test_user_xyz"}
    response = requests.delete(url, params=params)
    
    assert response.status_code == 404, f"Unexpected status code: {response.status_code} - {response.text}"
    data = response.json()
    assert "not found" in data.get("error", "")

def test_add_auth_data_invalid_payload(env_config):
    """Test creating a new auth user with invalid payload"""
    base_url = env_config["WEBHOOK_HOST"].rstrip('/')
    url = f"{base_url}/api/auth-data"
    # Missing user_name
    payload = {
        "size": 32
    }
    response = requests.post(url, json=payload)
    
    # Depending on how the error is handled, it might be 409 or 500, but auth.py raises ValueError which returns 409
    assert response.status_code == 409, f"Unexpected status code: {response.status_code} - {response.text}"
    
def test_delete_auth_data_missing_name(env_config):
    """Test deleting the auth user without a name parameter"""
    base_url = env_config["WEBHOOK_HOST"].rstrip('/')
    url = f"{base_url}/api/auth-data"
    response = requests.delete(url)
    
    assert response.status_code == 400, f"Unexpected status code: {response.status_code} - {response.text}"
    data = response.json()
    assert "Name parameter is required" in data.get("error", "")
