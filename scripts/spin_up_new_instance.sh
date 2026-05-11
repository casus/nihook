#!/bin/bash

PARENT_DIR="${1:-./}"
# Ensure PARENT_DIR ends with a slash
if [[ "${PARENT_DIR}" != */ ]]; then
  PARENT_DIR="${PARENT_DIR}/"
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"

# If an env file exists, load it
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi
echo "Spin up new NocoDB + webhook instance in parent dir ${PARENT_DIR}"

PUBLIC_URL=${PUBLIC_URL:-"https://data.casus.science"}
HOOK_HOST=${HOOK_HOST:-0.0.0.0} # internal port inside the container
HOOK_PORT=${HOOK_PORT:-5000}    # internal port inside the container
NOCODB_PORT=${NOCODB_PORT:-8080}  # internal port inside the container
DEBUG=${DEBUG:-False}
NOCODB_SSL_CERT=${NOCODB_SSL_CERT:-True}


if [ "$DEBUG" = "True" ]; then
  echo "⚠️ DEBUG mode active: using fixed ports"
else
  echo "🔎 Searching for free ports..."
fi

echo "🔒 NOCODB_SSL_CERT is ${NOCODB_SSL_CERT}"


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

# Determine URLs based on whether PUBLIC_URL is an IP address (direct ports) or domain (proxied)
# Remove protocol
TEMP_HOST="${PUBLIC_URL#*://}"

if [[ "$TEMP_HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # It's an IP address: assume direct port usage
    WEBHOOK_URL_BASE="${PUBLIC_URL}:${HOST_PORT_WEBHOOK}"
    NOCODB_URL_BASE="${PUBLIC_URL}:${HOST_PORT_NOCODB}"
    NC_PUBLIC_URL_ARG=""
    echo "Using direct ports for webhook and NocoDB: ${WEBHOOK_URL_BASE} and ${NOCODB_URL_BASE}"
else
    # It's a domain: assume proxy usage
    WEBHOOK_URL_BASE="${PUBLIC_URL}:5000/${HOST_PORT_WEBHOOK}"
    NOCODB_URL_BASE="${PUBLIC_URL}/${HOST_PORT_NOCODB}"
    NC_PUBLIC_URL_ARG="-e NC_PUBLIC_URL=${NOCODB_URL_BASE}"
fi

# Run the container
podman run -d \
  -p "${HOST_PORT_WEBHOOK}":"${HOOK_PORT}" \
  -p "${HOST_PORT_NOCODB}":"${NOCODB_PORT}" \
  -v "$(realpath "$CONFIG_DIR")":/app/config/:z \
  -v "$(realpath "$AUTH_DIR")":/app/auth/:z \
  -v "$(realpath "$DB_DIR")":/app/db/:z \
  -v "$(realpath "$LOGS_DIR")":/app/logs/:z \
  -e NOCODB_PORT="$NOCODB_PORT" \
  -e HOOK_HOST="$HOOK_HOST" \
  -e HOOK_PORT="$HOOK_PORT" \
  $NC_PUBLIC_URL_ARG \
  -e NOCODB_SSL_CERT="$NOCODB_SSL_CERT" \
  -e DEBUG="$DEBUG" \
  --restart=always \
  nihook

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

if [ -f "$CONFIG_FILE" ]; then
  
  email=$(jq -r '.nocodb_email' "$CONFIG_FILE")
  password=$(jq -r '.nocodb_password' "$CONFIG_FILE")
  token=$(jq -r '.nocodb_secret_token' "$CONFIG_FILE")

else

  echo "ERROR: NocoDB config file ${CONFIG_FILE} not found, exit"
  exit 1
fi

GUIDE_FILE_PATH="$VOLUME_DIR/README.md"
# print usage info
cat <<EOF | tee "$GUIDE_FILE_PATH"
<Username>
<Purpose>

🟢 NocoDB and webhook servers running:
  👉 Webhook at ${WEBHOOK_URL_BASE}
  👉 NocoDB at ${NOCODB_URL_BASE}
      NocoDB token: ${token}

      🛠 DEBUG is '${DEBUG}'
      🔒 SSL certificate checking is '${NOCODB_SSL_CERT}'

# Next steps

1) 💻 Connect to the NocoDB instance and create a new base:
    ${NOCODB_URL_BASE} with initial credentials ${email} : ${password}
    - Keep the base ID == the last part of the URL when inside the new base

2) ⌨ Create a table from a SCHEMA.json in a Datalad project on Github:
    - Either use an existing installation of NiHook-Client or make a new one
        - 2a) It is recommended to include it in your data repository as a submodule, do it via:
            - cd to the data directory 
            - Call:  

            \`\`\`
            git submodule add https://codebase.helmholtz.cloud/casus-datalad/nihook-client.git
            \`\`\`
            - ...
        - 2b) Alternatively, install it into a separate Python VENV (an existing one or a new one):
            \`\`\`
            python3 -m venv venv 
            source venv/bin/activate
            \`\`\`
            - Clone the repository
            \`\`\`
            git clone https://codebase.helmholtz.cloud/casus-datalad/nihook-client.git
            pip install -r nihook-client/requirements.txt
            pip install nihook-client/
            \`\`\`
    - Export the following environment variables:
        \`\`\`
        export NOCODB_HOST=${NOCODB_URL_BASE}
        export NOCODB_TOKEN=${token}
        export NOCODB_SSL_CERT="" # only in case you want to disable SSL certificate checking 
        \`\`\`
    - Run 

        \`\`\`
        python ./nihook-client/table_from_schema.py -b <base_id> -n <new-name-for-table> <path-to-SCHEMA.json> 
        \`\`\`
        - Note down the resulting table ID for later

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
        - Enter the URL ${WEBHOOK_URL_BASE}/webhooks/push
        - Add Custom headers:
            * X-Webhook-User: ${WEBHOOK_USERNAME}
            * X-Webhook-Secret: ${WEBHOOK_AUTH_SECRET}
            * X-Webhook-Nocodbtableid: <table ID from step 2>
        - Select 'Push events' as the Trigger
        - Disable SSL verification
        - Click 'Add webhook'

✅ Now the webhook is active. The next time there is a 'git push' including commits 
which have new or changed 'DATASET.json' files, the webhook will automatically enter 
their contents to the NocoDB table.

EOF

