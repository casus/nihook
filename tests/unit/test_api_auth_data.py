import os
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

# Set DEBUG to skip the authentication before_request hook during endpoint testing
os.environ["DEBUG"] = "True"

# Prevent file I/O errors during module import
with patch("builtins.open", MagicMock()):
    from gitlab_webhooks.api import api_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    
    # We yield the app in case we need it, but test_client is more useful
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('gitlab_webhooks.api.auth_data.Auth')
def test_get_auth_data(mock_auth_class, client):
    # Setup mock
    mock_auth_instance = MagicMock()
    mock_auth_instance.api_users_list.return_value = {"user1": {"salt": "...", "hash": "...", "size": 32}}
    mock_auth_class.return_value = mock_auth_instance

    # Make request
    response = client.get('/api/auth-data')

    assert response.status_code == 200
    assert response.json == {"user1": {"salt": "...", "hash": "...", "size": 32}}
    mock_auth_instance.api_users_list.assert_called_once()

@patch('gitlab_webhooks.api.auth_data.Auth')
def test_delete_auth_data_success(mock_auth_class, client):
    mock_auth_instance = MagicMock()
    # Assume True means successful deletion
    mock_auth_instance.api_delete_user.return_value = True
    mock_auth_class.return_value = mock_auth_instance

    response = client.delete('/api/auth-data?name=user1')

    assert response.status_code == 200
    assert response.json == {'message': 'user1 deleted'}
    mock_auth_instance.api_delete_user.assert_called_once_with('user1')

@patch('gitlab_webhooks.api.auth_data.Auth')
def test_delete_auth_data_missing_name(mock_auth_class, client):
    response = client.delete('/api/auth-data')

    assert response.status_code == 400
    assert response.json == {'error': 'Name parameter is required'}

@patch('gitlab_webhooks.api.auth_data.Auth')
def test_add_auth_data_success(mock_auth_class, client):
    mock_auth_instance = MagicMock()
    mock_auth_instance.api_add.return_value = "supersecret"
    mock_auth_class.return_value = mock_auth_instance

    response = client.post('/api/auth-data', json={'user_name': 'newuser', 'size': 64})

    assert response.status_code == 200
    assert response.json == {'secret': 'supersecret'}
    mock_auth_instance.api_add.assert_called_once_with('newuser', 64)

@patch('gitlab_webhooks.api.auth_data.Auth')
def test_add_auth_data_default_size(mock_auth_class, client):
    mock_auth_instance = MagicMock()
    mock_auth_instance.api_add.return_value = "supersecret"
    mock_auth_class.return_value = mock_auth_instance

    response = client.post('/api/auth-data', json={'user_name': 'newuser'})

    assert response.status_code == 200
    assert response.json == {'secret': 'supersecret'}
    mock_auth_instance.api_add.assert_called_once_with('newuser', 32)

@patch('gitlab_webhooks.api.auth_data.Auth')
def test_add_auth_data_conflict(mock_auth_class, client):
    mock_auth_instance = MagicMock()
    mock_auth_instance.api_add.side_effect = ValueError("User 'newuser' already exists.")
    mock_auth_class.return_value = mock_auth_instance

    response = client.post('/api/auth-data', json={'user_name': 'newuser', 'size': 64})

    assert response.status_code == 409
    assert response.json == {'error': "User 'newuser' already exists."}
