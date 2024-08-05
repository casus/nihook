#!/usr/bin/env python3

import argparse
import json
import os
import sys

import prepare_json
from nocodb_.nocodb import Base, Table

"""
Read one ore more 'DATASET.json' files and add it's contents to an existing NocoDB table
"""

if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')

    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs='+', help="Input JSON files")
    parser.add_argument("-t", "--table", required=True, help="Existing Nocodb table id, then insert into this table")
    parser.add_argument("-p", "--prefix", default="",
                        help="Prefix to the URL field which is usually the host part of the URL but can be any prefix string")
    args = parser.parse_args()

    inputfile = args.input
    print("Input file ", inputfile)

    with open(inputfile, "r") as f:
        input = json.load(f)

    data = prepare_json.prepare_input(input)

    tableid = None

    if args.table:

        tableid = args.table
        print("Nocodb table ", args.table)

    else:

        print("No table given")

        if args.base:

            table_name = None
            if args.name:
                table_name = args.name
            else:
                print("No name for new table given, abort")
                sys.exit(-1)

            baseid = args.base
            print("Nocodb base ", baseid)
            print(f"... create new table '{table_name}' in base {baseid}")

            # prepare column definition
            columns = prepare_json.derive_table_columns_definition(data)
            print(json.dumps(columns, indent=4))

            # actually create the new table
            base = Base(baseid, host=nocodb_host, auth_token=nocodb_token)
            tableid = base.create_table(table_name, columns, color="#e6f253")

        else:

            for f in args.inputs:
                print("insert file ", f)

                with open(f, "r") as file:
                    table = Table(tableid, host=nocodb_host, auth_token=nocodb_token)

                    data = prepare_json.prepare_input(input, url=args.prefix + f)

                    print(f"Enter input from {f} into table {args.table}")

                    res = table.insert(data)
                    print("    RESULT: ", json.dumps(res, indent=4))
