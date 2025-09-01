import json
import os
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from nocodb_client import nocodb, table_from_schema
import yaml
from . import api_bp
import ast
import gitlab
from const import HEADER_NOCO_DB_TABLE_ID, HEADER_WEBHOOK_USERNAME, HEADER_WEBHOOK_SECRET
import settings_manager
from utils import NOCODB_HOST, NOCODB_TOKEN, NOCODB_SSL_CERT, DEBUG


ID_COLUMN = {
    "ai": 1,
    "cdf": None,
    "ck": 0,
    "clen": None,
    "column_name": "id",
    "ct": "int(11)",
    "dt": "integer",
    "dtx": "integer",
    "dtxp": "",
    "dtxs": "",
    "np": None,
    "nrqd": 0,
    "ns": 0,
    "pk": 1,
    "rqd": 1,
    "title": "Id",
    "uicn": "",
    "uidt": "ID",
    "uip": "",
    "un": 0
}

COLUMN_METADATA_TO_COPY = ["uidt", "dt", "np", "ns", "clen", "cop", "pv", "un", "ct"]

def parse_link_field(value):
    if not value:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value]

    if isinstance(value, (int, float)):
        return [str(value)]

    value = str(value).strip()

    # Try to safely evaluate Python list syntax like "[6, 7]"
    if value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed]
        except Exception:
            pass  # fallback to manual split if eval fails

    # If it's a string with commas
    if "," in value:
        return [v.strip() for v in value.split(",") if v.strip()]
    else:
        return [value]  # single value



@api_bp.route("/create-table-file", methods=["POST"])
def create_table_file():
    """
    Create a new table in NocoDB from a schema file.
    Optionally, create a GitLab webhook for the given project.
    """
    # Get form data
    table_name = request.form.get("table_name")
    base_id = request.form.get("base_id")
    new_base_name = request.form.get("new_base_name")
    schema_file = request.files.get("schema")

    # Optional GitLab webhook params
    create_gitlab_webhook = request.form.get("create_gitlab_webhook", "").lower() == "true"
    gitlab_repo_url = request.form.get("gitlab_repo_url")
    gitlab_api_token = request.form.get("gitlab_api_token")
    webhook_secret = request.form.get("webhook_secret")  # optional
    webhook_username = request.form.get("webhook_username")  # optional
    server_ip = request.form.get("server_ip")  # where your webhook service is running

    store_settings = request.form.get("store_settings", "").lower() == "true" # optional, if you want to save the relationship settings in settings.yaml

    # Debug
    print("=== DEBUG ===")
    print("request.form:", request.form)
    print("request.files:", request.files)
    print("==============")

    # Validate table creation input
    if not table_name or not schema_file:
        if not table_name and not schema_file:
            return jsonify({"error": "Missing 'table_name' and 'schema' file"}), 400
        if not table_name:
            return jsonify({"error": "Missing 'table_name'"}), 400
        if not schema_file:
            return jsonify({"error": "Missing 'schema' file"}), 400

    try:
        schema = json.load(schema_file)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in schema file"}), 400

    try:
        if not NOCODB_TOKEN:
            return jsonify({"error": "Missing Nocodb Token"}), 400

        # If new_base_name is provided, create a new base
        if new_base_name:
            new_base = nocodb.Nocodb(
                NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT
            ).create_base(new_base_name)
            if not new_base:
                return jsonify({"error": f"Failed to create new base '{new_base_name}'"}), 500
            base_id = new_base["id"]
        elif not base_id:
            return jsonify({"error": "Provide either 'base_id' or 'new_base_name'"}), 400

        # Create the table
        created_table_id = table_from_schema.create_new_table_from_schema(
            nocodb_host=NOCODB_HOST,
            nocodb_token=NOCODB_TOKEN,
            nocodb_ssl_cert=NOCODB_SSL_CERT,
            base_id=base_id,
            table_name=table_name,
            schema=schema
        )
        if not created_table_id:
            return jsonify({"error": "Failed to create table"}), 500
        # Optional: create GitLab webhook
        webhook_info = None
        if create_gitlab_webhook:
            if not all([gitlab_repo_url, gitlab_api_token, server_ip]):
                return jsonify({"error": "Missing required parameters for GitLab webhook creation"}), 400
            if not webhook_username:
                webhook_username = request.headers.get(HEADER_WEBHOOK_USERNAME, None)  # use header if not provided
            if not webhook_secret:
                webhook_secret = request.headers.get(HEADER_WEBHOOK_SECRET, None)  # use header if not provided
            webhook_info = create_gitlab_project_webhook(
                repo_url=gitlab_repo_url,
                token=gitlab_api_token,
                webhook_secret=webhook_secret,
                nocodb_table_id=created_table_id,
                server_ip=server_ip,
                webhook_username=webhook_username
            )

        response = {
            "message": "Table created successfully",
            "table": created_table_id
        }
        if webhook_info:
            response["gitlab_webhook"] = webhook_info

        if create_gitlab_webhook or store_settings:
            # Save the relationship settings to settings.yaml
            project_settings = {
                "projectURL": gitlab_repo_url,
                "tableID": created_table_id,
                "links": []
            }
            settings_manager.save_project_settings(project_settings)
            response["settings_saved"] = True

        return jsonify(response), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_gitlab_project_webhook(repo_url, token, webhook_secret, nocodb_table_id, server_ip, webhook_username=None):
    """
    Create a webhook in the given GitLab project using python-gitlab.
    """
    # Extract project path from repo URL (e.g., https://gitlab.com/group/project.git → group/project)
    parsed_uri = urlparse(repo_url)
    gitlab_host = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    project_path = parsed_uri.path.lstrip("/").removesuffix(".git")
    gl = gitlab.Gitlab(gitlab_host, private_token=token)
    project = gl.projects.get(project_path)

    # Build webhook URL
    webhook_url = f"{server_ip}/webhooks/push"

    # Create webhook with custom headers
    try:
        hook = project.hooks.create({
            'url': webhook_url,
            'push_events': True,
            'enable_ssl_verification': NOCODB_SSL_CERT,
            'custom_headers': [
                {"key": HEADER_NOCO_DB_TABLE_ID, 'value': str(nocodb_table_id)},
                {"key": HEADER_WEBHOOK_USERNAME, 'value': webhook_username},
                {"key": HEADER_WEBHOOK_SECRET, 'value': webhook_secret}
            ]
        })
    except Exception as e:
        return {"error": f"Failed to create GitLab webhook: {str(e)}"} 

    return {"id": hook.id, "url": webhook_url}
    

