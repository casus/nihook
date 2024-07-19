# functionality to do special things with certain files from commits in gitlab webhooks

import os
import time
import json
import gitlab
import base64

import nocodb
import prepare_json


def process_special_files( operation, projectid, projecturl, ref, dirname, basename ):

    gitlab_host = os.getenv('GITLAB_HOST', "http://localhost")
    gitlab_access_token = os.getenv('GITLAB_ACCESS_TOKEN', "none")
    nocodb_host = os.getenv('NOCODB_HOST', 'none')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True) # optional

    if 'none' == nocodb_host:
        print("WARNING: no NOCODB_HOST given as environment variable, abort here")
        return

    if 'none' == nocodb_token:
        print("WARNING: no NOCODB_TOKEN given as environment variable, abort here")
        return

    # TODO 
    # - look up central Nocodb table, if we find an entry for projecturl
    # - then get the matchin entry which has to include a Nocodb table id where this DATASET.json should be inserted
    # ... shortcut it for now

    nocodb_tableid = os.getenv('NOCODB_TABLE_ID', 'none')
    if 'none' == nocodb_tableid:
        print("WARNING: no NOCODB_TABLE_ID given as environment variable, abort here")
        return

    print("WARNING: NOCODB_TABLE_ID as a environment variable is only as a temporary shortcut")


    ## try to download a "DATASET.json" file

    ref_prefix, ref_suffix= os.path.split(ref)

    print("processing: ", dirname, basename, " with ", operation, 
        " in project ", projectid, projecturl, ref, ref_prefix, ref_suffix )

    if 'DATASET.json' == basename:

        # try to download the file
        print("try download")

    else:

        print("ignore this file")
        return


    gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
    project= gl.projects.get(id=projectid)
    f= project.files.get( file_path= os.path.join(dirname,basename), ref= ref ) # get the base64 encoded content

    # file_content = base64.b64decode(f.content) ##.decode("utf-8")
    ##file_content= base64.b64decode(f.content).decode("utf-8") ##.decode("unicode_escape")

    file_content= f.decode()

    # get the base64 encoded content
    #print(file_content)
    #print(file_content.replace('\\n','\n'))
    #print( json.dumps(file_content,indent=4))

    # metadata= f.decode()
    # print(metadata)

    j= json.loads(file_content)

    #print( json.dumps(j,indent=4) )



    ### recreate the complete URL to the dir that contains the DATASET.json

    url=projecturl + "/-/tree/" + ref_suffix + "/" + dirname
    print("URL= ",url)

    # enter in existing Nocodb table

    table= nocodb.Table( nocodb_tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )

    data= prepare_json.prepare_input( j, extra={ 'URL': url, 'status': "current" } )
    res= table.insert(data)
    print( "    RESULT: ", json.dumps(res,indent=4) )

