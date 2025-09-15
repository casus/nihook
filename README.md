# Datalad Automation

Codebase for integrations and automations for [Datalad](https://handbook.datalad.org/en/latest/) repositories.

---

## Developer Guide: Setup

### Prerequisites

1. Ensure you have both [Docker](https://docs.docker.com/engine/install/) and [Python](https://www.python.org/downloads/) installed on your machine.

2. This project requires access to private GitLab repositories. To enable this:
   - Generate a new SSH key pair.
   - Add the **public** key to your GitLab account.
   - Place the **private key** (`id_rsa`) in the project’s root directory.

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

To run the container:

```bash
./run.sh
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

3. To use the [manager script](https://here_should_be_a_link_to_manager_script), ensure [Python](https://www.python.org/downloads/) is installed on your machine.

---

### Setup Steps


1) 💻 Connect to the NocoDB instance and create a new base:
    htttps://data.casus.science/$NOCODB_PORT_NUMBER with initial credentials from your administrator
    - Keep the base ID == the last part of the URL when inside the new base

2) ⌨ Clone and setup the Gitlab repository with the manager script
    git clone https://codebase.helmholtz.cloud/casus-datalad/webhook_manager
    cd ./webhook_manager
    cat > .env <<EOL
    export SERVER="htttps://data.casus.science/$WEBHOOK_PORT_NUMBER"
    export USER="Your Username"
    export SECRET="Your Secret"
3) 🛠 Create a table from a SCHEMA.json in a Datalad project on Github
    ./run-cli.sh
    Now enter '8' and follow the instructions
4) 🔑 Create a Gitlab API token and give it to the webhook server
    - Go to your Gitlab project → Settings → Access tokens → Add new token
        - Pick a token name 'for webhook + NocoDB' or something else
        - Increase expiration date to 1 year from now (this is the maximum)
        - Select role 'Reporter' or higher
        - Select scopes 'read_api'
        - Click 'Create project access token'
    - On the following page copy the token (this is the only time it is shown to you)
    - Add a new line in 'nocodb_webhook_instance_$WEBHOOK_PORT_$NOCODB_PORT/config/projects.json':
        "<Gitlab project URL>" : "<the token>"
      ... which allows the webhook server to access your gitlab project 
    🎁 Alternatively in order to add a new project you can also use the webhook manager script from the step 2:
    ./run-cli.sh
Now enter '5' and follow the instructions
4) 🎣 Configure the Gitlab webhook (If you haven't done it on the step 3):
    - Go to your Gitlab project → Settings → Webhooks → Add new webhook
        - Pick a webhook name 'for NocoDB' or something else
        - Enter the URL htttps://data.casus.science/$WEBHOOK_PORT/webhooks/push
        - Add Custom headers:
            X-Webhook-User: Your Username (the same as on the step 2)
            X-Webhook-Secret: Your Secret (the same as on the step 2)
            X-Webhook-Nocodbtableid: <table ID from step 2>
        - Select 'Push events' as the Trigger
        - Click 'Add webhook'

✅ Now the webhook is active. The next time there is a 'git push' including commits 
which have new or changed 'DATASET.json' files, the webhook will automatically enter 
their contents to the NocoDB table.

