import json
import os
from flask import Flask, request, jsonify
from nocodb_client import nocodb, table_from_schema
from . import api_bp
import ast

NOCODB_PORT = os.getenv('NOCODB_PORT', '8080')
NOCODB_HOST = f"http://localhost:{NOCODB_PORT}"
NOCODB_TOKEN = os.getenv('NOCODB_TOKEN', None)
NOCODB_SSL_CERT = os.getenv('NOCODB_SSL_CERT', True)

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
    Route in order to create a new table in NocoDB from a schema file.
    """
    # Get form data
    table_name = request.form.get("table_name")
    base_id = request.form.get("base_id")
    new_base_name = request.form.get("new_base_name")
    schema_file = request.files.get("schema")

    print("=== DEBUG ===")
    print("request.form:", request.form)
    print("request.files:", request.files)
    print("table_name:", request.form.get("table_name"))
    print("schema_file:", request.files.get("schema"))
    print("==============")
    # Validate input
    if not table_name or not schema_file:
        if not table_name and not schema_file:
            return jsonify({"error": "Missing 'table_name' and 'schema' file"}), 400
        if not table_name:
            return jsonify({"error": "Missing 'table_name'"}), 400
        if not schema_file:
            return jsonify({"error": "Missing 'schema' file"}), 400
        return jsonify({"error": "Missing 'table_name' or 'schema' file"}), 400

    try:
        schema = json.load(schema_file)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in schema file"}), 400

    try:

        if not NOCODB_TOKEN:
            return jsonify({"error": "Missing Nocodb Token"}), 400

        # Initialize base handler
        # base_client = nocodb.Base(host=NOCODB_HOST, auth_token=nocodb_token, verify=nocodb_ssl_cert)

        # If new_base_name is provided, create a new base
        if new_base_name:
            new_base = nocodb.Nocodb(NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT).create_base(new_base_name)
            if not new_base:
                return jsonify({"error": f"Failed to create new base '{new_base_name}'"}), 500
            base_id = new_base["id"]
        elif not base_id:
            return jsonify({"error": "Provide either 'base_id' or 'new_base_name'"}), 400
        

        # Now create the table in the selected base
        created_table_id = table_from_schema.create_new_table_from_schema(
            nocodb_host=NOCODB_HOST,
            nocodb_token=NOCODB_TOKEN,
            nocodb_ssl_cert=NOCODB_SSL_CERT,
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

    # Step 2: Fetch records from both tables
    parent_records = parent_table.list_all_records().get("list", [])
    child_records = child_table.list_all_records().get("list", [])

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
    if not parent_PK or not child_PK:
        return jsonify({"error": "Parent or child table does not have a primary key defined"}), 400

    # Step 3: Link records
    updated_count = 0
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
                existing_linked_records = parent_table.list_linked_records(
                    linkFieldId=field_link,
                    recordId=record[parent_PK]
                ).get("list", [])
            elif connection == "oo":
                column_name = parent_table_meta.get("columnsById", {}).get(field_link, {}).get("title")
                existing_linked_records = record.get(column_name, [])
                existing_linked_records = [existing_linked_records] if existing_linked_records else [] 
            else:
                existing_linked_records = parent_table.list_linked_records(
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
                unlink_res = parent_table.unlink_records(linkFieldId=field_link,
                                            recordId=record[parent_PK],
                                            refRowPKValues=record_ids_to_unlink)
                if not "error" in unlink_res:
                    updated_count += 1
                else:
                    print(f"Failed to unlink records for parent ID {record[parent_PK]}: {unlink_res['error']}")

            if record_ids_to_link:
                link_records_res = parent_table.link_records(linkFieldId=field_link,
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
                link_records_res = where_to_create_new_field_table.link_records(linkFieldId=field_link,
                                            recordId=record[parent_PK],
                                            refRowPKValues=[r[child_PK] for r in corresponding_child_records])
            else:
                # For "mo", we link the child records to the parent record
                for r in corresponding_child_records:
                    if not r.get(child_PK):
                        continue
                    link_records_res = where_to_create_new_field_table.link_records(linkFieldId=field_link,
                                                recordId=r[child_PK],
                                                refRowPKValue=record[parent_PK])
            if not "error" in link_records_res:
                updated_count += 1
            else:
                print(f"Failed to link records for parent ID {record[parent_PK]}: {link_records_res['error']}")

    return jsonify({
        "message": "Records linked successfully",
        "linked_field": field_link,
        "records_updated": updated_count
    }), 200
