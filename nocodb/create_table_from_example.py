#!/usr/bin/env python3

import sys
import os
import json
import argparse

import nocodb
import prepare_json

"""
Read a 'DATASET.json' file and create a matching NocoDB table. 

It will not import the given 'DATASET.json' file, though. Instead, the insert functionality stays in a separate script.
"""

if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("-b", "--base", required= True, help="Existing Nocodb base id to create the new Table in")
    parser.add_argument("-n", "--name", required= True, help="Name for the newly created table")
    args = parser.parse_args()

    inputfile= args.input
    print("Input file ", inputfile)

    with open(inputfile,"r") as f:
        input= json.load(f)

    data= prepare_json.prepare_input( input )

    print(f"... create new table '{args.name}' in base {args.base}")

    # prepare column definition
    columns= prepare_json.derive_table_columns_definition( data )
    print( json.dumps(columns,indent=4) )

    # actualy create the new table 
    base= nocodb.Base( args.base, host=nocodb_host, auth_token=nocodb_token )
    tableid= base.create_table(args.name,columns,color="#e6f253")

    table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token )


    # TODO output of newly created table layoutq