import json
import os
from flask import Flask, request, jsonify
from nocodb_client import nocodb, table_from_schema
from . import api_bp

NOCODB_PORT = os.getenv('NOCODB_PORT', '8080')
NOCODB_HOST = f"http://localhost:{NOCODB_PORT}"
NOCODB_TOKEN = os.getenv('NOCODB_TOKEN', None)


@api_bp.route("/create-table-file", methods=["POST"])
def create_table_file():
    # Get form data
    table_name = request.form.get("table_name")
    base_id = request.form.get("base_id")
    new_base_name = request.form.get("new_base_name")
    schema_file = request.files.get("schema")

    # Validate input
    if not table_name or not schema_file:
        return jsonify({"error": "Missing 'table_name' or 'schema' file"}), 400

    try:
        schema = json.load(schema_file)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in schema file"}), 400

    try:
        # Auth headers and NocoDB URL from env
        nocodb_ssl_cert = request.headers.get("X-Webhook-Nocodbssl") == "true"

        if not NOCODB_TOKEN:
            return jsonify({"error": "Missing Nocodb Token"}), 400

        # Initialize base handler
        # base_client = nocodb.Base(host=NOCODB_HOST, auth_token=nocodb_token, verify=nocodb_ssl_cert)

        # If new_base_name is provided, create a new base
        if new_base_name:
            new_base = nocodb.Nocodb(NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=nocodb_ssl_cert).create_base(new_base_name)
            if not new_base:
                return jsonify({"error": f"Failed to create new base '{new_base_name}'"}), 500
            base_id = new_base["id"]
        elif not base_id:
            return jsonify({"error": "Provide either 'base_id' or 'new_base_name'"}), 400
        

        # Now create the table in the selected base
        created_table_id = table_from_schema.create_new_table_from_schema(
            nocodb_host=NOCODB_HOST,
            nocodb_token=NOCODB_TOKEN,
            nocodb_ssl_cert=nocodb_ssl_cert,
            base_id=base_id,
            table_name=table_name,
            schema=schema
        )

        return jsonify({
            "message": "Table created successfully",
            "table": created_table_id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    