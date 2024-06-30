import os
from typing import Optional, List

import requests
from nocodb.nocodb import NocoDBProject, APIToken, JWTAuthToken
from nocodb.filters import LikeFilter, EqFilter, And
from nocodb.infra.requests_client import NocoDBRequestsClient
from requests import Response

# Usage with API Token
# client = NocoDBRequestsClient(
#     # Your API Token retrieved from NocoDB conf
#     APIToken(os.environ['NOCODB_TOKEN']),
#     # Your nocodb root path
#     "http://192.168.11.104:8080"
# )
#
# project = NocoDBProject(
#     "noco", # org name. noco by default
#     "myproject" # project name. Case sensitive!!
# )
#
# # Retrieve a page of rows from a table
# table_rows = client.table_row_list(project, "Table")
#
# print(table_rows)

vm_ip = 'http://192.168.11.104:8080'
api_url = f'{vm_ip}/api/v2/tables/mdxierqhk1ywvpc/records'


def table_list(view_id: Optional[str] = None,
               fields: Optional[List[str]] = None,
               sort: Optional[List[str]] = None,
               where: Optional[List[str]] = None,
               limit: Optional[int] = 25,
               shuffle: Optional[int] = 0,
               offset: Optional[int] = 0) -> Response:
    return requests.get(
        api_url,
        headers={"accept": "application/json", "xc-token": os.environ['NOCODB_TOKEN']},
        params={"viewId": view_id, "fields": fields, "sort": sort, "where": where, "limit": limit, "shuffle": shuffle,
                "offset": offset},
    )


def table_create() -> Response:
    return requests.post(
        api_url,
        headers={"accept": "application/json", "xc-token": os.environ['NOCODB_TOKEN'],
                 "Content-Type": "application/json"},
    )


def table_update() -> Response:
    return requests.patch(
        api_url,
        headers={"accept": "application/json", "xc-token": os.environ['NOCODB_TOKEN'],
                 "Content-Type": "application/json"},
    )


def table_delete(id: int) -> Response:
    return requests.delete(
        api_url,
        headers={"accept": "*/*", "xc-token": os.environ['NOCODB_TOKEN'],
                 "Content-Type": "application/json"},
        data={"id": id}
    )


response = table_list()
print(response.json())