def link_records_between_tables(parent_table_client: nocodb.Table, 
                                child_table_client: nocodb.Table, 
                                parent_field_name: str, 
                                child_field_name: str, 
                                new_column_created: bool,
                                connection: str,
                                field_link = ""
                                ):
    updated_count = 0
    parent_records = parent_table_client.list_all_records().get("list", [])
    child_records = child_table_client.list_all_records().get("list", [])
    parent_table_meta = parent_table_client.read_table()
    child_table_meta = child_table_client.read_table()
    parent_columns = parent_table_meta.get("columns", [])
    child_columns = child_table_meta.get("columns", [])

    # Find the first column where 'pk' is 1
    parent_PK = next(
        (col["title"] for col in parent_columns if col.get("pk") == 1),
        None  # default if not found
    )
    child_PK = next(
        (col["title"] for col in child_columns if col.get("pk") == 1),
        None  # default if not found
    )

    for record in parent_records:
        parent_link_to_child_record = str(record.get(parent_field_name))
        print("Parent link to child record:", parent_link_to_child_record)
        #  Parse link field value that might look like "[6, 7]" or "6, 7" or "6 7" to a list of strings
        parent_links_to_child_record = parse_link_field(parent_link_to_child_record)
        corresponding_child_records = []
        for parent_link_to_child_record in parent_links_to_child_record:
            # Find the corresponding child record based on the parent field value
            child_records_for_parent_link = [r for r in child_records if str(r.get(child_field_name)) == parent_link_to_child_record]
            if not child_records_for_parent_link:
                continue
            corresponding_child_records.extend(child_records_for_parent_link)
        print("Corresponding child records:", corresponding_child_records)

        # If we already have a link field, we need to check which records are missing / need to be unlinked
        if (not new_column_created):
            if connection == "mm":
                existing_linked_records = parent_table_client.list_linked_records(
                    linkFieldId=field_link,
                    recordId=record[parent_PK]
                ).get("list", [])
            elif connection == "oo":
                column_name = parent_table_meta.get("columnsById", {}).get(field_link, {}).get("title")
                existing_linked_records = record.get(column_name, [])
                existing_linked_records = [existing_linked_records] if existing_linked_records else [] 
            else:
                existing_linked_records = parent_table_client.list_linked_records(
                    linkFieldId=field_link,
                    recordId=record[parent_PK]
                )
                existing_linked_records = [existing_linked_records] if existing_linked_records else []
            print("Existing linked records:", existing_linked_records)
            record_ids_to_link = [r[child_PK] for r in corresponding_child_records if r[child_PK] not in [lr[child_PK] for lr in existing_linked_records]]
            record_ids_to_unlink = [lr[child_PK] for lr in existing_linked_records if lr[child_PK] not in [r[child_PK] for r in corresponding_child_records]]
            print("Record IDs to link:", record_ids_to_link)
            print("Record IDs to unlink:", record_ids_to_unlink)
            if record_ids_to_unlink:
                unlink_res = parent_table_client.unlink_records(linkFieldId=field_link,
                                            recordId=record[parent_PK],
                                            refRowPKValues=record_ids_to_unlink)
                if not "error" in unlink_res:
                    updated_count += 1
                else:
                    print(f"Failed to unlink records for parent ID {record[parent_PK]}: {unlink_res['error']}")

            if record_ids_to_link:
                link_records_res = parent_table_client.link_records(linkFieldId=field_link,
                                            recordId=record[parent_PK],
                                            refRowPKValues=record_ids_to_link)
                if not "error" in link_records_res:
                    updated_count += len(record_ids_to_link)
                else:
                    print(f"Failed to link records for parent ID {record[parent_PK]}: {link_records_res['error']}")
        else:
            if (len(corresponding_child_records) == 0):
                print(f"No corresponding child records found for parent ID {record[parent_PK]}")
                continue
            if (connection == "mm" or connection == "oo"):
                link_records_res = parent_table_client.link_records(linkFieldId=field_link,
                                            recordId=record[parent_PK],
                                            refRowPKValues=[r[child_PK] for r in corresponding_child_records])
            else:
                # For "mo", we link the child records to the parent record
                for r in corresponding_child_records:
                    if not r.get(child_PK):
                        continue
                    link_records_res = child_table_client.link_records(linkFieldId=field_link,
                                                recordId=r[child_PK],
                                                refRowPKValue=record[parent_PK])
            if not "error" in link_records_res:
                updated_count += 1
            else:
                print(f"Failed to link records for parent ID {record[parent_PK]}: {link_records_res['error']}")
    return updated_count


