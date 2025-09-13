#!/bin/bash

PARENT_DIR=$1
if [ -z "$PARENT_DIR" ]; then
  PARENT_DIR="./"
fi

echo "Spin up new NocoDB + webhook instance in parent dir ${PARENT_DIR}"

# hardcode here because internal to the container and probably no need to change it
PUBLIC_URL="http://192.168.11.167"
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

CONFIG_FILE="${CONFIG_DIR}/nocodb.json"

# create the initial projects file
PROJECTS_FILE=$CONFIG_DIR/projects.json
cp projects.template.json "$PROJECTS_FILE"

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


# print usage info
echo ""
echo "🟢 NocoDB and webhook servers running:"
echo "  👉 Webhook at ${PUBLIC_URL}:${HOST_PORT_WEBHOOK}"
echo "  👉 NocoDB at ${PUBLIC_URL}:${HOST_PORT_NOCODB}"
echo "      NocoDB token: ${token}"
echo ""
echo "# Next steps"
echo ""
echo "1) 💻 Connect to the NocoDB instance and create a new base:"
echo "    ${PUBLIC_URL}:${HOST_PORT_NOCODB} with initial credentials ${email} : ${password}"
echo "    - Keep the base ID == the last part of the URL when inside the new base"
echo ""
echo "2) ⌨ Clone and setup the Gitlab repository with the manager script"
echo "    git clone https://codebase.helmholtz.cloud/casus-datalad/webhook_manager"
echo "    cd ./webhook_manager"
echo '    cat > .env <<EOL'
echo "    export SERVER=\"${PUBLIC_URL}:${HOST_PORT_WEBHOOK}\""
echo "    export USER=\"${WEBHOOK_USERNAME}\""
echo "    export SECRET=\"${WEBHOOK_AUTH_SECRET}\""
echo "3) 🛠 Create a table from a SCHEMA.json in a Datalad project on Github"
echo "    ./run-cli.sh"
echo "    Now enter '8' and follow the instructions"
echo "4) 🔑 Create a Gitlab API token and give it to the webhook server"
echo "    - Go to your Gitlab project → Settings → Access tokens → Add new token"
echo "        - Pick a token name 'for webhook + NocoDB' or something else"
echo "        - Increase expiration date to 1 year from now (this is the maximum)"
echo "        - Select role 'Reporter' or higher"
echo "        - Select scopes 'read_api'"
echo "        - Click 'Create project access token'"
echo "    - On the following page copy the token (this is the only time it is shown to you)"
echo "    - Add a new line in 'nocodb_webhook_instance_${HOST_PORT_WEBHOOK}_${HOST_PORT_NOCODB}/config/projects.json':"
echo "        \"<Gitlab project URL>\" : \"<the token>\""
echo "      ... which allows the webhook server to access your gitlab project "
echo "    🎁 Alternatively in order to add a new project you can also use the webhook manager script from the step 2:"
echo "    ./run-cli.sh"
echo "Now enter '5' and follow the instructions"
echo "4) 🎣 Configure the Gitlab webhook (If you haven't done it on the step 3):"
echo "    - Go to your Gitlab project → Settings → Webhooks → Add new webhook"
echo "        - Pick a webhook name 'for NocoDB' or something else"
echo "        - Enter the URL ${PUBLIC_URL}:${HOST_PORT_WEBHOOK}/webhooks/push"
echo "        - Add Custom headers:"
echo "            X-Webhook-User: ${WEBHOOK_USERNAME}"
echo "            X-Webhook-Secret: ${WEBHOOK_AUTH_SECRET}"
echo "            X-Webhook-Nocodbtableid: <table ID from step 2>"
echo "        - Select 'Push events' as the Trigger"
echo "        - Click 'Add webhook'"
echo ""
echo "✅ Now the webhook is active. The next time there is a 'git push' including commits "
echo "which have new or changed 'DATASET.json' files, the webhook will automatically enter "
echo "their contents to the NocoDB table."
echo ""