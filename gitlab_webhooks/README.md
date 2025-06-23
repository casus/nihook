# Gitlab Webhooks

## Install

Flask needs to be in the same venv

    python3 -m venv venv
    . venv/bin/activate
    pip3 install flask json gitlab base64 dateutil requests hashlib

... or avail globally. (pandas is currently needed and probably not needed in the near future)


## Configuration

There are two config files which need to be present: `env.sh` and `gitlab.projects`.

### The `env.sh` file

The env.sh file defines a few environment variables that need to be there for webhook.py. They can also be exported manually. For an example look at `env.sh.template`or:

    export HOOK_HOST="111.22.3.15" # IP adress where the webhook will be listening
    export HOOK_PORT=5000 # port where the webhook will be listening
    export NOCODB_TOKEN="somekeywithan_underscoreinside" 
    export NOCODB_HOST="https://some.nocodb.instance"
    export NOCODB_SSL_CERT=cert/data_casus_science_interm.cer # location of an addl. SSL cert to use for REST API


### The `gitlab.projects` file
    
This file makes the gitlab API access key to a project known to thr webhook server. For an example look at `gitlab.projects.template` or:

	{
    	"https://codebase.helmholtz.cloud/some/gitlab/project": "glpat-1234567890ABCDEFGHIJ",
    	"https://codebase.helmholtz.cloud/knue/esa-hubble-picture-of-the-week.datalad/project": "glpat-1234567890ABCDEFGHIJ"
	}

This file must be available when the webhook server starts. After updating a key you need to restart the webhook server (for now).


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









