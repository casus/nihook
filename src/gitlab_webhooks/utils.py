import os

# Get environment variables
HOST = os.getenv('HOOK_HOST', '127.0.0.1')
PORT = os.getenv('HOOK_PORT', '5000')
NOCODB_HOST = f"http://localhost:{os.getenv('NOCODB_PORT', '8080')}"
NOCODB_TOKEN = os.getenv('NOCODB_TOKEN', None)
NOCODB_SSL_CERT = os.getenv('NOCODB_SSL_CERT', True) # optional
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')