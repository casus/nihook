import sys
import json

import pandas
import dateutil.parser


"""
Prepare JSON metadata from a 'DATASET.json' file before it can be entered to Nocodb
"""

""" 
Helper function to check if a string contains time duration. Test this before is_datetime() because that 
may also answer something but will use the currect day with the time duration as point in time.
"""
def is_time_duration(string):

    try: 
        # use pandas datetime parser because it also handles nanoseconds
        result= pandas.to_datetime(string, format='%H:%M:%S.%f', errors='raise')
        return pandas.Timedelta( days=0, 
            hours=result.hour, minutes=result.minute, seconds=result.second, 
            microseconds=result.microsecond, nanoseconds=result.nanosecond )

    except ValueError:
        pass

    try: 
        # use pandas datetime parser because it also handles nanoseconds
        result= pandas.to_datetime(string, format='%H:%M:%S', errors='raise')
        return result

    except ValueError:
        pass

    return None

""" 
Helper function to check if a string contains datetime
"""
def is_datetime(string, fuzzy=False):

    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        result= dateutil.parser.parse(string, fuzzy=fuzzy)
        return result

    except ValueError:
        return None



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

        # replace spaces in names by underscore
        kk= k.replace(' ','_')

        # if kk != k:
        #     print("    rename ",k, " --> ", kk, " as ", type( json_data[k] ))

        if type( {} ) == type( json_data[k] ):

            #print("        dict")

            #recursive
            flatten_keys( result, prefix+kk, json_data[k] )

        else:

            flat_key= prefix+kk
            if flat_key in result:
                print("WARNING: ", flat_key, " already present")

            result[flat_key]= json_data[k]

def prepare_input( input ):

    # print( json.dumps(input,indent=4) )

    print(" ======== ")

    data= {}

    flatten_keys( data, "", input )

    # print("Result: ")
    # print( json.dumps(data,indent=4))

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

        if type(1) == type(data[k]):

            #print("    ", k, " --> type ", type(data[k]), " example ", data[k])
            #print("handle int")
            columns.append( 
                {
                    "column_name": k,
                    "title": k,
                    "uidt": "Number",
                    "dt": "int",
                    "un": False
                })

        elif type(1.1) == type(data[k]):

            #print("    ", k, " --> type ", type(data[k]), " example ", data[k])
            #print("handle float or decimal")
            columns.append( 
                {
                    "column_name": k,
                    "title": k,
                    "uidt": "Number",
                    "dt": "float8",
                    "un": False
                })

        elif type("") == type(data[k]):

            #print("    ", k, " --> type ", type(data[k]), " example ", data[k])

            # several differtn cases here

            if is_it_time_duration := is_time_duration( data[k] ):

                #print("handle string -- duration")
                #print("    found duration ", is_it_time_duration, " from ", data[k])
                columns.append( 
                    {
                        "column_name": k,
                        "title": k,
                        "uidt": "Duration",
                        "dt": "decimal",
                        "un": False
                    })

            elif is_it_datetime := is_datetime( data[k] ):

                #print("handle string -- datetime")
                #print("    found datetime ", is_it_datetime, " from ", data[k])
                columns.append( 
                    {
                        "column_name": k,
                        "title": k,
                        "uidt": "DateTime",
                        "dt": "timestamp",
                        "un": False
                    })

            elif data[k].startswith("http://") or data[k].startswith("https://"):

                #print("handle string -- url")
                #print("    found datetime ", is_it_datetime, " from ", data[k])
                columns.append( 
                    {
                        "column_name": k,
                        "title": k,
                        "uidt": "URL",
                        "dt": "character varying",
                        "un": False
                    })
            else:

                #print("handle string -- generic")
                columns.append( 
                    {
                        "column_name": k,
                        "title": k,
                        "uidt": "SingleLineText",
                        "dt": "character varying",
                        "un": False
                    })


        elif type(True) == type(data[k]):

            #print("    ", k, " --> type ", type(data[k]), " example ", data[k])
            #print("handle bool")
            columns.append( 
                {
                    "column_name": k,
                    "title": k,
                    "uidt": "Checkbox",
                    "dt": "bool",
                    "un": False
                })

        elif type([]) == type(data[k]):

            # print("    ", k, " --> type ", type(data[k]), " example ", data[k])
            # print("handle list")
            columns.append( 
                {
                    "column_name": k,
                    "title": k,
                    "uidt": "JSON",
                    "dt": "json",
                    "un": False
                })

        else:

            ## no not cover {} above because those should have been resolved by 'flatten_keys()'

            print("    ", k, " --> type ", type(data[k]), " example ", data[k])
            print("handle unknown, abort")
            sys.exit(-2)

    return columns
