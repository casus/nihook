#!/bin/bash
set -e

# Restart all or given NocoDB + webhook instances
# Usage:
#   ./restart_instances.sh                      # restarts all instances
#   ./restart_instances.sh ./nocodb_webhook_instance_5233_7233 ./nocodb_webhook_instance_5555_7555

PUBLIC_URL="http://192.168.11.167"
PARENT_DIR=$(pwd)
INSTANCE_DIRS=()

if [ $# -eq 0 ]; then
  # No arguments → find all instances
  INSTANCE_DIRS=($(find "$PARENT_DIR" -maxdepth 1 -type d -name "nocodb_webhook_instance_*_*"))
else
  # Arguments provided → restart only those
  INSTANCE_DIRS=("$@")
fi

if [ ${#INSTANCE_DIRS[@]} -eq 0 ]; then
  echo "❌ No instance directories found."
  exit 1
fi

for INSTANCE in "${INSTANCE_DIRS[@]}"; do
  echo "🔄 Restarting instance: $INSTANCE"

  BASENAME=$(basename "$INSTANCE")
  # Expected format: nocodb_webhook_instance_5xyz_7xyz
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

  # Stop existing container if any (we can identify by ports)
  CONTAINER_ID=$(docker ps -q -f "publish=$HOST_PORT_WEBHOOK" -f "publish=$HOST_PORT_NOCODB")
  if [ -n "$CONTAINER_ID" ]; then
    echo "🛑 Stopping container $CONTAINER_ID using ports $HOST_PORT_WEBHOOK/$HOST_PORT_NOCODB..."
    docker stop "$CONTAINER_ID"
    docker rm "$CONTAINER_ID"
  fi

  # Run updated container
  docker run -d \
    -p "${HOST_PORT_WEBHOOK}:5000" \
    -p "${HOST_PORT_NOCODB}:8080" \
    -v "$(realpath "$CONFIG_DIR")":/app/config/ \
    -v "$(realpath "$AUTH_DIR")":/app/auth/ \
    -v "$(realpath "$DB_DIR")":/app/db/ \
    -v "$(realpath "$LOGS_DIR")":/app/logs/ \
    -e NOCODB_PORT=8080 \
    -e HOOK_HOST=0.0.0.0 \
    -e HOOK_PORT=5000 \
    webhook-nocodb

  echo "✅ Instance restarted at:"
  echo "   👉 Webhook: ${PUBLIC_URL}:${HOST_PORT_WEBHOOK}"
  echo "   👉 NocoDB : ${PUBLIC_URL}:${HOST_PORT_NOCODB}"
  echo "Authentication info:"
  echo "      NocoDB Email  : ${email}"
  echo "      NocoDB Password  : ${password}"
  echo "      NocoDB Token  : ${token}"
  echo ""
done
