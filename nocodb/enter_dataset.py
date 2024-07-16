#!/usr/bin/env python3

import sys
import os
import json
import argparse

import nocodb
import prepare_json

"""
Read one ore more 'DATASET.json' files and add it's contents to an existing NocoDB table
"""

if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')

    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs='+', help="Input JSON files")
    parser.add_argument("-t", "--table", required=True, help="Existing Nocodb table id, then insert into this table")
    args = parser.parse_args()

    table= nocodb.Table( args.table, host=nocodb_host, auth_token=nocodb_token )

    for f in args.inputs:

        print("insert file ", f)

        with open(f,"r") as file:

            input= json.load(file)

            data= prepare_json.prepare_input( input )

            print( f"Enter input from {f} into table {args.table}")

            res= table.insert(data)
            print( "    RESULT: ", json.dumps(res,indent=4) )