@api_bp.route("/link-tables", methods=["POST"])
def create_links_between_tables():
    """
    Link two tables in NocoDB based on field values or by creating a new link field.

    Required JSON fields:
    - parent_table_id: str
    - child_table_id: str
    - parent_field_name: str - the field in the parent table that contains the value from child table to match
    - child_field_name: str - the primary key field in the child table that contains the value to match with parent table

    Optional:
    - field_link: str (existing link field in child table)
    - connection: "mm", "oo", or "mo"
    """

    data = request.get_json()
    parent_table_id = data.get("parent_table_id")
    child_table_id = data.get("child_table_id")
    child_field_name = data.get("child_field_name")

    parent_field_name = data.get("parent_field_name")
    
    field_link = data.get("field_link")
    connection = data.get("connection")
    save_settings = data.get("save_settings", True)

    # Basic validation
    if not parent_table_id or not child_table_id or not parent_field_name or not child_field_name:
        return jsonify({"error": "Missing required fields"}), 400

    if not field_link and not connection:
        return jsonify({"error": "If 'field_link' is not provided, 'connection' must be specified"}), 400

    if connection not in ["mm", "oo", "mo"] and not field_link:
        return jsonify({"error": "Invalid connection type. Must be one of: 'mm', 'oo', 'mo'"}), 400
    

    # try:
    if not NOCODB_TOKEN:
        return jsonify({"error": "Missing Nocodb Token"}), 400

    parent_table = nocodb.Table(tableid=parent_table_id, host=NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT)
    child_table = nocodb.Table(tableid=child_table_id, host=NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT)


    where_to_create_new_field, what_to_reference = parent_table_id, child_table_id
    where_to_create_new_field_table = parent_table
    # Decide where to create the link field
    # If connection is "mo", we create the link in the child table with the type "has many"
    if connection == "mo":
        # parent_table_id, child_table_id = child_table_id, parent_table_id
        where_to_create_new_field, what_to_reference = child_table_id, parent_table_id
        where_to_create_new_field_table = child_table

    parent_table_meta = parent_table.read_table()
    child_table_meta = child_table.read_table()
    parent_columns = parent_table_meta.get("columns", [])
    child_columns = child_table_meta.get("columns", [])
    new_column_created = False
    # Step 1: Handle field creation (if needed)
    if not field_link:
        field_type_map = {
            "mm": "mm",
            "oo": "oo",
            "mo": "hm"  # for "mo", we add a "hm" field in the child table
        }

        link_type = field_type_map.get(connection)
        if not link_type:
            return jsonify({"error": "Invalid connection type. Must be one of: 'mm', 'hm', 'mo'"}), 400
        extra_options = {
            "type": link_type,
            "parentId": where_to_create_new_field,
            "childId": what_to_reference,
        }
        new_column_name = f"link_{what_to_reference}"

        field_response_columns = where_to_create_new_field_table.create_column(column_name=new_column_name,
                                                    column_type="Links",
                                                    extra_options=extra_options).get("columns")
        
        if not field_response_columns:
            return jsonify({"error": "Failed to create link field"}), 500
        
        field_link = next(
            (col["id"] for col in field_response_columns if col.get("title") == new_column_name),
            None
        )

        # Check if response was successful
        if not field_link:
            return jsonify({"error": "Failed to create link field"}), 500
        new_column_created = True
    else:
        connection = parent_table_meta["columnsById"][field_link]['colOptions']['type']

    updated_count = link_records_between_tables(parent_table_client=parent_table,
                                                child_table_client=child_table,
                                                parent_field_name=parent_field_name,
                                                child_field_name=child_field_name,
                                                new_column_created=new_column_created,
                                                connection=connection,
                                                field_link=field_link)

    res = {
        "message": "Records linked successfully",
        "linked_field": field_link,
        "records_updated": updated_count
    }

    if save_settings:
        parent_table_child_key_storage_field_id = next(
            (col["id"] for col in parent_columns if col.get("title") == parent_field_name),
            None  
        )
        if not parent_table_child_key_storage_field_id:
            return jsonify({"error": f"Parent table does not have a field named '{parent_field_name}'"}), 400
        child_table_link_field_id = next(
            (col["id"] for col in child_columns if col.get("title") == child_field_name),
            None
        )
        if not child_table_link_field_id:
            return jsonify({"error": f"Child table does not have a field named '{child_field_name}'"}), 400
        # Save the settings to the settings.yaml file
        project_settings = {
            "ParentTableLinkFieldID": field_link,
            "ParentTableChildKeyStorageFieldID": parent_table_child_key_storage_field_id,
            "ChildTableID": child_table_id,
            "ChildTableLinkFieldID": child_table_link_field_id,
            "AutomaticallyCreateChildRecords": save_settings,
        }
        settings_manager.save_relationship_settings(project_settings, parent_table_id)
        res["settings_saved"] = True

    return jsonify(res), 200


