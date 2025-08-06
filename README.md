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

1. After receiving credentials and service info from your admin, use the [manager script](https://here_should_be_a_link_to_manager_script) to create a new table using your `SCHEMA.json`.

2. After successful table creation, copy the table ID. You’ll see a response like:

   ```json
   {
     "message": "Table created successfully",
     "table": "m2hh0t4oyshybv8"
   }
   ```

   Here, `m2hh0t4oyshybv8` is the table ID.

3. If you have many commits with `DATASET.json` files to upload, use the manager script again. The `Upload All Commits to Table` option will help.

4. Before adding a webhook to your repository, register your repo with an access token in the webhook service. Use the manager script and follow these steps:

   - Go to **GitLab → Settings → Access Tokens**.
   - Create a new token:
     - **Name**: Choose any
     - **Expiration Date**: Optional
     - **Role**: `Reporter`
     - **Scopes**: `read_api`
   - Click **Create project access token** and copy the token.
   - Use the manager script option `Add GitLab Project` to register your repo and token.

5. Add a webhook to your GitLab repository:

   - Navigate to **Settings → Webhooks → Add new webhook**
   - Set the URL:

     ```
     https://<Webhook-IP>:<Port>/webhooks/push
     ```

     Example:

     ```
     https://192.168.11.167:5000/webhooks/push
     ```

   - Add these custom headers:

     ```
     X-Webhook-User: Your-Webhook-Username
     X-Webhook-Secret: Your-Webhook-Secret
     X-Webhook-Nocodbtableid: Your-NocoDB-Table-ID
     ```

   - In **Trigger**, select only:

     ```
     Push events
     ```

   - Ensure **"Enable SSL verification"** is checked.

   - Click **Add webhook**.

   - Test the setup by clicking **Test → Push events**.

---

### NocoDB usage
By default 
* your login is `admin@gmail.com`
* your password is `12345678`

Change it once you logged in!
