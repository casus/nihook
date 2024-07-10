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
    https://meta-apis-v2.nocodb.com/#tag/Base
    List all base meta data
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
    Get Base info
    Get info such as node version, arch, platform, is docker, rootdb and package version of a given base
    http://localhost:8080/api/v2/meta/bases/{baseId}/info
    """
    def get_base_info( self, baseid ):

        url= f"{self.host}/api/v2/meta/bases/{baseid}/info"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        #print( json.dumps(res, indent=4 ) )

        return res

    """
    Get Base
    Get the info of a given base
    https://meta-apis-v2.nocodb.com/#tag/Base/operation/base-read
    http://localhost:8080/api/v2/meta/bases/{baseId}
    """
    def get_base( self, baseid ):

        url= f"{self.host}/api/v2/meta/bases/{baseid}"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        #print( json.dumps(res, indent=4 ) )

        return res



    """
    Create Base
    Create a new base
    https://meta-apis-v2.nocodb.com/#tag/Base/operation/base-create
    http://localhost:8080/api/v2/meta/bases/
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


