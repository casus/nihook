#!/usr/bin/env python3

import os
import time
import json
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from waitress import serve

import gitlab
from nihook_client import nocodb

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
LOGDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = LOGDIR / "webhook.log"

# Ensure log directory exists

log = logging.getLogger('')
log.setLevel(logging.INFO)

fh = handlers.RotatingFileHandler(LOGFILE, maxBytes=(1048576*5), backupCount=7)
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

    log.debug(f"commit_ids {commit_ids}, len {len(commit_ids)}")

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
            log.debug(f"    Commit {c.get_id()}, branch {branch.name}")
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
                    log.debug(f"            handle {dirname} / {basename}")
                    res= process_files_from_gitlab.process_special_files( change_type, 
                        gitlab_project, project_url, git_ref, commit_before, commit_after, dirname, basename, table )
                    log.debug(f"Result: {res}")

    return jsonify({'message': 'All commits were scanned and added to the table'}), 201


@app.route('/webhooks/ping', methods=['GET'])
def webhook_ping():
    """
    Simple route to test if the webhook is up and running
    """
    return jsonify({'message': 'pong'}), 200    

@app.route('/webhooks/push', methods=['POST'])
def webhook_push():
    """
    Flask based webhook for push events in gogs
    """

    start_time = time.time()
    log.debug(f"webhook_push() called at {start_time}")

    headers= request.headers
    log.debug(f"    headers:", extra= {"headers": headers})

    auth_result = authenticate()
    log.debug(f"    auth:", extra= {"auth_result": auth_result})
    if auth_result:
        return auth_result  # immediately return 401 if auth fails

    tableid= headers.get(HEADER_NOCO_DB_TABLE_ID)
    log.debug(f"    tableid:", extra= {"tableid": tableid})

    event = request.get_json()
    log.debug(f"    request:", extra= {"event": event})

    project= event['project']
    commit_before= event['before']
    commit_after= event['after']

#   e.g."ref": "refs/heads/master",
    ref= event['ref']

    log.debug(f"Project: {project['name']} with id {project['id']}, previous commit id {commit_before}, current commit id {commit_after}" )

    projectid= project['id']
    projecturl= project['web_url']
    log.debug(f"    projecturl {projecturl}")
    log.debug(f"    project path with namespace {project['path_with_namespace']}")

    log.debug(f"    number commits {len(event['commits'])}" )
    log.debug(f"    total commits {event['total_commits_count']}" )

    parsed_uri = urlparse(projecturl)
    gitlab_host= '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    gitlab_projects = load_gitlab_projects()

    if projecturl in gitlab_projects:
        gitlab_access_token= gitlab_projects[projecturl]
    else:
        gitlab_access_token= "none"

    if "none" == gitlab_access_token:
        log.error(f"no GITLAB_ACCESS_TOKEN for {projecturl} in local file 'gitlab.projects', abort")
        return jsonify({'error': 'Missing GITLAB_ACCESS_TOKEN'}), 401

    # create gitlab connection object only once

    if None == NOCODB_TOKEN:
        log.error(f"no NOCODB_TOKEN given as environment variable, abort")
        return jsonify({'error': 'Missing NOCODB_TOKEN'}), 401

    gl= gitlab.Gitlab( url= gitlab_host, private_token= gitlab_access_token )
    gitlab_project= gl.projects.get(id=projectid)


    # create Nocodb Table object only once becasue the same table will be used anyway
    table= nocodb.Table( tableid, host=NOCODB_HOST, auth_token=NOCODB_TOKEN, verify=NOCODB_SSL_CERT )

    for c in event['commits']:
        log.debug(f"    Commit {c['id']} at {c['timestamp']}" )

        for action in ['added','modified','removed']:

            log.debug(f"        {action}: {len(c[action])}")

            for filename in c[action]:

                log.debug(f"Handle: {filename} {action}")

                dirname, basename= os.path.split(filename)
                if basename in SPECIAL_FILENAMES:
                    log.debug(f"            handle {dirname} {basename}")

                    res= process_files_from_gitlab.process_special_files( action, 
                        gitlab_project, projecturl, ref, commit_before, commit_after, dirname, basename, table )
                    log.debug(f"res: ", extra={"res":res})

    end_time = time.time()
    log.debug(f"webhook_push() finished successfully at time {end_time}")
    return jsonify('no errors'), 200


if __name__ == '__main__':

    # read in all known gitlab projects and their access tokens
    gitlab_projects = load_gitlab_projects()
    log.debug(f"Known gitlab projects are:", extra= {"gitlab_projects": gitlab_projects})

    if True == DEBUG:

        # only in debug mode send everything to stdout as well
        ch = logging.StreamHandler(sys.stdout)
        log.addHandler(ch)

        log.setLevel(logging.DEBUG)
        log.debug(f"DEBUG MODE is ON with:")
        log.debug(f"    HOST= {HOST}")
        log.debug(f"    PORT= {PORT}, ")
        log.debug(f"    NOCODB_HOST= {NOCODB_HOST}")
        log.debug(f"    NOCODB_TOKEN= {NOCODB_TOKEN}")
        log.debug(f"    NOCODB_SSL_CERT= {NOCODB_SSL_CERT}")

    serve(app, host=HOST, port=int(PORT))
