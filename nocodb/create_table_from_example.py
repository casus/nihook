#!/usr/bin/env python3

import sys
import os
import json
import argparse

import nocodb
import prepare_json

special_columns= [{
    "column_name": "URL",
    "title": "URL",
    "uidt": "URL",
    "dt": "character varying",
    "un": False,
    "pk": True # primary key
},{
    "column_name": "status",
    "title": "status",
    "uidt": "SingleSelect",
    "dt": "character varying",
    "dtx": "specificType",
    "dtxp": "'current','deleted','replaced'",
    "dtxs": "",
    "cdf": "'current'"
}]

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

    columns= special_columns + columns

    print( json.dumps(columns,indent=4) )

    # actualy create the new table 
    base= nocodb.Base( args.base, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )
    tableid= base.create_table(args.name, columns)

    if tableid:
        print(f"new table {tableid} with columns:")

        table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )
        details= table.read_table()

        # print(json.dumps(details,indent=4))
        for c in details['columns']:
            print(f"    column '{c['title']}' of type {c['uidt']} / {c['dt']}" )



# "id": "clvxk44a3kswa8f",
#             "source_id": "b71a3kuda2ljzuq",
#             "base_id": "pjkji23o6odzgvq",
#             "fk_model_id": "mgloh6ffsigaj0g",
#             "title": "index.id",
#             "column_name": "index_id",
#             "uidt": "SingleLineText",
#             "dt": "character varyin
    else:
        print("not successful")
