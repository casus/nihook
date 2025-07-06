#!/usr/bin/env python3

import os
import time
import json
from flask import Flask, request, jsonify, send_file

import gitlab
import nocodb
import yaml


from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

import base64
from urllib.parse import urlparse

import process_files_from_gitlab
import table_from_schema

METADATA_FILENAME= "DATASET.json"
SCHEMA_FILENAME= "SCHEMA.json"

AUTO_COMMIT_MESSAGE= "automatic commit by post-commit hook"
AUTO_COMMIT_METADATA_KEY= "auto-commit"
AUTO_COMMIT_METADATA_VAL= "1"

ADMIN_OVERRIDE_MESSAGE= "admin override"

BATCH_SIZE = 100

TABLE_ID = ""
# base file names that require further processing via the following function
SPECIAL_FILENAMES= {
    'DATASET.json'
}






# logging
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
import sys
from pathlib import Path

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

# dictionary of all known gitlab projects and their access tokens
gitlab_projects= {}

auth_file_path = Path(__file__).resolve().parent.parent / "auth" / "data" / "auth.json"


@app.route('/', methods=['GET'])
def index():
    # authentication= auth.Auth(auth_file_path)
    # authentication.debug()
    return "I work"


@app.route('/webhooks/push', methods=['POST'])
def webhook_push():
    """
    Flask based webhook for push events in gogs
    """

    log.debug("START: webhook_push() called")
    start_time = time.time()

    authentication= auth.Auth(auth_file_path)

    headers= request.headers

    #print("Headers:")
    #print(headers)

    # tableid= headers['X-Webhook-Nocodbtableid']
    tableid = TABLE_ID
    print("Table ID = ", tableid)
    # user= headers['X-Webhook-User']
    # secret= headers['X-Webhook-Secret']

    # if not authentication.check( user, secret ):
    #     return jsonify('authentication failed'), 401 # Although the HTTP standard specifies "unauthorized", semantically this response means "unauthenticated". That is, the client must authenticate itself to get the requested response. 

    event = request.get_json()

    with open("first-gitlab-webhook.log","a") as file:
        print(json.dump(event, file, indent=4))


    print( " ### Summary ### " )
    project= event['project']
    commit_before= event['before']
    commit_after= event['after']

#   e.g."ref": "refs/heads/master",
    ref= event['ref']

    print( "Project : ", project['name'], " id ", project['id'], " previous commit id ", commit_before, " current commit id ", commit_after )
    projectid= project['id']
    print( "URL : ", project['web_url'] )
    projecturl= project['web_url']
    print( "PATH : ", project['path_with_namespace'] )

    print( "Number commits: ", len(event['commits']) )
    print( "Total commits: ", event['total_commits_count'] )

    # old from evn var
    # gitlab_host = os.getenv('GITLAB_HOST', "http://localhost")
    # gitlab_access_token = os.getenv('GITLAB_ACCESS_TOKEN', "none")

    # new: get gitlab access token from 'gitlab.projects' file

    parsed_uri = urlparse(projecturl)
    gitlab_host= '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

    if projecturl in gitlab_projects:

        gitlab_access_token= gitlab_projects[projecturl]
    else:
        gitlab_access_token= "none"

    if "none" == gitlab_access_token:
        print("WARNING: no GITLAB_ACCESS_TOKEN given in local file 'gitlab.projects', abort here")
        return False

    # create gitlab connection object only once

    # == It would be better to check nocodb credentials before connecting to gitlab
    # create Nocodb Table object only once becasue the same table will be used anyway
    port = os.getenv('NOCODB_PORT', '8080')  # Default to 8080
    nocodb_host = f"http://localhost:{port}"

    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True) # optional

    if 'none' == nocodb_host:
        print("WARNING: no NOCODB_HOST given as environment variable, abort here")
        return False

    if 'none' == nocodb_token:
        print("WARNING: no NOCODB_TOKEN given as environment variable, abort here")
        return False

    gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
    gitlab_project= gl.projects.get(id=projectid)


    table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )

    for c in event['commits']:
        print("    Commit ", c['id'], " at ", c['timestamp'] )

        for action in ['added','modified','removed']:

            print(f"        {action}: ", len(c[action]))
            for filename in c[action]:

                log.debug(f"Handle: {filename} {action}")

                dirname, basename= os.path.split(filename)
                if basename in SPECIAL_FILENAMES:
                    print(f"            handle {dirname} {basename}")
                    res= process_files_from_gitlab.process_special_files( action, 
                        gitlab_project, projecturl, ref, commit_before, commit_after, dirname, basename, table )

                    log.debug(f"Result: {res}")

    log.debug("END: webhook_push() finished successfully")
    return jsonify('no errors'), 200

if __name__ == '__main__':


    host = os.getenv('HOOK_HOST', '127.0.0.1')
    port = os.getenv('HOOK_PORT', '5000')


    # read in all known gitlab projects and their access tokens
    gitlab_projects= {}
    with open("config.yml", 'r') as f:
        config = yaml.safe_load(f)
    gitlab_projects = config["projects"]

    print("Known gitlab projects:")
    for i in gitlab_projects:
        print("    ", i)


    nocodb_port = os.getenv('NOCODB_PORT', '8080')  # Default to 8080
    nocodb_host = f"http://localhost:{nocodb_port}"

    nocodb_token = os.getenv('NOCODB_TOKEN', 'none')
    nocodb_ssl_cert = os.getenv('NOCODB_SSL_CERT', True) # optional

    base_id = os.getenv("BASE_ID", "none")
    schema= {}
    script_dir = Path(__file__).parent
    file_path = script_dir / "SCHEMA.json"
    with open(file_path, "r") as f:
        schema= json.load(f)
    
    TABLE_ID = table_from_schema.create_new_table_from_schema(nocodb_host, nocodb_token, nocodb_ssl_cert, base_id, "Default-Table", schema)
    print("New table was created!")


    app.run(host=host, port=int(port))
