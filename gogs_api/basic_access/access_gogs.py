#!/usr/bin/env python3

import os
from nocodb.nocodb import NocoDBProject, APIToken
from nocodb.infra.requests_client import NocoDBRequestsClient
import requests
import json


def read_gogs( host, access_token ):

    url= host + "/api/v1/user/repos"
    headers = {"Authorization": "token "+access_token}

    print("  --> url ", url)
    print("  --> headers ", headers)

    response= requests.get( url, headers=headers, json={} )

    print("Status Code", response.status_code)
    print("JSON Response ", json.dumps( response.json(), indent=4))



if __name__ == '__main__':
    host = os.getenv('GOGS_HOST', 'http://localhost')
    token = os.getenv('GOGS_ACCESS_TOKEN', 'none')

    print( "    # access ", host, " with ", token )

    read_gogs(host,token)

