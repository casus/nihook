#!/usr/bin/env python3

import os
import json
import nocodb


if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_base = os.getenv('NOCODB_base', 'none')


    ndb= nocodb.Nocodb(nocodb_host,nocodb_token)

    #res= ndb.create_base( "test-create-base", color= "#d25cca" )
    #print( json.dumps( res, indent=4 )  )

    ret= ndb.list_bases()
    for i in ret:

        print(i," --> ",ret[i])
        print()
        print( json.dumps( ndb.get_base_info( ret[i] ), indent=4 ) )
        print()
        print( json.dumps( ndb.get_base( ret[i] ), indent=4 ) )
        print()
        print()

