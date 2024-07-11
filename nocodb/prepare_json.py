import sys
import json

"""
Prepare JSON metadata from a 'DATASET.json' file before it can be entered to Nocodb
"""

"""
Recursively flatten the keys in a nested JSON structure
- store resulting keys in 'result_keys' and resulting flat JSON in 'result_data'
- JSON dicts are flattened
- JSON arrays are kept like they are
- text and numbers are copied
- use '.' as separators for flattened keys
    - check if there are collisions between existing names and flattened names
"""
def flatten_keys( result, prefix, json_data, separator="." ):

    # only append a separator if prefix was not empty
    if "" != prefix:
        prefix= prefix+separator

    for k in json_data:

        print("    ",k, " --> ", type( json_data[k] ))

        if type( {} ) == type( json_data[k] ):

            print("        dict")

            #recursive
            flatten_keys( result, prefix+k, json_data[k] )

        else:

            flat_key= prefix+k
            if flat_key in result:
                print("WARNING: ", flat_key, " already present")

            result[flat_key]= json_data[k]

def prepare_input( input ):

    print( json.dumps(input,indent=4) )

    print(" ======== ")

    data= {}

    flatten_keys( data, "", input )

    print("Result: ")
    print( json.dumps(data,indent=4))

    return data


def derive_table_columns_definition( data ):

    columns= []

    # column_template= {
        # "column_name": "title",
        # "title": "Title",

        # "uidt": "SingleLineText",
        # "dt": "varchar",

        # "uidt": "Number" ,
        # "dt": "float8" | "int" | "bigint"

        # "uidt": "Decimal" ,
        # "dt": "decimal"

        # "uidt": "DateTime",
        # "dt": "timestamp",

        # "uidt": "Checkbox",
        # "dt": "bool",

        # "uidt": "ID",
        # "dt": "int4",

        # uidt": "SingleSelect",
        # "dt": "text"

        # "un": false
    # }

    # column_template= {
    #     "column_name": 
    #     "title": 
    #     "uidt": 
    #     "dt": 
    #     "un": false
    # }


    for k in data:
        print("    ", k, " --> ", type(data[k]))

        if type(1) == type(data[k]):

            print("handle int")

        elif type(1.1) == type(data[k]):

            print("handle float or decimal")

        elif type("") == type(data[k]):

            print("handle string")

        elif type(True) == type(data[k]):

            print("handle bool")

        elif type([]) == type(data[k]):

            print("handle list")
            print("    ",data[k])

        else:

            ## no not cover {} above because those should have been resolved by 'flatten_keys()'

            print("handle unknown, abort")
            sys.exit(-2)

    return columns
