from flask import request, jsonify

import settings_manager
from . import api_bp
from auth import Auth
from pathlib import Path
from gitlab_project_manager import (
    load_gitlab_projects,
    add_gitlab_project,
    remove_gitlab_project
)


@api_bp.route('/gitlab-projects', methods=['GET'])
def get_gitlab_projects():
    """
    Route in order to retrieve all GitLab projects.
    This will return a list of projects with their URLs and tokens.
    """
    projects = load_gitlab_projects()
    return jsonify(projects), 200


@api_bp.route('/gitlab-projects', methods=['POST'])
def create_gitlab_project():
    """
    Route in order to add a new GitLab project.
    It expects a JSON payload with 'url' and 'token'.
    If the project already exists, it will return a 409 Conflict error.
    """
    data = request.get_json()
    url = data.get('url')
    token = data.get('token')

    if not url or not token:
        return jsonify({'error': 'Missing "url" or "token"'}), 400
    try:
        add_gitlab_project(url, token)
        return jsonify({'message': f'Project added: {url}'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409


@api_bp.route('/gitlab-projects', methods=['DELETE'])
def delete_gitlab_project():
    """
    Route in order to remove a GitLab project.
    It expects a JSON payload with 'url'.
    """
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'Missing "url"'}), 400

    try:
        remove_gitlab_project(url)
        return jsonify({'message': f'Project removed: {url}'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    

@api_bp.route('/gitlab-projects/settings', methods=['PUT'])
def link_to_a_table():
    """
    Route in order to save new GitLab project and table pair in the settings file.
    It expects a JSON payload with 'url' and 'table_id'.
    """
    data = request.get_json()
    url = data.get('url')
    table_id = data.get('table_id')

    if not url or not table_id:
        return jsonify({'error': 'Missing "url" or "table_id"'}), 400
    try:
        settings_manager.save_project_settings({
            "projectURL": url,
            "tableID": table_id,
            "links": []
        })
        return jsonify({'message': f'Project {url} linked to the table {table_id}'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409