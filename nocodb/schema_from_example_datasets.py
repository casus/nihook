#!/usr/bin/env python3
import importlib
import sys
import os
import json
import argparse

import nocodb
import prepare_json
from jsonschema import validate

import pandas
import dateutil.parser

# TODO replace genson and remove jsonschema in order to:
# - to make this script self-contained so that ony copy it to datalad repos
# - we can detect and mark special string types such as datatime strings
#   ... to create NOCODB table columns accordingly, JSON SCHEMAS don't support this

""" 
Helper function to check if a string contains time duration. Test this before is_datetime() because that 
may also answer something but will use the currect day with the time duration as point in time.
"""
def is_time_duration(string):
    try:
        # use pandas datetime parser because it also handles nanoseconds
        result = pandas.to_datetime(string, format='%H:%M:%S.%f', errors='raise')
        return pandas.Timedelta(days=0,
                                hours=result.hour, minutes=result.minute, seconds=result.second,
                                microseconds=result.microsecond, nanoseconds=result.nanosecond)

    except ValueError:
        pass

    try:
        # same but with no second decimals
        # use pandas datetime parser because it also handles nanoseconds
        result = pandas.to_datetime(string, format='%H:%M:%S', errors='raise')
        return pandas.Timedelta(days=0,
                                hours=result.hour, minutes=result.minute, seconds=result.second,
                                microseconds=result.microsecond, nanoseconds=result.nanosecond)

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
        result = dateutil.parser.parse(string, fuzzy=fuzzy)
        return result

    except ValueError:
        return None

# Generate a JSON SCHEMA from several JSCON objects which are
# identiacally or at least similarly structured
class SchemaGenerator:

    template= '{"$schema": "http://json-schema.org/schema#", "type": "object", "properties": {}, "required": [], "count": {} }'

    schema= json.loads( template )

    def __init__(self):
        self.num= 0

    # recursively go through JSON input files and enter all keys with their types into the schema
    # use temporary dict 'count' to count how often each key appeared 
    # ... use this later to identify "required" and "not required" keys
    def recursiveScan( self, input_json, output_schema ):

        if not "type" in output_schema:
            print("WARNING: no \"type\" in (sub)schema")

        if not "properties" in output_schema:
            print("WARNING: no \"properties\" in (sub)schema")

        if not "required" in output_schema:
            print("WARNING: no \"required\" in (sub)schema")

        for k,v in input_json.items():

            ### depending on the type of v do different things with k,v

            # handle nested dicts with recursive calls

            if  type(v) is dict:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "object", "properties": {}, "required": [], "count": {} } } )
                    output_schema['count'].update( { k : 1 } )
                else:
                    output_schema['count'][k] += 1
                    if output_schema['properties'][k]['type'] != "object":
                        print( f"WARNING: type mismatch for key '{k}' where 'object' != ", output_schema['properties'][k]["type"] )

                self.recursiveScan( input_json[k], output_schema['properties'][k] )

                continue

            # handle arrays, assume same type

            if  type(v) is list:

                num= len(v)

                typename= ""
                if num >= 1:

                    if type(v[0]) is int:
                        typename= "integer"
                    elif type(v[0]) is float:
                        typename= "number"
                    elif type(v[0]) is str:
                        typename= "string"
                    else:
                        typename= ""
                        print("    unknown array type name for ", type(v[0]))

                    if k not in output_schema['properties']:
                        output_schema['properties'].update( { k : { "type": "array", "items": { "type": typename } } } )
                        output_schema['count'].update( { k : 1 } )
                    else:
                        output_schema['count'][k] += 1
                        if output_schema['properties'][k]['type'] != "array":
                            print( f"WARNING: type mismatch for key '{k}' where 'object' != ", output_schema['properties'][k]['type'] )
                        if output_schema['properties'][k]['items']['type'] != typename:
                            print( f"WARNING: type mismatch for key '{k}' array type where '{typename}' != ", output_schema['properties'][k]['items']['type'] )

                else: # empty array

                    if k not in output_schema['properties']:
                        output_schema['properties'].update( { k : { "type": "array" } } )
                        output_schema['count'].update( { k : 1 } )
                    else:
                        output_schema['count'][k] += 1
                        if output_schema['properties'][k]['type'] != "array":
                            print( f"WARNING: type mismatch for key '{k}' where 'object' != ", output_schema['properties'][k]['type'] )

                continue


            # handle plain types except string, no recursion here

            if  type(v) is int:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "integer" } } )
                    output_schema['count'].update( { k : 1 } )
                else:
                    output_schema['count'][k] += 1
                    if output_schema['properties'][k]['type'] != "integer":

                        if output_schema['properties'][k]['type'] == "number":

                            pass # don't warn because the integer of this instance can just as well be covered by 'number'

                        elif output_schema['properties'][k]['type'] == "string":

                            print( f"        HINT: found an 'integer' in a string-type field, accept" )

                        else:

                            print( f"        WARNING: type mismatch for key '{k}' where 'integer' != ", output_schema['properties'][k]['type'] )

                continue

            if  type(v) is float:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "number" } } )
                    output_schema['count'].update( { k : 1 } )
                else:
                    output_schema['count'][k] += 1
                    if output_schema['properties'][k]['type'] != "number":

                        if output_schema['properties'][k]['type'] == "integer":

                            print( f"        TODO: found a 'number' field where 'integer' was expected -- convert it" )

                        elif output_schema['properties'][k]['type'] == "string":

                            print( f"        HINT: found a 'number' in a string-type field, accept" )

                        else:

                            print( f"        WARNING: type mismatch for key '{k}' where 'number' != ", output_schema['properties'][k]['type'] )

                continue

            if  type(v) is bool:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "boolean" } } )
                    output_schema['count'].update( { k : 1 } )
                else:
                    output_schema['count'][k] += 1
                    if output_schema['properties'][k]['type'] != "boolean":
                        print( f"WARNING: type mismatch for key '{k}' where 'boolean' != ", output_schema['properties'][k]['type'] )

                continue

            # test for NoneType
            if  v is None: 

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "null" } } )
                    output_schema['count'].update( { k : 1 } )
                else:
                    output_schema['count'][k] += 1
                    if output_schema['properties'][k]['type'] != "null":
                        print( f"WARNING: type mismatch for key '{k}' where 'null' != ", output_schema['properties'][k]['type'] )

                continue

            # handle string types with special sub types, no recursion here

            if  type(v) is str:

                newentry= { "type": "string" }

                if time_duration := is_time_duration(v):

                    newentry= { "type": "string", "subtype": "Duration" }
                    # print(f"DEBUG: {v} interpreted as a duration")

                elif datetime := is_datetime(v):

                    newentry= { "type": "string", "subtype": "DateTime" }
                    # print(f"DEBUG: {v} interpreted as a datetime")

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : newentry } )
                    output_schema['count'].update( { k : 1 } )
                else:
                    output_schema['count'][k] += 1
                    if output_schema['properties'][k]['type'] != "string":

                        print( f"WARNING: type mismatch for string key '{k}' where {newentry} != ", output_schema['properties'][k] )

                    else:

                        if output_schema['properties'][k] != newentry:

                            ## this is not an issue to report
                            #print( f"WARNING: sub-type mismatch for string key '{k}' where {newentry} != ", output_schema['properties'][k], " --> revert to plain string" )

                            output_schema['properties'][k]['subtype']= ""
                continue

            print( "unhandled type ", type(v), " for key ", k )
        return 1

    def addJsonObject( self, object ):

        if self.num < 0:
            print("ERROR: cannot add more JSON objects, SCHEMA already finalized, abort")
            return

        self.num += self.recursiveScan( object, self.schema )

    # go through schema and mark all keys as required which appeared in all input objects,
    # this have count == self.num
    def finalizeSchema( self, output_schema, num ):

        if not "type" in output_schema:
            print("WARNING: no \"type\" in (sub)schema")

        if not "properties" in output_schema:
            print("WARNING: no \"properties\" in (sub)schema")

        if not "required" in output_schema:
            print("WARNING: no \"required\" in (sub)schema")

        if not "count" in output_schema:
            print("WARNING: no \"count\" in (sub)schema")

        for k,v in output_schema['properties'].items():

            if output_schema['count'][k] == num:
                output_schema['required'].append(k)

            if type(v) is dict and v["type"] == "object":
                self.finalizeSchema( output_schema['properties'][k], num )

        # remove the counters
        output_schema.pop("count",None)


    # this destroys the internal counts, don't use addJsonObject after this again
    def getSchema( self ):

        self.finalizeSchema( self.schema, self.num )
        self.num= -1 # diable further addJsonObject() calls

        return self.schema


