from flask import request, jsonify
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
    projects = load_gitlab_projects()
    return jsonify(projects), 200


@api_bp.route('/gitlab-projects', methods=['POST'])
def create_gitlab_project():
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
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'Missing "url"'}), 400

    try:
        remove_gitlab_project(url)
        return jsonify({'message': f'Project removed: {url}'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404