# api/auth_data.py

from flask import request, jsonify
from . import api_bp
from auth import Auth
from pathlib import Path


auth_file_path = Path(__file__).resolve().parent.parent.parent / "auth" / "data" / "auth.json"

@api_bp.route('/auth-data', methods=['GET'])
def get_auth_data():
    authentication= Auth(auth_file_path)
    return authentication.api_users_list()


@api_bp.route('/auth-data', methods=['DELETE'])
def delete_auth_data():
    name = request.args.get('name')
    authentication= Auth(auth_file_path)
    if (authentication.api_delete_user(name)):
        return jsonify({'message': f'{name} deleted'}), 200
    return jsonify({'error': f'{name} not found'}), 404


@api_bp.route('/auth-data', methods=['POST'])
def add_auth_data():
    data = request.get_json()
    user_name = data.get('user_name')
    size = data.get('size', 32) 
    authentication = Auth(auth_file_path)
    try:
        secret = authentication.api_add(user_name, int(size))
        return jsonify({'secret': secret}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 409

