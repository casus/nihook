#!/usr/bin/env python3
import importlib
import sys
import os
import json
import argparse

import nocodb
import prepare_json


special_columns = [{
    "column_name": "URL",
    "title": "URL",
    "uidt": "URL",
    "dt": "character varying",
    "un": False,
    "pk": True  # primary key
}, {
    "column_name": "status",
    "title": "status",
    "uidt": "SingleSelect",
    "dt": "character varying",
    "dtx": "specificType",
    "dtxp": "'current','deleted','replaced'",
    "dtxs": "",
    "cdf": "'current'"
}, {
    "column_name": "branch",
    "title": "branch",
    "uidt": "SingleLineText",
    "dt": "character varying",
}]


def parse_and_append_column_metadata(columns: [], k: str, v: dict):

    if len(v) == 1:

        if 'type' in v:

            type = v['type']
            match type:
                case 'string':
                    prepare_json.append_column_metadata(columns, k, '')
                case 'integer':
                    prepare_json.append_column_metadata(columns, k, 0)
                case 'boolean':
                    prepare_json.append_column_metadata(columns, k, False)
                case 'number':
                    prepare_json.append_column_metadata(columns, k, 0.0)
                case 'array':
                    prepare_json.append_column_metadata(columns, k, [])
                case _:
                    raise Exception(f'unknown column type{type}')

        elif 'anyOf' in v:

            # this is an selection of types it could be -- force it to string
            prepare_json.append_column_metadata(columns, k, '')

    else:
        if len(v) == 2 and 'type' in v and 'items' in v:
            prepare_json.append_column_metadata(columns, k, [])
        else:
            root = k
            for k, v in v['properties'].items():
                parse_and_append_column_metadata(columns, f'{root}.{k}', v)

def check_package(pkg: str):
    if pkg in sys.modules:
        pass
        # print(f"{pkg!r} already in sys.modules")
    elif (spec := importlib.util.find_spec(pkg)) is not None:
        # If you choose to perform the actual import ...
        module = importlib.util.module_from_spec(spec)
        sys.modules[pkg] = module
        spec.loader.exec_module(module)
        print(f"{pkg!r} has been imported")
    else:
        print(f"can't find the {pkg!r} module, please install it")


def create_table( base, name, schema ):
    assert args.base is not None
    assert args.name is not None

    columns = []

    # prepare column definition
    for k, v in schema['properties'].items():
        parse_and_append_column_metadata(columns, k, v)

    # add "URL" as extra column and as a primary key
    # add "status" as extra column

    for c in columns:

        if "URL" == c['column_name'] or "URL" == c['title']:
            print("ERROR: special key 'URL' used in input JSON -- not allowed, rename there")
            print("not successful")
            sys.exit(-3)

        if "status" == c['column_name'] or "status" == c['title']:
            print("ERROR: special key 'status' used in input JSON -- not allowed, rename there")
            print("not successful")
            sys.exit(-3)

        if "branch" == c['column_name'] or "branch" == c['title']:
            print("ERROR: special key 'branch' used in input JSON -- not allowed, rename there")
            print("not successful")
            sys.exit(-3)

    columns = special_columns + columns

    # print(json.dumps(columns, indent=4))

    # actually create the new table
    base = nocodb.Base(args.base, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert)
    table_id = base.create_table(args.name, columns)

    if table_id:
        # print(f"new table {table_id} with columns:")

        table = nocodb.Table(table_id, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert)
        details = table.read_table()

        # print(json.dumps(details,indent=4))
        # for c in details['columns']:
        #     print(f"    column '{c['title']}' of type {c['uidt']} / {c['dt']}")



"""
Create a new NOCODB table from an existing JSON schema file
"""

if __name__ == '__main__':

    check_package('genson')
    check_package('jsonschema')

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True)

    parser = argparse.ArgumentParser(description='Create a new NOCODB table from an existing JSON schema file')
    parser.add_argument("schema", help="Existing JSON schema file as template for the NOCODB table")
    parser.add_argument("-b", "--base", help="Existing Nocodb base id to create the new Table in")
    parser.add_argument("-n", "--name", help="Name for the newly created table")
    args = parser.parse_args()

    schema= {}
    with open(args.schema, "r") as f:
        schema= json.load(f)

    create_table( args.base, args.name, schema )
