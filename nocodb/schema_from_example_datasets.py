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

# TODO replace genson and remove jsonschema in order to:
# - to make this script self-contained so that ony copy it to datalad repos
# - we can detect and mark special string types such as datatime strings
#   ... to create NOCODB table columns accordingly, JSON SCHEMAS don't support this

# Generate a JSON SCHEMA from several JSCON objects which are
# identiacally or at least similarly structured
class SchemaGenerator:

    template= '{"$schema": "http://json-schema.org/schema#",\n"type": "object",\n"properties": {}\n}'

    schema= json.loads( template )

    def __init__(self):
        print("Init: ")
        print( json.dumps(self.schema) )
        print("Done init ")

    def recursiveScan( self, input_json, output_schema ):

        print("recursiveScan")

        if not "type" in output_schema:
            print("WARNING: no \"type\" in (sub)schema")

        if not "properties" in output_schema:
            print("WARNING: no \"properties\" in (sub)schema")

        for k,v in input_json.items():

            ### depending on the type of v do different things with k,v

            # handle nested dicts with recursive calls

            if  type(v) is dict:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "object", "properties": {} } } )
                else:
                    if output_schema['properties'][k]["type"] != "object":
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
                    else:
                        if output_schema['properties'][k]["type"] != "array":
                            print( f"WARNING: type mismatch for key '{k}' where 'object' != ", output_schema['properties'][k]["type"] )
                        if output_schema['properties'][k]["items"]["type"] != typename:
                            print( f"WARNING: type mismatch for key '{k}' array type where '{typename}' != ", output_schema['properties'][k]["items"]["type"] )

                else: # empty array

                    if k not in output_schema['properties']:
                        output_schema['properties'].update( { k : { "type": "array" } } )
                    else:
                        if output_schema['properties'][k]["type"] != "array":
                            print( f"WARNING: type mismatch for key '{k}' where 'object' != ", output_schema['properties'][k]["type"] )

                continue


            # handle plain types except string, no recursion here

            if  type(v) is int:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "integer" } } )
                else:
                    if output_schema['properties'][k]["type"] != "integer":
                        print( f"WARNING: type mismatch for key '{k}' where 'integer' != ", output_schema['properties'][k]["type"] )

                continue

            if  type(v) is float:
    
                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "number" } } )
                else:
                    if output_schema['properties'][k]["type"] != "number":
                        print( f"WARNING: type mismatch for key '{k}' where 'number' != ", output_schema['properties'][k]["type"] )

                continue





            # handle string types with special sub types, no recursion here

            if  type(v) is str:

                if k not in output_schema['properties']:
                    output_schema['properties'].update( { k : { "type": "string" } } )

                continue


            print( "unhandled type ", type(v) )

    def addJsonObject( self, object ):
        print("add a json object")

        self.recursiveScan( object, self.schema )

    def getSchema( self ):
        return self.schema



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
                    case _:
                        print(f'unknown column type{type} for key {k}')
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
        generator= SchemaGenerator()

        for input_file in args.input:

            print("    INPUT ", input_file)

            with open(input_file, "r") as f:
                input = json.load(f)
                builder.add_object(input)
                generator.addJsonObject(input)

        schema = builder.to_json(indent=4)
        check_schema( json.loads(schema) )

        f = open("SCHEMA.json", "w")
        f.write(schema)
        f.close()


        schemanew= generator.getSchema()

        f = open("SCHEMA.new.json", "w")
        f.write(json.dumps(schemanew, indent=4))
        f.close()

