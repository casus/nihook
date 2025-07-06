#!/usr/bin/env python3
import importlib
import sys
import os
import json
import argparse

import nocodb
import prepare_json


special_columns = [
    {
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
    "dt": "varchar",
    "dtx": "specificType",
    "colOptions": {
        "options": 
        [
            {"title": "current"},
            {"title": "deleted"},
            {"title": "replaced"}
        ]
    },
    "dtxs": "",
    "cdf": "current"
}, {
    "column_name": "branch",
    "title": "branch",
    "uidt": "SingleLineText",
    "dt": "character varying",
}]


def parse_and_append_column_metadata(columns: [], k: str, v: dict):

    # replace spaces in keys
    k_nice= k.replace(' ', '_')

    if 'type' not in v:

        print("ERROR: 'type' not given, abort")
        sys.exit(-12)

    type= v['type']
    subtype= ""
    if 'subtype' in v:
        subtype= v['subtype']

    if 'anyOf' in v or 'anyOf' == type:

        # this is an selection of types it could be
        print(f"WARNING: conflicting types for key {k}, mapping to string, this may cause issues")

        # force it to string -- likely to cause trouble down the road
        prepare_json.add_column_definition(columns, k_nice, "string", "" )

    if 'type' in v:

        type = v['type']
        subtype= ""
        if 'subtype' in v:
            subtype= v['subtype']


        if "object" == type:

            # nested object, handle recursively
            assert 'properties' in v

            for kk, vv in v['properties'].items():
                parse_and_append_column_metadata(columns, f'{k}.{kk}', vv)

        else: # all other types and array []

            prepare_json.add_column_definition(columns,k_nice,type,subtype)


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


def schema_to_nocodb_definition( base, name, schema ):

    assert base is not None
    assert name is not None

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

    return columns


def create_new_table( base, name, columns ):

    assert base is not None
    assert name is not None

    base = nocodb.Base(base, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert)
    table_id = base.create_table(name, columns)

    if table_id:

        # print(f"new table {table_id} with columns:")

        table = nocodb.Table(table_id, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert)
        details = table.read_table()

        # print(json.dumps(details,indent=4))
        # for c in details['columns']:
        #     print(f"    column '{c['title']}' of type {c['uidt']} / {c['dt']}")


def create_new_table_with_params( base, name, columns, nocodb_host, nocodb_token, nocodb_ssl_cert ):

    assert base is not None
    assert name is not None

    base = nocodb.Base(base, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert)
    table_id = base.create_table(name, columns)

    if not table_id:
        raise RuntimeError(f"Failed to create table '{name}' in base '{base}'.")

    if table_id:

        # print(f"new table {table_id} with columns:")

        table = nocodb.Table(table_id, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert)
        details = table.read_table()

        # print(json.dumps(details,indent=4))
        # for c in details['columns']:
        #     print(f"    column '{c['title']}' of type {c['uidt']} / {c['dt']}")
        return table_id


def create_new_table_from_schema(nocodb_host, nocodb_token, nocodb_ssl_cert, base_id, table_name, schema):
    columns= schema_to_nocodb_definition( base_id, table_name, schema )
    return create_new_table_with_params( base_id, table_name, columns, nocodb_host, nocodb_token, nocodb_ssl_cert )

"""
Create a new NOCODB table from an existing JSON schema file
"""

if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True)

    parser = argparse.ArgumentParser(description='Create a new NOCODB table from an existing JSON schema file')
    parser.add_argument("schema", help="Existing JSON schema file as template for the NOCODB table")
    parser.add_argument("-b", "--base", help="Existing Nocodb base id to create the new Table in")
    parser.add_argument("-n", "--name", help="Name for the newly created table")
    parser.add_argument("-d", "--dryrun", action='store_true', help="Evaluate schema but don't create table")
    args = parser.parse_args()

    schema= {}
    with open(args.schema, "r") as f:
        schema= json.load(f)

    columns= schema_to_nocodb_definition( args.base, args.name, schema )
 
    if not args.dryrun:

        create_new_table( args.base, args.name, columns )

    else:

        print("Dryrun, this is what I would send to Nocodb: ")
        print(json.dumps(columns, indent=4))