@api_bp.route("/analyze-unique-values", methods=["POST"])
def analyze_unique_values():
    data = request.get_json()
    project_urls = data.get("project_urls", [])
    minimum_unique_values = data.get("minimum_unique_values", 1)
    maximum_unique_values = data.get("maximum_unique_values", 10)
    settings_projects = settings_manager.get_all_projects()        
    if not project_urls:
        project_urls = [p["projectURL"] for p in settings_projects]

    if not project_urls:
        return jsonify({"error": "No project URLs was found"}), 400
    
    res = {}
    for project_url in project_urls:
        project_settings = next(
            (project for project in settings_projects if project.get("projectURL") == project_url),
            None 
        )
        if project_settings:
            table_id = project_settings.get("tableID")
            table_client = nocodb.Table(
                tableid=table_id,
                host=NOCODB_HOST,
                auth_token=NOCODB_TOKEN,
                verify=NOCODB_SSL_CERT
            )
            table_metadata = table_client.read_table()
            columns_to_exclude = []
            list_of_linked_columns = project_settings.get("links", [])
            if (list_of_linked_columns):
                for link in list_of_linked_columns:
                    linked_column = table_metadata.get("columnsById", {}).get(link)
                    if linked_column:
                        columns_to_exclude.append(linked_column["title"])
            if not table_id:
                return jsonify({"error": f"Project {project_url} does not have a table ID defined"}), 400
            table_rows = table_client.list_all_records().get("list", [])
            if not table_rows:
                continue  # Skip empty tables
            unique_counts = {key: len(set(item[key] for item in table_rows if key in item)) for key in table_rows[0]}
            allowed_keys = {
                key
                for key, count in unique_counts.items()
                if minimum_unique_values <= count <= maximum_unique_values
            }
            filtered_unique_counts = {
                key: count
                for key, count in unique_counts.items()
                if key in allowed_keys and key not in columns_to_exclude
            }
            if (filtered_unique_counts):
                res[project_url] = filtered_unique_counts
    return jsonify(res), 200



