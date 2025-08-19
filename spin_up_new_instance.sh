#!/bin/bash

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


# Create auth directory
if [ "$DEBUG" = "True" ]; then
  CONTAINER_ID=1
else
  CONTAINER_ID=$(date +%s)
fi
VOLUME_DIR="./volumes/container_${CONTAINER_ID}"
CONFIG_DIR=$VOLUME_DIR/config
AUTH_DIR=$VOLUME_DIR/auth
DB_DIR=$VOLUME_DIR/db
LOGS_DIR=$VOLUME_DIR/logs
mkdir -p $CONFIG_DIR $VOLUME_DIR $AUTH_DIR $DB_DIR $LOGS_DIR


# create the initial auth file

AUTH_FILE="${AUTH_DIR}/auth.json"
if [ ! -f "$AUTH_FILE" ]; then
    echo "{}" > "$AUTH_FILE"
    echo "📁 Created empty auth.json in $VOLUME_DIR"
fi
WEBHOOK_AUTH_SECRET=`python3 src/auth/add_auth.py $WEBHOOK_USERNAME -f "$AUTH_FILE"`

# create the initial projects file
PROJECTS_FILE=$CONFIG_DIR/projects.yml
cp projects.template.yml $PROJECTS_FILE

# Run the container
docker run -d \
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

# # Wait for NocoDB to be ready
# TRIES=30
# until curl -s "http://localhost:$HOST_PORT_NOCODB/api/v1/health" | grep -q 'OK'; do
#   if (( $TRIES < 1 )); then
#     echo "NocoDB did not become ready in time, exiting."
#     exit 1
#   fi
#   echo "Waiting for NocoDB to start on port $HOST_PORT_NOCODB..."
#   TRIES=$((TRIES-1))
#   sleep 2
# done

# echo "NocoDB is up!"

# # Generate the token by signing up
# response=$(curl -s -X POST \
#   -H "Content-Type: application/json" \
#   -d '{
#         "email": "admin@gmail.com",
#         "password": "12345678",
#         "ignore_subscribe": true,
#         "token": ""
#       }' \
#   "http://localhost:$HOST_PORT_NOCODB/api/v1/auth/user/signup")

# user_token=$(echo "$response" | jq -r '.token')

# if [[ -z "$user_token" || "$user_token" == "null" ]]; then
#   echo "Failed to get admin token:"
#   echo "$response"
#   exit 1
# fi

# # Use the token as the xc-auth header for the next request
# response=$(curl -s -X POST "http://localhost:$HOST_PORT_NOCODB/api/v1/tokens" \
#   -H "Content-Type: application/json" \
#   -H "xc-auth: $user_token" \
#   -d '{"description":"Default-Token"}')

# token=$(echo "$response" | jq -r '.token')

# if [[ -z "$token" || "$token" == "null" ]]; then
#   echo "Failed to get API token:"
#   echo "$response"
#   exit 1
# fi

jq --null-input \
  --arg webhook_url "${PUBLIC_URL}:${HOST_PORT_WEBHOOK}" \
  --arg nocodb_url "${PUBLIC_URL}:${HOST_PORT_NOCODB}" \
'{ "webhook_url": $webhook_url, "nocodb_url": $nocodb_url}' >{$CONFIG_DIR}/settings.json

# Print port mapping info
echo ""
echo "🟢 Application is running:"
echo "  👉 ${PUBLIC_URL}:${HOST_PORT_WEBHOOK} → Webhook"
echo "  👉 ${PUBLIC_URL}:${HOST_PORT_NOCODB} → NocoDB"
echo "      NocoDB token: ${token}"
echo ""
echo "🎣 Gitlab Webhook config data:"
echo "URL: ${PUBLIC_URL}:${HOST_PORT_WEBHOOK}/webhooks/push"
echo "Custom headers:"
echo "    X-Webhook-User: ${WEBHOOK_USERNAME}"
echo "    X-Webhook-Secret: ${WEBHOOK_AUTH_SECRET}"
echo "    X-Webhook-Nocodbtableid: ..."
echo ""