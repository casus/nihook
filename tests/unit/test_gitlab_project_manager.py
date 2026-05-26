import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from gitlab_webhooks.gitlab_project_manager import (
    load_gitlab_projects,
    save_gitlab_projects,
    add_gitlab_project,
    update_gitlab_project,
    remove_gitlab_project,
    does_gitlab_project_exist
)

@patch('gitlab_webhooks.gitlab_project_manager.CONFIG_PATH')
def test_load_gitlab_projects_not_exists(mock_config_path):
    mock_config_path.exists.return_value = False
    
    projects = load_gitlab_projects()
    
    assert projects == {}
    mock_config_path.exists.assert_called_once()

@patch('gitlab_webhooks.gitlab_project_manager.CONFIG_PATH')
@patch('builtins.open', new_callable=mock_open, read_data='{"projects": {"http://gitlab.com/test": "token123"}}')
def test_load_gitlab_projects_exists(mock_file, mock_config_path):
    mock_config_path.exists.return_value = True
    
    projects = load_gitlab_projects()
    
    assert projects == {"http://gitlab.com/test": "token123"}
    mock_file.assert_called_once_with(mock_config_path, 'r')

@patch('gitlab_webhooks.gitlab_project_manager.CONFIG_PATH')
@patch('builtins.open', new_callable=mock_open)
def test_save_gitlab_projects(mock_file, mock_config_path):
    projects_to_save = {"http://gitlab.com/test": "token123"}
    
    save_gitlab_projects(projects_to_save)
    
    mock_file.assert_called_once_with(mock_config_path, 'w')
    
    # Get the written content by joining all the write() calls
    written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
    assert json.loads(written_data) == {"projects": projects_to_save}

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
@patch('gitlab_webhooks.gitlab_project_manager.save_gitlab_projects')
def test_add_gitlab_project_success(mock_save, mock_load):
    mock_load.return_value = {}
    
    add_gitlab_project("http://gitlab.com/new", "new_token")
    
    mock_save.assert_called_once_with({"http://gitlab.com/new": "new_token"})

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
@patch('gitlab_webhooks.gitlab_project_manager.save_gitlab_projects')
def test_add_gitlab_project_conflict(mock_save, mock_load):
    mock_load.return_value = {"http://gitlab.com/existing": "token123"}
    
    with pytest.raises(ValueError, match="already exists"):
        add_gitlab_project("http://gitlab.com/existing", "new_token")
        
    mock_save.assert_not_called()

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
@patch('gitlab_webhooks.gitlab_project_manager.save_gitlab_projects')
def test_update_gitlab_project_success(mock_save, mock_load):
    mock_load.return_value = {"http://gitlab.com/existing": "token123"}
    
    update_gitlab_project("http://gitlab.com/existing", "updated_token")
    
    mock_save.assert_called_once_with({"http://gitlab.com/existing": "updated_token"})

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
@patch('gitlab_webhooks.gitlab_project_manager.save_gitlab_projects')
def test_update_gitlab_project_not_found(mock_save, mock_load):
    mock_load.return_value = {}
    
    with pytest.raises(ValueError, match="not found"):
        update_gitlab_project("http://gitlab.com/missing", "updated_token")
        
    mock_save.assert_not_called()

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
@patch('gitlab_webhooks.gitlab_project_manager.save_gitlab_projects')
def test_remove_gitlab_project_success(mock_save, mock_load):
    mock_load.return_value = {"http://gitlab.com/existing": "token123", "other": "token"}
    
    remove_gitlab_project("http://gitlab.com/existing")
    
    mock_save.assert_called_once_with({"other": "token"})

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
@patch('gitlab_webhooks.gitlab_project_manager.save_gitlab_projects')
def test_remove_gitlab_project_not_found(mock_save, mock_load):
    mock_load.return_value = {}
    
    with pytest.raises(ValueError, match="not found"):
        remove_gitlab_project("http://gitlab.com/missing")
        
    mock_save.assert_not_called()

@patch('gitlab_webhooks.gitlab_project_manager.load_gitlab_projects')
def test_does_gitlab_project_exist(mock_load):
    mock_load.return_value = {"http://gitlab.com/existing": "token123"}
    
    assert does_gitlab_project_exist("http://gitlab.com/existing") is True
    assert does_gitlab_project_exist("http://gitlab.com/missing") is False
