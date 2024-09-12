#!/usr/bin/env python3
import importlib
import sys
import os
import json
import argparse

import nocodb
import prepare_json
from genson import SchemaBuilder
from jsonschema import validate


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
}]


def parse_and_append_column_metadata(columns: [], k: str, v: dict):
    if len(v) == 1:
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
            case _:
                raise Exception(f'unknown column type{type}')
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

def generate(args: argparse.Namespace):
    assert args.base is None
    assert args.name is None
    input_file = args.input

    builder = SchemaBuilder()
    with open(input_file, "r") as f:
        input = json.load(f)

        builder.add_object(input)

    schema = builder.to_json(indent=2)
    schema_dir = input_file.rpartition("/")[0]

    f = open(f"{schema_dir}/SCHEMA.json", "w")
    f.write(schema)
    f.close()


def create_table(args: argparse.Namespace):
    assert args.base is not None
    assert args.name is not None
    schema_dir = args.input

    with open(f'{schema_dir}/SCHEMA.json', "r") as f:
        schema = json.load(f)

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

        if "status" == c['column_name'] or "URL" == c['title']:
            print("ERROR: special key 'status' used in input JSON -- not allowed, rename there")
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


def add_record(args: argparse.Namespace, base: nocodb.Base, table_id: str):
    assert args.base is not None
    assert args.table is not None
    assert args.input is not None

    if args.validate is not None:

        with open(args.input) as f:
            input = json.load(f)
        with open(args.validate) as f:
            schema = json.load(f)

        # Validate will raise exception if given json is not
        # what is described in schema.
        res = validate(instance=input, schema=schema)
        if res is not None:
            raise Exception(f'dataset is not valid because of the following errors: {res}')

    table = nocodb.Table(table_id, base=base)
    input['URL'] = 'url'
    input['status'] = "current"
    res = table.insert(input)
    print('')

# - generate schema, all fields optional except primary key
# - apply schema and create table
# - take input file (validate with skip option) and add to an existing table directly (not the default), without data
# SCHEMA should be by default in the current top directory
# check dependencies and output error nicely
# examples:
# > generateSchema test/DATASET.json
# > createTable test -b pn5o22efioeuz89 -n "table name"
# > -v test/SCHEMA.json -b pn5o22efioeuz89 -t mri37qzsk50zoe9 addRecord test/DATASET.json

"""
Read a 'DATASET.json' file and create a matching NocoDB table. 

It will not import the given 'DATASET.json' file, though. Instead, the insert functionality stays in a separate script.

It will insert **one** additional key "URL" which also serves as the primary key. This must not be used by the DATASET.json.
"""

if __name__ == '__main__':

    check_package('genson')
    check_package('jsonschema')

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True)

    parser = argparse.ArgumentParser()
    parser.add_argument("schema", choices=['generateSchema', 'createTable', 'addRecord'],
                        help="generate schema, create table, add record")
    parser.add_argument("input", nargs='?', default=None,
                        help="Input file, it must be: "
                             "1) a dataset for generating a schema. "
                             "2) a directory containing the schema to create the table."
                             "3) a dataset to add to an existing table")
    parser.add_argument("-b", "--base", help="Existing Nocodb base id to create the new Table in")
    parser.add_argument("-n", "--name", help="Name for the newly created table")
    parser.add_argument("-t", "--table", help="Existing Nocodb table id to add a record to")
    parser.add_argument("-v", "--validate", help="schema to validate it from")
    args = parser.parse_args()

    schema = args.schema
    match schema:

        case 'generateSchema':
            generate(args)

        case 'createTable':
            create_table(args)

        case 'addRecord':
            base = nocodb.Base(args.base, host=nocodb_host, auth_token=nocodb_token)
            add_record(args, base, args.table)

    # "id": "clvxk44a3kswa8f",
    #             "source_id": "b71a3kuda2ljzuq",
    #             "base_id": "pjkji23o6odzgvq",
    #             "fk_model_id": "mgloh6ffsigaj0g",
    #             "title": "index.id",
    #             "column_name": "index_id",
    #             "uidt": "SingleLineText",
    #             "dt": "character varyin
    # else:
    #     print("not successful")
