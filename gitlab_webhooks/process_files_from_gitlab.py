# functionality to do special things with certain files from commits in gitlab webhooks

import os
import time
import json
import gitlab
import base64

import nocodb
import prepare_json


def process_special_files( operation, projectid, projecturl, ref, commit_before, commit_after, dirname, basename, tableid= None ) -> bool:

    gitlab_host = os.getenv('GITLAB_HOST', "http://localhost")
    gitlab_access_token = os.getenv('GITLAB_ACCESS_TOKEN', "none")
    nocodb_host = os.getenv('NOCODB_HOST', 'none')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True) # optional

    if "none" == gitlab_access_token:
        print("WARNING: no GITLAB_ACCESS_TOKEN given as environment variable, abort here")
        return False

    if 'none' == nocodb_host:
        print("WARNING: no NOCODB_HOST given as environment variable, abort here")
        return False

    if 'none' == nocodb_token:
        print("WARNING: no NOCODB_TOKEN given as environment variable, abort here")
        return False

    # double check here even though it should have been checked upstairs already
    if 'DATASET.json' != basename:

        print(f"ignore this file '{basename}'")
        return False

    ## try to download a "DATASET.json" file

    ref_prefix, ref_suffix= os.path.split(ref)

    # print("processing: ", dirname, basename, " with ", operation, 
    #        " in project ", projectid, projecturl, ref, ref_prefix, ref_suffix )

    # when DATASET.json was added, then read it and add a new row to the Nocodb table 
    if 'added' == operation:

        gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
        project= gl.projects.get(id=projectid)
        f= project.files.get( file_path= os.path.join(dirname,basename), ref= ref ) # get the base64 encoded content
        file_content= f.decode()
        j= json.loads(file_content)
        #print( json.dumps(j,indent=4) )

        ### recreate the complete URL to the dir that contains the DATASET.json

        url=projecturl + "/-/tree/" + ref_suffix + "/" + dirname
        # print("URL= ",url)

        # enter in existing Nocodb table
        table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )

        data= prepare_json.prepare_input( j, extra={ 'URL': url, 'status': "current" } )
        res= table.insert(data)
        return res


    if 'modified' == operation:

        print("TODO action 'modified'")
        return False

    # when DATASET.json was removed, then 
    # - try to find it's previous Nocodb entry and change its status to 'deleted'
    # - change URL to the commit where one can find the old version
    #     - actually create a new table entry because the URL is the primary key which cannot be changed
    #     - then delete the original table entry instead
    if 'removed' == operation:

        url=projecturl + "/-/tree/" + ref_suffix + "/" + dirname
        print("URL= ",url)

        table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )

        # get the old entry
        old= table.list(where=f"(URL,eq,{url})" )
        # print(json.dumps(old,indent=4))

        assert 'list' in old

        if 0 == len(old['list']):

            # did not find an old entry, can happen if it was added to gitlab which the webhook was inactive, skip
            print("No matchin entry in DB, skip")
            return False

        assert 1 == len(old['list'])

        old_record= old['list'][0]
        old_url= old_record['URL']

        old_record['URL']= projecturl + "/-/commit/" + commit_before
        old_record['status']= 'deleted'

        # remove Nocodb's system fields
        old_record.pop('CreatedAt')
        old_record.pop('UpdatedAt')

        res= table.insert(old_record)
        res= table.delete( { "URL": old_url } )

        return True


    print(f"unknown operation '{operation}', skip")
    return False
