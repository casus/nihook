#!/usr/bin/env python3

import os
import time
import json
from flask import Flask, request, jsonify, send_file
from datetime import datetime

import gitlab
from nocodb_client import nocodb
from nocodb_client import table_from_schema


from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

import base64
from urllib.parse import urlparse

from const import HEADER_NOCO_DB_TABLE_ID
import process_files_from_gitlab

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
from api import api_bp
from api import authenticate

from gitlab_project_manager import (
    load_gitlab_projects
)
from utils import (HOST, PORT, NOCODB_HOST, NOCODB_TOKEN, NOCODB_SSL_CERT, DEBUG)

LOGDIR = Path("logs")
LOGFILE = LOGDIR / "push-hook.log"


# Ensure log directory exists
LOGDIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger('')
log.setLevel(logging.INFO)


ch = logging.StreamHandler(sys.stdout)
log.addHandler(ch)

#fh = handlers.RotatingFileHandler(LOGFILE, maxBytes=(1048576*5), backupCount=7)
fh = handlers.RotatingFileHandler(LOGFILE)
log.addHandler(fh)


app = Flask(__name__)
app.register_blueprint(api_bp)

# dictionary of all known gitlab projects and their access tokens
gitlab_projects= {}

auth_file_path = Path(__file__).resolve().parent.parent / "auth" / "data" / "auth.json"


def map_change_type(diff):
    if diff.get('new_file'):
        return 'added'
    elif diff.get('deleted_file'):
        return 'removed'
    else:
        return 'modified'

@app.route('/webhooks/upload-all-commits', methods=['POST'])
def webhhook_upload_all_commits():
    """
    Route in order to upload all "Dataset.json" files form all of the commits into a table
    """
    auth_result = authenticate()
    if auth_result:
        return auth_result  # immediately return 401 if auth fails
    headers = request.headers

    tableid = headers.get(HEADER_NOCO_DB_TABLE_ID)

    if (tableid == None):
        return jsonify({'error': f'{HEADER_NOCO_DB_TABLE_ID} is empty'}), 400

    data = request.get_json()
    project_url = data.get("project_url")

    if not project_url:
        return jsonify({'error': 'Missing "project_url" in request body'}), 400
    
    parsed_uri = urlparse(project_url)
    gitlab_host= '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    project_path = parsed_uri.path.lstrip('/')

    gitlab_projects = load_gitlab_projects()

    if project_url in gitlab_projects:
        gitlab_access_token= gitlab_projects[project_url]
    else:
        gitlab_access_token= "none"

    gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
    gitlab_project= gl.projects.get(project_path)
    # commits = gitlab_project.commits.list(get_all=True)

    all_commits = []
    seen_ids = set()
    branches = gitlab_project.branches.list()

    for branch in branches:
        branch_commits = gitlab_project.commits.list(all=True, ref_name=branch.name)
        for c in branch_commits:
            if c.id not in seen_ids:
                all_commits.append(c)
                seen_ids.add(c.id)

    commit_ids = [c.id for c in all_commits]

    # table= nocodb.Table( tableid, host=nocodb_host, auth_token=nocodb_token, verify=nocodb_ssl_cert )
    # print(commits)
    # commits_data = [commit.attributes for commit in commits]
    print(commit_ids)
    print(len(commit_ids))

    table= nocodb.Table( tableid, host=NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT )
    if (table.count()["count"] > 0):
        return jsonify({'error': 'Table is not empty, please clear it first'}), 400

    for branch in branches:
        branch_commits = gitlab_project.commits.list(all=True, ref_name=branch.name)
        git_ref = f"refs/heads/{branch.name}"
        # Let's put the oldest commits first
        branch_commits.sort(key=lambda c: datetime.fromisoformat(c.committed_date.replace('Z', '+00:00')))
        branch_commits_ids = [c.id for c in branch_commits]
        for c in branch_commits:
            print("    Commit ", c.get_id(), " branch = ", branch.name )
            target_index = branch_commits_ids.index(c.id)
            commit_after = branch_commits_ids[target_index + 1] if target_index + 1 < len(branch_commits_ids) else None
            commit_before = branch_commits_ids[target_index - 1] if target_index > 0 else None

            commit_diffs = c.diff(get_all=True)
            for diff in commit_diffs:
                change_type = map_change_type(diff)
                filename = diff['new_path']

                log.debug(f"Handle: {filename} {change_type}")

                dirname, basename= os.path.split(filename)
                if basename in SPECIAL_FILENAMES:
                    print(f"            handle {dirname} {basename}")
                    res= process_files_from_gitlab.process_special_files( change_type, 
                        gitlab_project, project_url, git_ref, commit_before, commit_after, dirname, basename, table )

                    log.debug(f"Result: {res}")

    return jsonify({'message': 'All commits were scanned and added to the table'}), 201


    

@app.route('/webhooks/push', methods=['POST'])
def webhook_push():
    """
    Flask based webhook for push events in gogs
    """

    log.debug("START: webhook_push() called")
    start_time = time.time()


    headers= request.headers

    auth_result = authenticate()
    if auth_result:
        return auth_result  # immediately return 401 if auth fails

    tableid= headers.get(HEADER_NOCO_DB_TABLE_ID)

    event = request.get_json()

    with open(LOGDIR / "/app/logs/first-gitlab-webhook.log", "a") as file:
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
    gitlab_projects = load_gitlab_projects()

    if projecturl in gitlab_projects:
        gitlab_access_token= gitlab_projects[projecturl]
    else:
        gitlab_access_token= "none"

    if "none" == gitlab_access_token:
        print("WARNING: no GITLAB_ACCESS_TOKEN given in local file 'gitlab.projects', abort here")
        return False

    # create gitlab connection object only once


    if None == NOCODB_TOKEN:
        print("WARNING: no NOCODB_TOKEN given as environment variable, abort here")
        return False

    gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
    gitlab_project= gl.projects.get(id=projectid)


    # create Nocodb Table object only once becasue the same table will be used anyway
    table= nocodb.Table( tableid, host=NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT )

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

    # read in all known gitlab projects and their access tokens
    gitlab_projects = load_gitlab_projects()

    print("Known gitlab projects:")
    for i in gitlab_projects:
        print("    ", i)


    if (DEBUG == True):
        log.setLevel(logging.DEBUG)
        # base_id = os.getenv("BASE_ID", "none")
        # schema= {}
        # script_dir = Path(__file__).parent
        # file_path = script_dir / "SCHEMA.json"
        # if (file_path.exists()):
        #     with open(file_path, "r") as f:
        #         schema= json.load(f)

        #     TABLE_ID = table_from_schema.create_new_table_from_schema(NOCODB_HOST, NOCODB_TOKEN, NOCODB_SSL_CERT, base_id, "Default-Table", schema)
        #     print("New table was created!")
        #     print(TABLE_ID)
        # else:
        #     log.info("Couldn't find file with the path = " + file_path)


    app.run(host=HOST, port=int(PORT))
