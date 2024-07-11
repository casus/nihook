#!/usr/bin/env python3

import sys
import os
import json
import nocodb


if __name__ == '__main__':

    nocodb_host = os.getenv('NOCODB_HOST', 'http://localhost')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')

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


    print( " ======== \n")

    base_name= "Getting Started"
    base= ndb.get_base_object( base_name  )

    if base:

        print("Found base ", base_name )
        base.debug()

    else:

        print("No such base, stop")
        sys.exit(1)

    print(" #### List tables: #### ")

    res= base.list_tables()
    #print( json.dumps( res, indent=4 ) )

    for t in res:
        print("    ", t, " --> ", res[t])

        # print( f" #### Read table {t["title"]} #### " )
        # res= base.read_table( t["id"] )
        # print( json.dumps( res, indent=4 ) )

    table_name= "testtable"
    table= base.get_table_object(table_name)

    if table:

        print("Found table ", table_name )
        table.debug()
    else:

        print("No such table, stop")
        sys.exit(1)
