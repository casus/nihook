# nocodb class

import os
import requests
import json
from typing import Optional, List


class Nocodb:

    def __init__(self, host, auth_token ):
        self.host= host
        self.auth_token= auth_token


    def get_bases(self):

        url= self.host+"/api/v2/meta/bases/"

        res= requests.get( url,
            headers={"accept": "application/json", "xc-token": self.auth_token},
            params={} ).json()

        # print( json.dumps(res, indent=4 ) )

        ret= {}
        for i in res['list']:
            # print( i['title'], i['id'] )
            ret[ i['title'] ]= i['id']

        return ret


