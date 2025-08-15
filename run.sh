#!/bin/bash

# Load environment variables from .env
set -a
source .env
set +a

DEBUG=${DEBUG:-False}

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
  HOST_PORT_APP1=5555
  HOST_PORT_APP2=7555
else
  # Dynamically find free host ports
  read -r HOST_PORT_APP1 HOST_PORT_APP2 < <(find_valid_ports)
fi


# Create auth directory
if [ "$DEBUG" = "True" ]; then
  CONTAINER_ID=1
else
  CONTAINER_ID=$(date +%s)
fi
FULLAPPDIR="./fullapp/container_${CONTAINER_ID}" # for development, remove later
VOLUME_DIR="./volumes/container_${CONTAINER_ID}"
LOGS_DIR="./volumes/container_${CONTAINER_ID}/logs"
mkdir -p "$VOLUME_DIR"
mkdir -p "$FULLAPPDIR" # for development, remove later
AUTH_FILE="${VOLUME_DIR}/auth.json"
if [ ! -f "$AUTH_FILE" ]; then
    echo "{}" > "$AUTH_FILE"
    echo "📁 Created empty auth.json in $VOLUME_DIR"
fi

cp ./src/auth/manage.sh "$VOLUME_DIR/manage.sh"
chmod +x "$VOLUME_DIR/manage.sh"

python3 ./src/auth/manage_users.py "$VOLUME_DIR"




# Run the container
docker run -d \
  --env-file .env \
  -p "${HOST_PORT_APP1}":"${HOOK_PORT}" \
  -p "${HOST_PORT_APP2}":"${NOCODB_PORT}" \
  -v "$(realpath "$VOLUME_DIR")":/app/auth/data \
  -v "$(realpath "$LOGS_DIR")":/app/logs \
  -v "$(realpath "$FULLAPPDIR")":/app \
  webhook-nocodb



# Print port mapping info
echo ""
echo "🟢 Application is running:"
echo "  👉 http://192.168.11.167:${HOST_PORT_APP1} → Webhook"
echo "  👉 http://192.168.11.167:${HOST_PORT_APP2} → NocoDB"
