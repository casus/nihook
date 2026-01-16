# NiHook Data Repository Automation

The _NocoDB Integration Hooks_ are the webhooks who say "Ni!". 

They will integrate git data repositories with [NocoDB](https://nocodb.com/) / 
[NocoDB on github](https://github.com/nocodb/nocodb). 
Matching data repositories are standard git repositories or git-annex enabled git repositories 
or [Datalad](https://handbook.datalad.org/en/latest/) repositories.
When such repositories contain metadata in the form of DATASET.json metadata files, 
they will be synchronized to a linked NocoDB instance.

## Public example repository

There is a public data repository with example data used for tutorials etc. at 
the [Helmholtz GitLab Server](https://codebase.helmholtz.cloud/knue/esa-hubble-picture-of-the-week.datalad/project) and
a public view of the metadata inventory at 
the [CASUS data server](https://data.casus.science/7716/dashboard/#/nc/view/a44a2c02-e0b6-4fa7-ab5e-222f807f5f3a).


## Developer Guide: Setup

### Prerequisites

1. Ensure you have [Podman](https://podman.io/) or [Docker](https://docs.docker.com/engine/install/) 
and [Python](https://www.python.org/downloads/) installed on your server.

2. This project requires access to private GitLab repositories. To enable this:
   - Generate a new SSH key pair.
   - Add the **public** key to your GitLab account.
   - Place the **private key** (`id_rsa`) in the project’s root directory.

3. You need to install the submodules needed for this project. In order to do this you need to run 
   ```bash
   git submodule update --init --recursive
   ```
    Alternatevily you can initially clone the repo with all submodules using
    ```bash
    git clone --recurse-submodules git@codebase.helmholtz.cloud:casus-datalad/datalad_automation.git
    ```
4. If there are new commits in the submodules and you want to have the latest version you need to run 
    ```bash
   git submodule update --remote --recursive
   ```
---

### Build and Run

To build the Docker container:

- Run the script:  
  ```bash
  ./build.sh
  ```

- Or build it manually:  
  ```bash
  docker build -t webhook-nocodb .
  ```

Before running the container, make sure to configure the `.env` file. In particular:

- Remove `DEBUG=True` if deploying in **production mode**.

**What `DEBUG=True` does:**

- Disables user authentication for the webhook API.
- Automatically creates a Base and Table using `SCHEMA.json` from the `gitlab_webhooks` folder.
- Creates only a single container volume folder (`container_1`).
- Sets default ports:
  - `5000` for the Webhook API
  - `5555` for the NocoDB server

Then check the script `spin_up_new_instance.sh` and adjust the `PUBLIC_URL` variable from "https://data.casus.science" to 
what your public URL prefix will be. Then bring up the first instance (or later additional instances) with:

```bash
./spin_up_new_instance.sh
```

---

### Additional Notes

- **Port allocation:**  
  In production mode, ports are dynamically selected from the range `5001–5999`.

- **Volume handling:**  
  Each running container has its own mounted directory inside the `volumes/` folder, named `container_<ID>`. The ID is generated based on the start time.

- **User management:**  
  Each container volume includes a `manage.sh` script, which invokes `manage_users.py` with the container path as an argument. Use this to create, delete, or query users associated with a container.

---

## Client Guide: How to Use

### Prerequisites

1. Your repository must contain at least one `DATASET.json` file describing a dataset.  
   You also need a `SCHEMA.json` file, typically built based on several `DATASET.json` files.  
   Refer to this [example project](https://codebase.helmholtz.cloud/knue/esa-hubble-picture-of-the-week.datalad/project).

2. Obtain the following information from your administrator:
   - Webhook service IP address and port
   - Your webhook username and secret
   - NocoDB service IP address and port


---

### Setup Steps



1) 💻 Connect to the NocoDB instance and create a new base:
    https://data.casus.science/$NOCODB_PORT_NUMBER with initial credentials from your administrator
    - Keep the base ID == the last part of the URL when inside the new base

2) ⌨ Create a table from a SCHEMA.json in a Datalad project on Github:
    - Clone the repository
    git clone https://codebase.helmholtz.cloud/casus-datalad/nocodb_automation.git
    cd ./nocodb_automation
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    export NOCODB_HOST=${PUBLIC_URL}/${HOST_PORT_NOCODB}
    export NOCODB_TOKEN=${token}
    python ./src/nocodb_client/table_from_schema.py -b <base_id> -n <new-name-for-table> <path-to-SCHEMA.json>
        ... note the resulting table ID for later

3) 🔑 Create a Gitlab API token and give it to the webhook server
    - Go to your Gitlab project → Settings → Access tokens → Add new token
        - Pick a token name 'for webhook + NocoDB' or something else
        - Increase expiration date to 1 year from now (this is the maximum)
        - Select role 'Reporter' or higher
        - Select scopes 'read_api'
        - Click 'Create project access token'
    - On the following page copy the token (this is the only time it is shown to you)
    - Add a new line in 'config/projects.json' or give the token to your administrator:
        "<Gitlab project URL>" : "<the token>"
      ... which allows the webhook server to access your gitlab project 

4) 🎣 Configure the Gitlab webhook:
    - Go to your Gitlab project → Settings → Webhooks → Add new webhook
        - Pick a webhook name 'for NocoDB' or something else
        - Enter the URL https://data.casus.science/${HOST_PORT_WEBHOOK}/webhooks/push
        - Add Custom headers:
            X-Webhook-User: Your Username 
            X-Webhook-Secret: Your Secret 
            X-Webhook-Nocodbtableid: <table ID from step 3>
        - Select 'Push events' as the Trigger
        - Disable SSL verification
        - Click 'Add webhook'

✅ Now the webhook is active. The next time there is a 'git push' including commits 
which have new or changed 'DATASET.json' files, the webhook will automatically enter 
their contents to the NocoDB table.