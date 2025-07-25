# api/__init__.py

import os
from flask import Blueprint
from pathlib import Path

api_bp = Blueprint('api', __name__, url_prefix='/api')

auth_file_path = Path(__file__).resolve().parent.parent.parent / "auth" / "data" / "auth.json"

debug_mode = os.getenv("DEBUG", "False")
DEBUG_MODE = False if debug_mode == "False" else True

@api_bp.before_request
def authenticate():
    from flask import request, jsonify
    from auth import Auth

    if (not DEBUG_MODE):
        authentication= Auth(auth_file_path)
        user = request.headers.get('X-Webhook-User')
        secret = request.headers.get('X-Webhook-Secret')

        if not authentication.check(user, secret):
            return jsonify({'error': 'authentication failed'}), 401


# Import modules to register routes
from . import auth_data, gitlab_projects, tables # routes will attach to `api_bp`
