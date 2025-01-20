# Gitlab Webhooks

## Install

Flask needs to be in the same venv

    python3 -m venv venv
    . venv/bin/activate
    pip3 install flask json gitlab base64 dateutil requests hashlib

... or avail globally. (pandas is currently needed and probably not needed in the near future)


## Run

Run with all the environment variables defined in `env.sh`, compare `env.sh.template`:

    . env.sh
    ./webhook.py

in this dir.


### Optional SSH tunnel

Useful ssh tunnel if you want to have the flask server running on the development host but test from the LakeFS host

    ssh -R<PORT>:localhost:<PORT> knuepf66@<LAKEFSHOST>

where <LAKEFSHOST> is accessible from the development host anyway.


### Webhook configurations

There are 3 values that have to be passed by the webhook as additional headers.

* NOCODBTABLEID : the table ID that is returned by 'nocodb/create_table_from_example.py'
* USER and AUTH as added to the allowed users with 'auth/add_auth.py'. USER is the user name and AUTH is the secret auth token









