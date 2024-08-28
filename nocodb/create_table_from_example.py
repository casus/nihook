#!/usr/bin/env python3

import sys
import os
import json
import argparse

import nocodb
import prepare_json
from genson import SchemaBuilder

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


def parse_and_append_column_metadata(columns: [], k: str, v: str):
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

#                 generate schema
# apply schema and create table
# take input file (validate) and create a table directly (not the default), without data

def generate(args: argparse.Namespace):
    assert args.base is None
    assert args.name is None
    input_file = args.input

    builder = SchemaBuilder()
    with open(input_file, "r") as f:
        input = json.load(f)

        builder.add_object(input)

    schema = builder.to_json(indent=2)
    schemaDir = input_file.rpartition("/")[0]

    f = open(f"{schemaDir}/SCHEMA.json", "w")
    f.write(schema)
    f.close()

"""
Read a 'DATASET.json' file and create a matching NocoDB table. 

It will not import the given 'DATASET.json' file, though. Instead, the insert functionality stays in a separate script.

It will insert **one** additional key "URL" which also serves as the primary key. This must not be used by the DATASET.json.
"""

if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True)

    parser = argparse.ArgumentParser()
    parser.add_argument("schema", choices=['generate', 'apply', 'generateAndApply'],
                        help="generate|apply|generate&apply schema")
    parser.add_argument("input", nargs='?', default=None,
                        help="Input file, either a schema or a dataset, or directory containing the schema")
    parser.add_argument("-b", "--base", help="Existing Nocodb base id to create the new Table in")
    parser.add_argument("-n", "--name", help="Name for the newly created table")
    args = parser.parse_args()

    schema = args.schema
    match schema:

        case 'generate':


        case 'apply':

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
                for c in details['columns']:
                    print(f"    column '{c['title']}' of type {c['uidt']} / {c['dt']}")



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
