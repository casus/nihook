# functionality to do special things with certain files from commits in gitlab webhooks

import os
import time
import json
import gitlab
import base64

from nocodb_client import nocodb
from nocodb_client import prepare_json


def process_special_files( operation, gitlab_project, projecturl, ref, commit_before, commit_after, dirname, basename, table ) -> bool:

    # double check here even though it should have been checked upstairs already
    if 'DATASET.json' != basename:

        print(f"ignore this file '{basename}'")
        return False

    ref_prefix, ref_suffix= os.path.split(ref)
    branch= ref_suffix

    # when DATASET.json was added, then read it and add a new row to the Nocodb table 
    if 'added' == operation:

        f= gitlab_project.files.get( file_path= os.path.join(dirname,basename), ref= ref ) # get the base64 encoded content
        file_content= f.decode()
        j= json.loads(file_content)

        ### recreate the complete URL to the dir that contains the DATASET.json

        url=projecturl + "/-/tree/" + ref_suffix + "/" + dirname
        # print("URL= ",url)

        data= prepare_json.prepare_input( j, extra={ 'URL': url, 'status': "current", 'branch': branch } )
        print("Data to be inserted: ")
        print( json.dumps(data,indent=4) )
        res= table.insert(data)
        print("inserted res: ", res)

        # return res


    if 'modified' == operation:

        url=projecturl + "/-/tree/" + ref_suffix + "/" + dirname
        # print("URL= ",url)

        # get the old entry
        old= table.list(where=f"(URL,eq,{url})" )
        # print(json.dumps(old,indent=4))

        assert 'list' in old

        # load data from gitlab -- needed in both cases below
        f= gitlab_project.files.get( file_path= os.path.join(dirname,basename), ref= ref ) # get the base64 encoded content
        file_content= f.decode()
        j= json.loads(file_content)
        #print( json.dumps(j,indent=4) )
        

        # of len == 0, then no old entry present -- can happen because webhook was inactive some time, ignore
        # len cannot be > 1 because the URL is the primary key
        if 1 == len(old['list']):

            old_record= old['list'][0]
            old_url= old_record['URL']

            # need to add the dirname in the end, otherwise multiple cases in the same commit get overwritten
            # assume that there can be only one DATASET.json or maybe other special file names (!) in the dir
            old_record['URL']= projecturl + "/-/tree/" + commit_before + "/" + dirname
            old_record['status']= 'replaced'
            old_record['branch']= branch

            # remove Nocodb's system fields
            old_record.pop('CreatedAt')
            old_record.pop('UpdatedAt')

            res= table.insert(old_record)
            print("inserted res: ", res)

            # if an existing entry was present, then change it according to the new data
            # let the 'index.id' hash unchanged if it was not changed in the 'DATASET.json' 
            # so one can track which changed versions belong together
            data= prepare_json.prepare_input( j, extra={ 'URL': url, 'status': "current", 'branch': branch } )

            res= table.update(data)
            print("updated res: ", res)

        else:

            # if no existing entry was present, then add the new entry

            data= prepare_json.prepare_input( j, extra={ 'URL': url, 'status': "current", 'branch': branch } )
            res= table.insert(data)
            print("inserted res: ", res)

    return True


    # when DATASET.json was removed, then 
    # - try to find it's previous Nocodb entry and change its status to 'deleted'
    # - change URL to the commit where one can find the old version
    #     - actually create a new table entry because the URL is the primary key which cannot be changed
    #     - then delete the original table entry instead
    if 'removed' == operation:

        url=projecturl + "/-/tree/" + ref_suffix + "/" + dirname
        # print("URL= ",url)

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

        # need to add the dirname in the end, otherwise multiple cases in the same commit get overwritten
        # assume that there can be only one DATASET.json or maybe other special file names (!) in the dir
        old_record['URL']= projecturl + "/-/tree/" + commit_before + "/" + dirname
        old_record['status']= 'deleted'

        # remove Nocodb's system fields
        old_record.pop('CreatedAt')
        old_record.pop('UpdatedAt')

        res= table.insert(old_record)
        print("inserted res: ", res)

        res= table.delete( { "URL": old_url } )
        print("deleted res: ", res)

        return True


    print(f"unknown operation '{operation}', skip")
    return False
