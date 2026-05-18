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
    
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@patch('gitlab_webhooks.api.gitlab_projects.load_gitlab_projects')
def test_get_gitlab_projects(mock_load, client):
    mock_load.return_value = [{"url": "http://gitlab.com/project", "token": "secret"}]
    
    response = client.get('/api/gitlab-projects')
    
    assert response.status_code == 200
    assert response.json == [{"url": "http://gitlab.com/project", "token": "secret"}]
    mock_load.assert_called_once()

@patch('gitlab_webhooks.api.gitlab_projects.add_gitlab_project')
def test_create_gitlab_project_success(mock_add, client):
    response = client.post('/api/gitlab-projects', json={'url': 'http://gitlab.com/new', 'token': 'token123'})
    
    assert response.status_code == 201
    assert response.json == {'message': 'Project added: http://gitlab.com/new'}
    mock_add.assert_called_once_with('http://gitlab.com/new', 'token123')

@patch('gitlab_webhooks.api.gitlab_projects.add_gitlab_project')
def test_create_gitlab_project_missing_data(mock_add, client):
    response = client.post('/api/gitlab-projects', json={'url': 'http://gitlab.com/new'})
    
    assert response.status_code == 400
    assert response.json == {'error': 'Missing "url" or "token"'}
    mock_add.assert_not_called()

@patch('gitlab_webhooks.api.gitlab_projects.add_gitlab_project')
def test_create_gitlab_project_conflict(mock_add, client):
    mock_add.side_effect = ValueError("Project already exists")
    response = client.post('/api/gitlab-projects', json={'url': 'http://gitlab.com/new', 'token': 'token123'})
    
    assert response.status_code == 409
    assert response.json == {'error': 'Project already exists'}

@patch('gitlab_webhooks.api.gitlab_projects.update_gitlab_project')
def test_replace_gitlab_project_success(mock_update, client):
    response = client.put('/api/gitlab-projects', json={'url': 'http://gitlab.com/existing', 'token': 'new_token'})
    
    assert response.status_code == 200
    assert response.json == {'message': 'Project updated: http://gitlab.com/existing'}
    mock_update.assert_called_once_with('http://gitlab.com/existing', 'new_token')

@patch('gitlab_webhooks.api.gitlab_projects.update_gitlab_project')
def test_replace_gitlab_project_missing_data(mock_update, client):
    response = client.put('/api/gitlab-projects', json={'token': 'new_token'})
    
    assert response.status_code == 400
    assert response.json == {'error': 'Missing "url" or "token"'}
    mock_update.assert_not_called()

@patch('gitlab_webhooks.api.gitlab_projects.update_gitlab_project')
def test_replace_gitlab_project_not_found(mock_update, client):
    mock_update.side_effect = ValueError("Project not found")
    response = client.put('/api/gitlab-projects', json={'url': 'http://gitlab.com/missing', 'token': 'new_token'})
    
    assert response.status_code == 409
    assert response.json == {'error': 'Project not found'}

@patch('gitlab_webhooks.api.gitlab_projects.remove_gitlab_project')
def test_delete_gitlab_project_success(mock_remove, client):
    response = client.delete('/api/gitlab-projects', json={'url': 'http://gitlab.com/existing'})
    
    assert response.status_code == 200
    assert response.json == {'message': 'Project removed: http://gitlab.com/existing'}
    mock_remove.assert_called_once_with('http://gitlab.com/existing')

@patch('gitlab_webhooks.api.gitlab_projects.remove_gitlab_project')
def test_delete_gitlab_project_missing_data(mock_remove, client):
    response = client.delete('/api/gitlab-projects', json={})
    
    assert response.status_code == 400
    assert response.json == {'error': 'Missing "url"'}
    mock_remove.assert_not_called()

@patch('gitlab_webhooks.api.gitlab_projects.remove_gitlab_project')
def test_delete_gitlab_project_not_found(mock_remove, client):
    mock_remove.side_effect = ValueError("Project not found")
    response = client.delete('/api/gitlab-projects', json={'url': 'http://gitlab.com/missing'})
    
    assert response.status_code == 404
    assert response.json == {'error': 'Project not found'}

@patch('gitlab_webhooks.api.gitlab_projects.settings_manager.save_project_settings')
def test_link_to_a_table_success(mock_save, client):
    response = client.put('/api/gitlab-projects/settings', json={'url': 'http://gitlab.com/project', 'table_id': 'tbl123'})
    
    assert response.status_code == 201
    assert response.json == {'message': 'Project http://gitlab.com/project linked to the table tbl123'}
    mock_save.assert_called_once_with({
        "projectURL": "http://gitlab.com/project",
        "tableID": "tbl123",
        "links": []
    })

@patch('gitlab_webhooks.api.gitlab_projects.settings_manager.save_project_settings')
def test_link_to_a_table_missing_data(mock_save, client):
    response = client.put('/api/gitlab-projects/settings', json={'url': 'http://gitlab.com/project'})
    
    assert response.status_code == 400
    assert response.json == {'error': 'Missing "url" or "table_id"'}
    mock_save.assert_not_called()

@patch('gitlab_webhooks.api.gitlab_projects.settings_manager.save_project_settings')
def test_link_to_a_table_error(mock_save, client):
    mock_save.side_effect = ValueError("Duplicate setting")
    response = client.put('/api/gitlab-projects/settings', json={'url': 'http://gitlab.com/project', 'table_id': 'tbl123'})
    
    assert response.status_code == 409
    assert response.json == {'error': 'Duplicate setting'}
