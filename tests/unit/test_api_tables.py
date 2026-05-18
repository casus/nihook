import os
import io
import json
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

# Set DEBUG to skip the authentication before_request hook during endpoint testing
os.environ["DEBUG"] = "True"

with patch("builtins.open", MagicMock()):
    from gitlab_webhooks.api import api_bp
    from gitlab_webhooks.api.tables import parse_link_field

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

# --- Unit tests for parse_link_field ---

def test_parse_link_field_empty():
    assert parse_link_field(None) == []
    assert parse_link_field("") == []

def test_parse_link_field_list():
    assert parse_link_field([1, "two", 3.0]) == ["1", "two", "3.0"]

def test_parse_link_field_numbers():
    assert parse_link_field(123) == ["123"]
    assert parse_link_field(45.67) == ["45.67"]

def test_parse_link_field_eval_list():
    assert parse_link_field("[1, 2, 3]") == ["1", "2", "3"]
    assert parse_link_field("['a', 'b']") == ["a", "b"]

def test_parse_link_field_comma_separated():
    assert parse_link_field("a, b, c") == ["a", "b", "c"]
    assert parse_link_field("1,2") == ["1", "2"]

def test_parse_link_field_single_string():
    assert parse_link_field("single") == ["single"]

# --- Unit tests for /create-table-file endpoint ---

@patch('gitlab_webhooks.api.tables.NOCODB_TOKEN', 'fake-token')
@patch('gitlab_webhooks.api.tables.table_from_schema.create_new_table_from_schema')
def test_create_table_file_success(mock_create_table, client):
    mock_create_table.return_value = "table123"
    
    data = {
        'table_name': 'NewTable',
        'base_id': 'base123',
        'schema': (io.BytesIO(b'{"columns": []}'), 'schema.json')
    }
    
    response = client.post('/api/create-table-file', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 201
    assert response.json['table'] == 'table123'
    assert response.json['message'] == 'Table created successfully'

@patch('gitlab_webhooks.api.tables.NOCODB_TOKEN', 'fake-token')
def test_create_table_file_missing_inputs(client):
    response = client.post('/api/create-table-file', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "Missing 'table_name' and 'schema' file" in response.json['error']

@patch('gitlab_webhooks.api.tables.NOCODB_TOKEN', 'fake-token')
def test_create_table_file_invalid_json(client):
    data = {
        'table_name': 'NewTable',
        'base_id': 'base123',
        'schema': (io.BytesIO(b'invalid json'), 'schema.json')
    }
    response = client.post('/api/create-table-file', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "Invalid JSON format" in response.json['error']

# --- Unit tests for /link-tables endpoint ---

@patch('gitlab_webhooks.api.tables.NOCODB_TOKEN', 'fake-token')
@patch('gitlab_webhooks.api.tables.nocodb.Table')
@patch('gitlab_webhooks.api.tables.link_records_between_tables')
@patch('gitlab_webhooks.api.tables.settings_manager.save_relationship_settings')
def test_link_tables_success(mock_save_settings, mock_link_records, mock_nocodb_table, client):
    mock_parent_table = MagicMock()
    mock_parent_table.read_table.return_value = {"columns": [{"id": "field_p", "title": "parent_field"}]}
    
    mock_child_table = MagicMock()
    mock_child_table.read_table.return_value = {"columns": [{"id": "field_c", "title": "child_field"}]}
    
    mock_nocodb_table.side_effect = [mock_parent_table, mock_child_table]
    mock_link_records.return_value = 5
    
    payload = {
        "parent_table_id": "tbl_parent",
        "child_table_id": "tbl_child",
        "parent_field_name": "parent_field",
        "child_field_name": "child_field",
        "field_link": "existing_link",
        "connection": "mm",
        "save_settings": False
    }
    
    # We must patch parent_table_meta to return columnsById for connection type extraction
    mock_parent_table.read_table.return_value = {
        "columns": [{"id": "field_p", "title": "parent_field"}],
        "columnsById": {"existing_link": {"colOptions": {"type": "mm"}}}
    }
    
    response = client.post('/api/link-tables', json=payload)
    
    assert response.status_code == 200
    assert response.json['message'] == "Records linked successfully"
    assert response.json['records_updated'] == 5
    assert response.json['linked_field'] == "existing_link"

@patch('gitlab_webhooks.api.tables.NOCODB_TOKEN', 'fake-token')
def test_link_tables_missing_fields(client):
    payload = {
        "parent_table_id": "tbl_parent"
        # missing other fields
    }
    response = client.post('/api/link-tables', json=payload)
    assert response.status_code == 400
    assert "Missing required fields" in response.json['error']

# --- Unit tests for /analyze-unique-values endpoint ---

@patch('gitlab_webhooks.api.tables.settings_manager.get_all_projects')
@patch('gitlab_webhooks.api.tables.nocodb.Table')
def test_analyze_unique_values_success(mock_nocodb_table, mock_get_projects, client):
    mock_get_projects.return_value = [
        {"projectURL": "http://git.local/proj", "tableID": "tbl123", "links": []}
    ]
    
    mock_table = MagicMock()
    mock_table.read_table.return_value = {"columnsById": {}}
    mock_table.list_all_records.return_value = {
        "list": [
            {"col1": "A", "col2": "Same"},
            {"col1": "B", "col2": "Same"}
        ]
    }
    mock_nocodb_table.return_value = mock_table
    
    payload = {
        "project_urls": ["http://git.local/proj"],
        "minimum_unique_values": 1,
        "maximum_unique_values": 5
    }
    
    response = client.post('/api/analyze-unique-values', json=payload)
    
    assert response.status_code == 200
    assert "http://git.local/proj" in response.json
    assert response.json["http://git.local/proj"]["col1"] == 2
    assert response.json["http://git.local/proj"]["col2"] == 1

# --- Unit tests for /normalize-columns endpoint ---

def test_normalize_columns_missing_data(client):
    response = client.post('/api/normalize-columns', json={})
    assert response.status_code == 400
    assert "No projects or columns provided" in response.json['error']
