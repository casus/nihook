#!/bin/bash

# Load environment variables from .env
set -a
source .env
set +a

DEBUG=${DEBUG:-False}

# Function to find a free port on the host
find_free_port() {
  while :; do
    PORT=$(shuf -i 5001-5999 -n 1)
    if ! lsof -i ":$PORT" >/dev/null 2>&1; then
      echo "$PORT"
      return
    fi
  done
}

# Dynamically find free host ports

if [ "$DEBUG" = "True" ]; then
  HOST_PORT_APP1=5000
  HOST_PORT_APP2=5555
else
  HOST_PORT_APP1=$(find_free_port)
  HOST_PORT_APP2=$(find_free_port)
fi

# Create auth directory
if [ "$DEBUG" = "True" ]; then
  CONTAINER_ID=1
else
  CONTAINER_ID=$(date +%s)
fi
VOLUME_DIR="./volumes/container_${CONTAINER_ID}"
LOGS_DIR="./volumes/container_${CONTAINER_ID}/logs"
mkdir -p "$VOLUME_DIR"
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
  webhook-nocodb



# Print port mapping info
echo ""
echo "🟢 Application is running:"
echo "  👉 http://192.168.11.167:${HOST_PORT_APP1} → Webhook"
echo "  👉 http://192.168.11.167:${HOST_PORT_APP2} → NocoDB"
