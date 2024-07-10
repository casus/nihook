#!/usr/bin/env python3

import os
import nocodb


if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_base = os.getenv('NOCODB_base', 'none')

    ndb= nocodb.Nocodb(nocodb_host,nocodb_token)
    ret= ndb.get_bases()
    for i in ret:
        print(i," --> ",ret[i])

