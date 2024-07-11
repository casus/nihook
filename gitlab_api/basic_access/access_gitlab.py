#!/usr/bin/env python3

import os
import gitlab
import json
import base64


def read_gitlab( host, access_token ):

    gl= gitlab.Gitlab( url= host, private_token= access_token )

    # optional, only tests auth
    gl.auth()

    # print(" #### Projects #### ")
    # # list all the projects
    # projects = gl.projects.list(iterator=True)
    # for project in projects:
    #     print( project.to_json(indent=4) )
    #     break;

    ## selected project -- id from webhook
    id= 12806
    project= gl.projects.get(id=12806)
    #pjs= project.to_json(indent=4) ## gives strin representation of json object
    d= project.asdict()
    print("Project: ", d['name'])
    print("Created at: ", d['created_at'])
    print("Last active: ", d['last_activity_at'])

    ## selected commit -- hash from webhook
    hash= '3816bf4deba2ac4b79332929c6e2ca70df609dbb'
    commit = project.commits.get(hash)
    print("Commit ", hash, ": ")
    print(commit.to_json(indent=4))

    # Access a file just like this, without a commit -- get file name and ref from webhook
    path= "README.md"
    ref= "refs/heads/master" # just "master" seems also to work
    print("File: ", path, ref)
    f= project.files.get(file_path= path, ref= ref)

    file_content = base64.b64decode(f.content).decode("utf-8")
    # get the base64 encoded content
    print(file_content)
    print( json.dumps(file_content,indent=4))

if __name__ == '__main__':
    host = os.getenv('GITLAB_HOST', "http://localhost")
    token = os.getenv('GITLAB_ACCESS_TOKEN', "none")

    print( "    # access ", host, " with ", token )

    read_gitlab(host,token)

