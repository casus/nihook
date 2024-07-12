#!/usr/bin/env python3

import sys
import os
import json
import argparse

import nocodb
import prepare_json

"""
Read a 'DATASET.json' file and add it's contents it in a given NocoDB table

steps:
    - flatten the keys in a given fashion
    - create the table if needed, then an existing Base needs to be specified
    - if the table is already present, check that it matches
"""

if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')


    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("-t", "--table", help="Existing Nocodb table id, then insert into this table")
    parser.add_argument("-b", "--base", help="Existing Nocodb base id, then create a matchin table in this base and insert in this table")
    parser.add_argument("-n", "--name", help="Name for the newly created table, when -b/--base was used")
    args = parser.parse_args()

    inputfile= args.input
    print("Input file ", inputfile)

    with open(inputfile,"r") as f:
        input= json.load(f)

    data= prepare_json.prepare_input( input )


    tableid= None

    if args.table:

        tableid= args.table
        print("Nocodb table ", args.table)

    else:

        print("No table given")

        if args.base:

            table_name= None
            if args.name:
                table_name= args.name
            else:
                print("No name for new table given, abort")
                sys.exit(-1)


            baseid= args.base
            print("Nocodb base ", baseid)
            print(f"... create new table '{table_name}' in base {baseid}")

            # prepare column definition
            columns= prepare_json.derive_table_columns_definition( data )
            print( json.dumps(columns,indent=4) )

            # actualy create the new table 
            base= nocodb.Base( baseid, host=nocodb_host, auth_token=nocodb_token )
            tableid= base.create_table(table_name,columns,color="#e6f253")

        else:

            print("No table and no base given, abort")
            sys.exit(-1)


    print( f"Enter input from {inputfile} into table {tableid}")