@api_bp.route("/normalize-columns", methods=["POST"])
def normalize_columns():
    """
    Normalize columns in the given tables based on the provided project URLs.
    Expects a JSON payload with 'projects_columns'
    Format:
    {
        "projects_columns": [
            {
                "project_url": "http://example.com/project1",
                "columns": [
                    "column1Title",
                    "column2Title"
                ]
            }
        ]
    }
    """
    data = request.get_json()
    projects_columns = data.get("projects_columns", [])
    if not projects_columns:
        return jsonify({"error": "No projects or columns provided"}), 400
    for project in projects_columns:
        project_url = project.get("project_url")
        columns_to_normalize = project.get("columns", [])
        if not project_url or not columns_to_normalize:
            return jsonify({"error": "Missing 'project_url' or 'columns'"}), 400
        
        # Get the settings for the project
        project_settings = next(
            (p for p in settings_manager.get_all_projects() if p.get("projectURL") == project_url),
            None
        )
        if not project_settings:
            return jsonify({"error": f"No settings found for project {project_url}"}), 404
        
        table_id = project_settings.get("tableID")
        if not table_id:
            return jsonify({"error": f"Project {project_url} does not have a table ID defined"}), 400
        
        # Normalize the columns
        table_client = nocodb.Table(
            tableid=table_id,
            host=NOCODB_HOST,
            auth_token=NOCODB_TOKEN,
            verify=NOCODB_SSL_CERT
        )
        table_metadata = table_client.read_table()
        table_base_id = table_metadata.get("base_id")
        table_base = nocodb.Base(
            base_id=table_base_id,
            host=NOCODB_HOST,
            auth_token=NOCODB_TOKEN,
            verify=NOCODB_SSL_CERT
        )
        records = table_client.list_all_records().get("list", [])
        # Step 1: For each column to normalize, create a new table and copy the data
        for column_title in columns_to_normalize:
            try:
                all_column_metadata = next(
                    (col for col in table_metadata.get("columns", []) if col.get("title") == column_title),
                    None
                )
                column_metadata = {k: all_column_metadata[k] for k in COLUMN_METADATA_TO_COPY if k in all_column_metadata}
                new_table_id = table_base.create_table(
                    name=f"{table_metadata.get('title')}_{column_title}",
                    columns=[
                        {"title": f"{column_title}", **column_metadata},
                        ID_COLUMN
                    ]
                )
                if not new_table_id:
                    return jsonify({"error": f"Failed to create new table for column {column_title}"}), 500
                new_table_client = nocodb.Table(
                    tableid=new_table_id,
                    host=NOCODB_HOST,
                    auth_token=NOCODB_TOKEN,
                    verify=NOCODB_SSL_CERT
                )

                unique_values = sorted({row[column_title] for row in records if column_title in row and row[column_title]})
                print(f"Unique values for column {column_title}: {unique_values}")
                if not unique_values:
                    continue
                # Copy the column data to the new table
                for value in unique_values:
                    new_table_client.insert({
                        f"{column_title}": value,
                    })

                # TODO: Make it work with mm as well
                extra_options = {
                    "type": "hm",
                    "parentId": new_table_id,
                    "childId": table_id,
                }
                new_column_name = f"link_{table_id}"
                field_response_columns = new_table_client.create_column(column_name=new_column_name,
                                                            column_type="Links",
                                                            extra_options=extra_options).get("columns")
                field_link = next(
                (col["id"] for col in field_response_columns if col.get("title") == new_column_name),
                None
                )
                print("Created link field:", field_link)

                updated_count = link_records_between_tables(parent_table_client=table_client, 
                                                            child_table_client=new_table_client,
                                                            parent_field_name=column_title,
                                                            child_field_name=column_title,
                                                            new_column_created=True,
                                                            connection="mo",
                                                            field_link=field_link)
                
                settings_manager.save_relationship_settings({
                    "ParentTableLinkFieldID": field_link,
                    "ParentTableChildKeyStorageFieldID": None,
                    "ChildTableID": new_table_id,
                    "ChildTableLinkFieldID": None,
                    "AutomaticallyCreateChildRecords": True,
                }, table_id)
                res = {
                    "message": f"Column {column_title} normalized successfully",
                    "new_table_id": new_table_id,
                    "records_updated": updated_count
                }
                print(res)
                return jsonify(res), 200

            except Exception as e:
                return jsonify({"error": f"Failed to normalize column {column_title}: {str(e)}"}), 500

