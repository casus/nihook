#!/bin/bash


# Download and install NocoDB binary
# curl http://get.nocodb.com/linux-x64 -o /usr/local/bin/nocodb -L
# chmod +x /usr/local/bin/nocodb

# # Start NocoDB in the background
# /usr/local/bin/nocodb &

# Define URL and binary name

# Download the binary
curl -L -o Noco-linux-x64 https://github.com/nocodb/nocodb/releases/download/0.263.8/Noco-linux-x64

# Make it executable
chmod +x Noco-linux-x64

# Run it in the background
./Noco-linux-x64 --host 0.0.0.0 --port "$NOCODB_PORT" &


# Wait for NocoDB to be ready
MAX_TRIES=30
TRIES=0
until curl -s "http://localhost:$NOCODB_PORT/api/v1/health" | grep -q 'OK'; do
  if [ $TRIES -ge $MAX_TRIES ]; then
    echo "NocoDB did not become ready in time, exiting."
    exit 1
  fi
  echo "Waiting for NocoDB to start on port $NOCODB_PORT..."
  TRIES=$((TRIES+1))
  sleep 2
done

echo "NocoDB is up!"

# Generate the token by signing up
response=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "email": "admin@gmail.com",
        "password": "12345678",
        "ignore_subscribe": true,
        "token": ""
      }' \
  "http://localhost:$NOCODB_PORT/api/v1/auth/user/signup")

user_token=$(echo "$response" | jq -r '.token')

if [[ -z "$user_token" || "$user_token" == "null" ]]; then
  echo "Failed to get admin token:"
  echo "$response"
  exit 1
fi

# Use the token as the xc-auth header for the next request
response=$(curl -s -X POST "http://localhost:$NOCODB_PORT/api/v1/tokens" \
  -H "Content-Type: application/json" \
  -H "xc-auth: $user_token" \
  -d '{"description":"Default-Token"}')

token=$(echo "$response" | jq -r '.token')

if [[ -z "$token" || "$token" == "null" ]]; then
  echo "Failed to get API token:"
  echo "$response"
  exit 1
fi

# Create a default base only in debug mode
if [ "$DEBUG" = "True" ]; then
  response=$(curl -s -X POST "http://localhost:$NOCODB_PORT/api/v1/db/meta/projects/" \
    -H "Content-Type: application/json" \
    -H "xc-auth: $user_token" \
    -d '{"title":"Default-Base"}')
  base_id=$(echo "$response" | jq -r '.id')
  export BASE_ID="$base_id"
fi

export NOCODB_TOKEN="$token"

# Start the webhook app
python /app/gitlab_webhooks/webhook.py &

wait -n
