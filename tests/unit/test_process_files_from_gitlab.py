import pytest
import json
from unittest.mock import MagicMock, patch

from gitlab_webhooks.process_files_from_gitlab import process_special_files

@pytest.fixture
def mock_gitlab_project():
    project = MagicMock()
    file_mock = MagicMock()
    file_mock.decode.return_value = '{"key": "value"}'
    project.files.get.return_value = file_mock
    return project

@pytest.fixture
def mock_table():
    table = MagicMock()
    return table

@patch('gitlab_webhooks.process_files_from_gitlab.prepare_json.prepare_input')
def test_process_special_files_wrong_basename(mock_prepare, mock_gitlab_project, mock_table):
    result = process_special_files(
        operation='added',
        gitlab_project=mock_gitlab_project,
        projecturl='http://gitlab.com/test',
        ref='refs/heads/main',
        commit_before='abc',
        commit_after='def',
        dirname='data',
        basename='OTHER.json',
        table=mock_table
    )
    assert result is False
    mock_table.insert.assert_not_called()

@patch('gitlab_webhooks.process_files_from_gitlab.prepare_json.prepare_input')
def test_process_special_files_added(mock_prepare, mock_gitlab_project, mock_table):
    mock_prepare.return_value = {"prepared": "data"}
    
    result = process_special_files(
        operation='added',
        gitlab_project=mock_gitlab_project,
        projecturl='http://gitlab.com/test',
        ref='refs/heads/main',
        commit_before='abc',
        commit_after='def',
        dirname='data',
        basename='DATASET.json',
        table=mock_table
    )
    
    # Although added doesn't have an explicit return, it falls through to the 'return True' at the end of the method
    assert result is True
    
    # Check that prepare_input was called with the correct extra data
    mock_prepare.assert_called_once()
    called_args = mock_prepare.call_args
    assert called_args[0][0] == {"key": "value"}
    assert called_args[1]['extra']['URL'] == 'http://gitlab.com/test/-/tree/main/data'
    assert called_args[1]['extra']['status'] == 'current'
    assert called_args[1]['extra']['branch'] == 'main'
    
    # Check that insert was called
    mock_table.insert.assert_called_once_with({"prepared": "data"})

@patch('gitlab_webhooks.process_files_from_gitlab.prepare_json.prepare_input')
def test_process_special_files_modified_existing(mock_prepare, mock_gitlab_project, mock_table):
    mock_prepare.return_value = {"prepared": "data"}
    mock_table.list.return_value = {
        'list': [{'URL': 'http://gitlab.com/test/-/tree/main/data', 'CreatedAt': 'x', 'UpdatedAt': 'y', 'other': 'val'}]
    }
    
    result = process_special_files(
        operation='modified',
        gitlab_project=mock_gitlab_project,
        projecturl='http://gitlab.com/test',
        ref='refs/heads/main',
        commit_before='abc',
        commit_after='def',
        dirname='data',
        basename='DATASET.json',
        table=mock_table
    )
    
    assert result is True
    
    # Check that the old record was inserted with updated URL/status
    mock_table.insert.assert_called_once()
    inserted_old_record = mock_table.insert.call_args[0][0]
    assert inserted_old_record['URL'] == 'http://gitlab.com/test/-/tree/abc/data'
    assert inserted_old_record['status'] == 'replaced'
    assert inserted_old_record['branch'] == 'main'
    assert 'CreatedAt' not in inserted_old_record
    assert 'UpdatedAt' not in inserted_old_record
    
    # Check that the new record was updated
    mock_table.update.assert_called_once_with({"prepared": "data"})

@patch('gitlab_webhooks.process_files_from_gitlab.prepare_json.prepare_input')
def test_process_special_files_modified_not_existing(mock_prepare, mock_gitlab_project, mock_table):
    mock_prepare.return_value = {"prepared": "data"}
    mock_table.list.return_value = {'list': []}
    
    result = process_special_files(
        operation='modified',
        gitlab_project=mock_gitlab_project,
        projecturl='http://gitlab.com/test',
        ref='refs/heads/main',
        commit_before='abc',
        commit_after='def',
        dirname='data',
        basename='DATASET.json',
        table=mock_table
    )
    
    assert result is True
    
    # Insert should be called for the new entry instead of update
    mock_table.insert.assert_called_once_with({"prepared": "data"})
    mock_table.update.assert_not_called()
