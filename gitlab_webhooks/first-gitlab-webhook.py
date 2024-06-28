#!/usr/bin/env python3

import os
import time
import json
from flask import Flask, request, jsonify, send_file

from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError


METADATA_FILENAME= "DATASET.json"
SCHEMA_FILENAME= "SCHEMA.json"

AUTO_COMMIT_MESSAGE= "automatic commit by post-commit hook"
AUTO_COMMIT_METADATA_KEY= "auto-commit"
AUTO_COMMIT_METADATA_VAL= "1"

ADMIN_OVERRIDE_MESSAGE= "admin override"

BATCH_SIZE = 100



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
    print( "Project : ", project['name'] )
    print( "URL : ", project['web_url'] )
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
            print("            ", filename)
        print("        Removed: ", len(c['removed']))
        for filename in c['removed']:
            print("            ", filename)

    log.debug("END: webhook_push() finished successfully")
    return jsonify('no errors'), 200


if __name__ == '__main__':
    host = os.getenv('HOOK_HOST', '127.0.0.1')
    port = os.getenv('HOOK_PORT', '5000')
    app.run(host=host, port=int(port))