def check_schema( schema ):

    result= True

    if not "type" in schema:
        print("WARNING: no \"type\" in (sub)schema")
        result= False

    if not "properties" in schema:
        return True

    for k, v in schema['properties'].items():

        if len(v) == 1:

            if 'type' in v:

                type = v['type']
                match type:
                    case 'string':
                        pass
                    case 'integer':
                        pass
                    case 'boolean':
                        pass
                    case 'number':
                        pass
                    case 'array':
                        pass
                    case 'null':
                        pass
                    case _:
                        print(f'unknown column type {type} for key {k}')
                        result= False

            elif 'anyOf' in v:

                # this is an selection of types it could be
                print(f"WARNING: conflicting types for key {k}, mapping to string, may cause issues")
                result= False

        else:

            r= check_schema(v)
            result= result or r

    return result


"""
Generate a JSON schema from multiple DATASET.json example files
"""
if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True)

    parser = argparse.ArgumentParser(description='Generate a JSON schema from multiple DATASET.json example files')
    parser.add_argument("input", nargs='+', default=None,
        help="Input files must be DATASET.json files as generated from the use-case specific metadata extraction scripts")
    parser.add_argument("-o", "--output", default="SCHEMA.json", help="Output schema file, default 'SCHEMA.json")
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

        generator= SchemaGenerator()

        for input_file in args.input:

            print("    INPUT ", input_file)

            with open(input_file, "r") as f:
                input = json.load(f)
                generator.addJsonObject(input)

        schemanew= generator.getSchema()
        check_schema( schemanew )

        f = open(args.output, "w")
        f.write(json.dumps(schemanew, indent=4))
        f.close()

