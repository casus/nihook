# Gitlab Webhooks

## Install

Flask needs to be in the same venv

    python3 -m venv venv
    . venv/bin/activate
    pip3 install flask python-dotenv jsonschema gitlab

... or avail globally

Run with all the environment variables defined in `env.sh`, compare `env.sh.template`:

    . env.sh
    ./first-gitlab-webhook.py

in this dir.


Useful ssh tunnel if you want to have the flask server running on the development host but test from the LakeFS host

    ssh -R<PORT>:localhost:<PORT> knuepf66@<LAKEFSHOST>

where <LAKEFSHOST> is accessible from the development host anyway.

