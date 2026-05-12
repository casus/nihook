# api/auth_data.py

from flask import request, jsonify
from . import api_bp
from auth import Auth # type: ignore
from const import AUTH_FILE_PATH

@api_bp.route('/auth-data', methods=['GET'])
def get_auth_data():
    """
    Route to retrieve all the users data.
    """
    authentication= Auth(AUTH_FILE_PATH)
    return authentication.api_users_list()


@api_bp.route('/auth-data', methods=['DELETE'])
def delete_auth_data():
    """
    Route to delete a user by name.
    It expects a query parameter 'name'.
    """
    name = request.args.get('name')
    authentication= Auth(AUTH_FILE_PATH)
    if not name:
        return jsonify({'error': 'Name parameter is required'}), 400
    if (authentication.api_delete_user(name)):
        return jsonify({'message': f'{name} deleted'}), 200
    return jsonify({'error': f'{name} not found'}), 404


@api_bp.route('/auth-data', methods=['POST'])
def add_auth_data():
    """
    Route to add a new user.
    It expects a JSON payload with 'user_name' and optional 'size'.
    If 'size' is not provided, it defaults to 32.
    """
    data = request.get_json()
    user_name = data.get('user_name')
    size = data.get('size', 32) 
    authentication = Auth(AUTH_FILE_PATH)
    try:
        secret = authentication.api_add(user_name, int(size))
        return jsonify({'secret': secret}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 409

