#!/usr/bin/env python3

import os
import time
import json
from flask import Flask, request, jsonify, send_file

import gitlab

from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

import base64

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


def process_special_files( operation, projectid, projecturl, ref, dirname, basename ):

    gitlab_host = os.getenv('GITLAB_HOST', "http://localhost")
    gitlab_access_token = os.getenv('GITLAB_ACCESS_TOKEN', "none")

    print("processing: ", dirname, basename, " with ", operation )

    if 'DATASET.json' == basename:

        # try to download the file
        print("try download")

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

    print( json.dumps(j,indent=4) )




# logging
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
import sys

LOGFILE= "push-hook.log"

log = logging.getLogger('')
log.setLevel(logging.INFO)


ch = logging.StreamHandler(sys.stdout)
log.addHandler(ch)

#fh = handlers.RotatingFileHandler(LOGFILE, maxBytes=(1048576*5), backupCount=7)
fh = handlers.RotatingFileHandler(LOGFILE)
log.addHandler(fh)


app = Flask(__name__)


@app.route('/webhooks/push', methods=['POST'])
def webhook_push():
    """
    Flask based webhook for push events in gogs
    """

    log.debug("START: webhook_push() called")
    start_time = time.time()

    event = request.get_json()

    with open("first-gitlab-webhook.log","a") as file:
        print(json.dump(event, file, indent=4))

    print( " ### Summary ### " )

    project= event['project']

    ref= event['ref']

    print( "Project : ", project['name'], " id ", project['id'] )
    projectid= project['id']
    print( "URL : ", project['web_url'] )
    projecturl= project['web_url']
    print( "PATH : ", project['path_with_namespace'] )

    print( "Number commits: ", len(event['commits']) )
    print( "Total commits: ", event['total_commits_count'] )

    for c in event['commits']:
        print("    Commit ", c['id'], " at ", c['timestamp'] )

        print("        Added: ", len(c['added']))
        for filename in c['added']:
            print("            ", filename)

        print("        Modified: ", len(c['modified']))
        for filename in c['modified']:
            print("            ", filename, " --> ", os.path.basename(filename) )

            dirname, basename= os.path.split(filename)
            if basename in SPECIAL_FILENAMES:
                process_special_files( 'modified', projectid, projecturl, ref, dirname, basename )

        print("        Removed: ", len(c['removed']))
        for filename in c['removed']:
            print("            ", filename)

    log.debug("END: webhook_push() finished successfully")
    return jsonify('no errors'), 200


if __name__ == '__main__':
    host = os.getenv('HOOK_HOST', '127.0.0.1')
    port = os.getenv('HOOK_PORT', '5000')
    app.run(host=host, port=int(port))
