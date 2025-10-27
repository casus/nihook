#!/bin/bash
set -e

# Resume all NocoDB + webhook instances that are not running
# Usage:
#   ./resume_instances.sh                      # resumes all instances
#   ./resume_instances.sh ./nocodb_webhook_instance_5233_7233 ./nocodb_webhook_instance_5555_7555

PUBLIC_URL="https://data.casus.science"
HOOK_HOST=0.0.0.0
HOOK_PORT=5000
NOCODB_PORT=8080
PARENT_DIR=$(pwd)
INSTANCE_DIRS=()

if [ $# -eq 0 ]; then
  # No arguments → find all instances
  INSTANCE_DIRS=($(find "$PARENT_DIR" -maxdepth 1 -type d -name "nocodb_webhook_instance_*_*"))
else
  # Arguments provided → resume only those
  INSTANCE_DIRS=("$@")
fi

if [ ${#INSTANCE_DIRS[@]} -eq 0 ]; then
  echo "❌ No instance directories found."
  exit 1
fi

for INSTANCE in "${INSTANCE_DIRS[@]}"; do
  echo "🔍 Checking instance: $INSTANCE"

  BASENAME=$(basename "$INSTANCE")
  HOST_PORT_WEBHOOK=$(echo "$BASENAME" | awk -F'_' '{print $4}')
  HOST_PORT_NOCODB=$(echo "$BASENAME" | awk -F'_' '{print $5}')

  CONFIG_DIR="$INSTANCE/config"
  AUTH_DIR="$INSTANCE/auth"
  DB_DIR="$INSTANCE/db"
  LOGS_DIR="$INSTANCE/logs"
  CONFIG_FILE="$CONFIG_DIR/nocodb.json"

  if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️ Config file not found in $INSTANCE, skipping."
    continue
  fi

  email=$(jq -r '.nocodb_email' "$CONFIG_FILE")
  password=$(jq -r '.nocodb_password' "$CONFIG_FILE")
  token=$(jq -r '.nocodb_secret_token' "$CONFIG_FILE")

  # Check if container is already running (matching published ports)
  RUNNING_ID=$(podman ps --format "{{.ID}} {{.Ports}}" | grep "${HOST_PORT_WEBHOOK}->5000" | awk '{print $1}')
  if [ -n "$RUNNING_ID" ]; then
    echo "✅ Instance already running on ports $HOST_PORT_WEBHOOK/$HOST_PORT_NOCODB (container $RUNNING_ID)"
    continue
  fi

  OLD_ID=$(podman ps -a --format "{{.ID}} {{.Ports}}" | grep "${HOST_PORT_WEBHOOK}->5000" | awk '{print $1}')
  if [ -n "$OLD_ID" ]; then
    echo "Removing old container"
    podman rm "$OLD_ID" || echo "️Failed to remove old container $OLD_ID"
  fi
  
  echo "▶️ Starting instance on ports $HOST_PORT_WEBHOOK/$HOST_PORT_NOCODB..."
  podman run -d \
    -p "${HOST_PORT_WEBHOOK}":"${HOOK_PORT}" \
    -p "${HOST_PORT_NOCODB}":"${NOCODB_PORT}" \
    -v "$(realpath "$CONFIG_DIR")":/app/config/ \
    -v "$(realpath "$AUTH_DIR")":/app/auth/ \
    -v "$(realpath "$DB_DIR")":/app/db/ \
    -v "$(realpath "$LOGS_DIR")":/app/logs/ \
    -e NOCODB_PORT="$NOCODB_PORT" \
    -e HOOK_HOST="$HOOK_HOST" \
    -e HOOK_PORT="$HOOK_PORT" \
    --restart=always \
    webhook-nocodb

  echo "✅ Instance started at:"
  echo "   👉 Webhook: ${PUBLIC_URL}:${HOST_PORT_WEBHOOK}"
  echo "   👉 NocoDB : ${PUBLIC_URL}:${HOST_PORT_NOCODB}"
  echo "Authentication info:"
  echo "      NocoDB Email  : ${email}"
  echo "      NocoDB Password  : ${password}"
  echo "      NocoDB Token  : ${token}"
  echo ""
done
