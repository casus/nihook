#!/bin/bash

PARENT_DIR=$1
if [ -z "$PARENT_DIR" ]; then
  PARENT_DIR="./"
fi

echo "Spin up new NocoDB + webhook instance in parent dir ${PARENT_DIR}"

# hardcode here because internal to the container and probably no need to change it
PUBLIC_URL="https://data.casus.science"
HOOK_HOST=0.0.0.0
HOOK_PORT=5000
NOCODB_PORT=8080
DEBUG=${DEBUG:-False}

WEBHOOK_USERNAME="firstuser"
WEBHOOK_AUTH_SECRET=""

is_port_free() {
  ! lsof -i ":$1" >/dev/null 2>&1
}

# Function to find a valid pair of ports
find_valid_ports() {
  while :; do
    PORT1=$(shuf -i 5001-5999 -n 1)
    LAST3=$(printf "%03d" $((PORT1 % 1000)))  # Ensures leading zeroes
    PORT2="7$LAST3"

    if is_port_free "$PORT1" && is_port_free "$PORT2"; then
      echo "$PORT1 $PORT2"
      return
    fi
  done
}

if [ "$DEBUG" = "True" ]; then
  HOST_PORT_WEBHOOK=5555
  HOST_PORT_NOCODB=7555
else
  # Dynamically find free host ports
  read -r HOST_PORT_WEBHOOK HOST_PORT_NOCODB < <(find_valid_ports)
fi

# Create directories
VOLUME_DIR=$PARENT_DIR"nocodb_webhook_instance_${HOST_PORT_WEBHOOK}_${HOST_PORT_NOCODB}"
CONFIG_DIR=$VOLUME_DIR/config
AUTH_DIR=$VOLUME_DIR/auth
DB_DIR=$VOLUME_DIR/db
LOGS_DIR=$VOLUME_DIR/logs
mkdir -p "$CONFIG_DIR" "$VOLUME_DIR" "$AUTH_DIR" "$DB_DIR" "$LOGS_DIR"


# create the initial auth file

AUTH_FILE="${AUTH_DIR}/auth.json"
if [ ! -f "$AUTH_FILE" ]; then
    echo "{}" > "$AUTH_FILE"
    echo "📁 Created empty auth.json in $VOLUME_DIR"
fi
WEBHOOK_AUTH_SECRET=$(python3 src/auth/add_auth.py $WEBHOOK_USERNAME -f "$AUTH_FILE")
cp src/auth/manage_users.sh "$AUTH_DIR/manage_users.sh"
chmod +x "$AUTH_DIR/manage_users.sh"

CONFIG_FILE="${CONFIG_DIR}/nocodb.json"

# create the initial projects file
PROJECTS_FILE=$CONFIG_DIR/projects.json
cp projects.template.json "$PROJECTS_FILE"
cp src/project_manager_interactive/manage_projects.sh "$CONFIG_DIR/manage_projects.sh"
chmod +x "$CONFIG_DIR/manage_projects.sh"

# Run the container
podman run -d \
  -p "${HOST_PORT_WEBHOOK}":"${HOOK_PORT}" \
  -p "${HOST_PORT_NOCODB}":"${NOCODB_PORT}" \
  -v "$(realpath "$CONFIG_DIR")":/app/config/ \
  -v "$(realpath "$AUTH_DIR")":/app/auth/ \
  -v "$(realpath "$DB_DIR")":/app/db/ \
  -v "$(realpath "$LOGS_DIR")":/app/logs/ \
  -e NOCODB_PORT=$NOCODB_PORT \
  -e HOOK_HOST=$HOOK_HOST \
  -e HOOK_PORT=$HOOK_PORT \
  -e NC_PUBLIC_URL="${PUBLIC_URL}/${HOST_PORT_NOCODB}" \
  webhook-nocodb

# Wait for NocoDB to be ready
TRIES=30
until curl -s "http://localhost:$HOST_PORT_NOCODB/api/v1/health" | grep -q 'OK'; do
  if (( $TRIES < 1 )); then
    echo "NocoDB did not become ready in time, exiting."
    exit 1
  fi
  echo "Waiting for NocoDB to start on port $HOST_PORT_NOCODB..."
  TRIES=$((TRIES-1))
  sleep 2
done
sleep 4 # sleep 2 extra seconds so inside the container the following config file can be written
echo "NocoDB is up!"

# read token from 'nocodb.json'

if [ -f $CONFIG_FILE ]; then
  
  email=$(jq -r '.nocodb_email' "$CONFIG_FILE")
  password=$(jq -r '.nocodb_password' "$CONFIG_FILE")
  token=$(jq -r '.nocodb_secret_token' "$CONFIG_FILE")

else

  echo "ERROR: NocoDB config file ${CONFIG_FILE} not found, exit"
  exit -1
fi

GUIDE_FILE_PATH="$VOLUME_DIR/README.md"
# print usage info
cat <<EOF | tee "$GUIDE_FILE_PATH"
<Username>
<Purpose>

🟢 NocoDB and webhook servers running:
  👉 Webhook at ${PUBLIC_URL}:5000/${HOST_PORT_WEBHOOK}
  👉 NocoDB at ${PUBLIC_URL}/${HOST_PORT_NOCODB}
      NocoDB token: ${token}

# Next steps

1) 💻 Connect to the NocoDB instance and create a new base:
    ${PUBLIC_URL}/${HOST_PORT_NOCODB} with initial credentials ${email} : ${password}
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
        - Enter the URL ${PUBLIC_URL}:5000/${HOST_PORT_WEBHOOK}/webhooks/push
        - Add Custom headers:
            X-Webhook-User: ${WEBHOOK_USERNAME}
            X-Webhook-Secret: ${WEBHOOK_AUTH_SECRET}
            X-Webhook-Nocodbtableid: <table ID from step 2>
        - Select 'Push events' as the Trigger
        - Disable SSL verification
        - Click 'Add webhook'

✅ Now the webhook is active. The next time there is a 'git push' including commits 
which have new or changed 'DATASET.json' files, the webhook will automatically enter 
their contents to the NocoDB table.

EOF
