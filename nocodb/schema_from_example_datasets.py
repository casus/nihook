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


"""
Generate a JSON schema from multiple DATASET.json example files
"""
if __name__ == '__main__':

    check_package('genson')
    check_package('jsonschema')

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True)

    parser = argparse.ArgumentParser(description='Generate a JSON schema from multiple DATASET.json example files')
    parser.add_argument("input", nargs='+', default=None,
        help="Input files must be DATASET.json files as generated from the use-case specific metadata extraction scripts")
    parser.add_argument("-v", "--validate", help="Don't generate but validate all input files against an existing schema")
    args = parser.parse_args()

    if args.validate:

        schema= {}
        with open(args.validate, "r") as f:
            schema= json.load(f)

        for input_file in args.input:
            with open(input_file, "r") as f:
                print(f"Check {input_file} ", end='')
                input= json.load(f)

                try:
                    result= validate( instance=input, schema=schema )
                except:
                    print("mismatch")
                else:
                    print("okay")

    else:

        builder = SchemaBuilder()

        for input_file in args.input:

            with open(input_file, "r") as f:
                input = json.load(f)
                builder.add_object(input)

        schema = builder.to_json(indent=2)
        schema_dir = input_file.rpartition("/")[0]

        f = open("SCHEMA.json", "w")
        f.write(schema)
        f.close()
