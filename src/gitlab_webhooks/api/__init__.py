# api/__init__.py

import os
from flask import Blueprint
from pathlib import Path
from const import HEADER_WEBHOOK_USERNAME, HEADER_WEBHOOK_SECRET

api_bp = Blueprint('api', __name__, url_prefix='/api')

auth_file_path = Path(__file__).resolve().parent.parent.parent / "auth" / "data" / "auth.json"

DEBUG_MODE = True if os.getenv("DEBUG", "False") == "True" else False

@api_bp.before_request
def authenticate():
    """
    Middleware to authenticate requests.
    If DEBUG_MODE is True, it skips authentication.
    Otherwise, it checks the user and secret from headers against the auth data.
    """
    from flask import request, jsonify
    from auth import Auth

    if (not DEBUG_MODE):
        authentication= Auth(auth_file_path)
        user = request.headers.get(HEADER_WEBHOOK_USERNAME)
        secret = request.headers.get(HEADER_WEBHOOK_SECRET)
        print("USER: ", user)
        print("SECRET: ", secret)
        print("Using auth file at:", auth_file_path)
        print("Auth file content preview:", auth_file_path.read_text()[:200])

        if not authentication.check(user, secret):
            return jsonify({'error': 'authentication failed'}), 401


# Import modules to register routes
from . import auth_data, gitlab_projects, tables # routes will attach to `api_bp`
