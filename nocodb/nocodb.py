# nocodb class

import os
import requests
import json
from typing import Optional, List

"""
Class for access to a NOCODB instance
"""
class Nocodb:

    def __init__(self, host, auth_token ):
        self.host= host
        self.auth_token= auth_token

    """ 
    List Bases
    List all base meta data
    https://meta-apis-v2.nocodb.com/#tag/Base/operation/base-list
    GET http://localhost:8080/api/v2/meta/bases/
    """
    def list_bases(self):

        url= f"{self.host}/api/v2/meta/bases/"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        # print( json.dumps(res, indent=4 ) )

        ret= {}
        for i in res['list']:
            # print( i['title'], i['id'] )
            ret[ i['title'] ]= i['id']

        return ret


    """
    Create Base
    Create a new base
    https://meta-apis-v2.nocodb.com/#tag/Base/operation/base-create
    POST http://localhost:8080/api/v2/meta/bases/
    """
    def create_base( self, title, color= None ):

        url= f"{self.host}/api/v2/meta/bases/"

        data= { "title": title}
        if color:
            data["color"]= color

        res= requests.post( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            data=data ).json()

        #print( json.dumps(res, indent=4 ) )

        return res


    def get_base_object(self,title):

        # check if such a table exists
        allbases= self.list_bases()

        if title in allbases:

            return Base( allbases[title], nocodb=self )

        else:

            return None

"""
Class for access to a NOCODB base == one database in the Nocodb instance
"""
class Base:

    def __init__(self, baseid, nocodb=None, host=None, auth_token=None  ):

        # Don't keep the parent Nocodb object because we can work without it
        # Accessing a Base only needs the baseid and the auth_token
        # Thus like this one can create a Base object without a Nocodb object.
        # #self.nocodb= nocodb 
        self.baseid= baseid

        if nocodb:

            self.host= nocodb.host
            self.auth_token= nocodb.auth_token

        else:

            assert None != host
            assert None != auth_token 

            self.host= host
            self.auth_token= auth_token

        self.info= self.get_base_info()
        self.metadata= self.get_base()

    def debug(self):
        print("class Base: ", self.baseid )
        print( json.dumps( self.info, indent=4 ) )
        print( json.dumps( self.metadata, indent=4 ) )


    """
    Get Base info
    Get info such as node version, arch, platform, is docker, rootdb and package version of a given base
    GET http://localhost:8080/api/v2/meta/bases/{baseId}/info
    """
    def get_base_info( self ):

        url= f"{self.host}/api/v2/meta/bases/{self.baseid}/info"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        #print( json.dumps(res, indent=4 ) )

        return res

    """
    Get Base
    Get the info of a given base
    https://meta-apis-v2.nocodb.com/#tag/Base/operation/base-read
    GET http://localhost:8080/api/v2/meta/bases/{baseId}
    """
    def get_base( self ):

        url= f"{self.host}/api/v2/meta/bases/{self.baseid}"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        #print( json.dumps(res, indent=4 ) )

        return res


    """
    List Tables
    List all tables in a given base
    https://meta-apis-v2.nocodb.com/#tag/DB-Table/operation/db-table-list
    GET http://localhost:8080/api/v2/meta/bases/{baseId}/tables
    """
    def list_tables(self):

        url= f"{self.host}/api/v2/meta/bases/{self.baseid}/tables"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        #print( json.dumps(res, indent=4 ) )

        ret= {}
        for i in res['list']:
            # print( i['title'], i['id'] )
            ret[ i['title'] ]= i['id']

        return ret


    """
    Read Table
    Read the table meta data by the given table ID
    https://meta-apis-v2.nocodb.com/#tag/DB-Table/operation/db-table-read
    GET http://localhost:8080/api/v2/meta/tables/{tableId}
    """
    def read_table(self,tableid):

        url= f"{self.host}/api/v2/meta/tables/{tableid}"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        #print( json.dumps(res, indent=4 ) )

        return res

    """
    Create Table
    Create a new table in a given base
    https://meta-apis-v2.nocodb.com/#tag/DB-Table/operation/db-table-create
    POST http://localhost:8080/api/v2/meta/bases/{baseId}/tables
    TBD
    """

    def get_table_object(self,title):

        # check if such a table exists
        alltables= self.list_tables()

        if title in alltables:

            return Table( self, alltables[title])

        else:

            return None



"""
Class for access to a NOCODB table
"""
class Table:

    def __init__(self, base, tableid ):

        # Don't keep the parent Base object because we can work without it
        # Accessing a Table only needs the tableid and the auth_token
        # Thus like this one can create a Table object without a Base object.
        #self.base= base
        self.tableid= tableid
        self.host= base.host
        self.auth_token= base.auth_token

        self.metadata= base.read_table(tableid)

    def debug(self):
        print("class Table: ", self.tableid )
        #print( json.dumps( self.metadata, indent=4 ) )
        columns= self.metadata["columns"]
        for c in columns:
            print( "    ", c["title"] )
