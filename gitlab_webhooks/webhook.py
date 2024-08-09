#!/usr/bin/env python3

import os
import time
import json
from flask import Flask, request, jsonify, send_file

import gitlab
import nocodb

from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

import base64

import process_files_from_gitlab


METADATA_FILENAME= "DATASET.json"
SCHEMA_FILENAME= "SCHEMA.json"

AUTO_COMMIT_MESSAGE= "automatic commit by post-commit hook"
AUTO_COMMIT_METADATA_KEY= "auto-commit"
AUTO_COMMIT_METADATA_VAL= "1"

ADMIN_OVERRIDE_MESSAGE= "admin override"

BATCH_SIZE = 100

# base file names that require further processing via the following function
SPECIAL_FILENAMES= {
    'DATASET.json'
}






# logging
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
import sys

import auth


LOGFILE= "push-hook.log"

log = logging.getLogger('')
log.setLevel(logging.INFO)


ch = logging.StreamHandler(sys.stdout)
log.addHandler(ch)

#fh = handlers.RotatingFileHandler(LOGFILE, maxBytes=(1048576*5), backupCount=7)
fh = handlers.RotatingFileHandler(LOGFILE)
log.addHandler(fh)


app = Flask(__name__)

authentication= None


@app.route('/webhooks/push', methods=['POST'])
def webhook_push():
    """
    Flask based webhook for push events in gogs
    """

    log.debug("START: webhook_push() called")
    start_time = time.time()

    headers= request.headers

    #print("Headers:")
    #print(headers)

    tableid= headers['Nocodbtableid']
    user= headers['User']
    secret= headers['Auth']

    if not authentication.check( user, secret ):
        return jsonify('authentication failed'), 401 # Although the HTTP standard specifies "unauthorized", semantically this response means "unauthenticated". That is, the client must authenticate itself to get the requested response. 

    event = request.get_json()

    with open("first-gitlab-webhook.log","a") as file:
        print(json.dump(event, file, indent=4))


    print( " ### Summary ### " )
    project= event['project']
    commit_before= event['before']
    commit_after= event['after']

    ref= event['ref']

    print( "Project : ", project['name'], " id ", project['id'], " previous commit id ", commit_before, " current commit id ", commit_after )
    projectid= project['id']
    print( "URL : ", project['web_url'] )
    projecturl= project['web_url']
    print( "PATH : ", project['path_with_namespace'] )

    print( "Number commits: ", len(event['commits']) )
    print( "Total commits: ", event['total_commits_count'] )


    # create gitlab connection object only once
    gitlab_host = os.getenv('GITLAB_HOST', "http://localhost")
    gitlab_access_token = os.getenv('GITLAB_ACCESS_TOKEN', "none")

    if "none" == gitlab_access_token:
        print("WARNING: no GITLAB_ACCESS_TOKEN given as environment variable, abort here")
        return False

    gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
    gitlab_project= gl.projects.get(id=projectid)

    # create Nocodb Table object only once becasue the same table will be used anyway
    nocodb_host = os.getenv('NOCODB_HOST', 'none')
    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True) # optional

    if 'none' == nocodb_host:
        print("WARNING: no NOCODB_HOST given as environment variable, abort here")
        return False

    if 'none' == nocodb_token:
        print("WARNING: no NOCODB_TOKEN given as environment variable, abort here")
        return False

    table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )

    for c in event['commits']:
        print("    Commit ", c['id'], " at ", c['timestamp'] )

        for action in ['added','modified','removed']:

            print(f"        {action}: ", len(c[action]))
            for filename in c[action]:

                dirname, basename= os.path.split(filename)
                if basename in SPECIAL_FILENAMES:
                    print(f"            handle {dirname} {basename}")
                    process_files_from_gitlab.process_special_files( action, 
                        gitlab_project, projecturl, ref, commit_before, commit_after, dirname, basename, table )

    log.debug("END: webhook_push() finished successfully")
    return jsonify('no errors'), 200

if __name__ == '__main__':


    host = os.getenv('HOOK_HOST', '127.0.0.1')
    port = os.getenv('HOOK_PORT', '5000')

    authentication= auth.Auth("auth")

    app.run(host=host, port=int(port))
