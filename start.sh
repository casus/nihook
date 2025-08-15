#!/bin/bash


# Download and install NocoDB binary
# curl http://get.nocodb.com/linux-x64 -o /usr/local/bin/nocodb -L
# chmod +x /usr/local/bin/nocodb

# # Start NocoDB in the background
# /usr/local/bin/nocodb &

# Define URL and binary name


# Run nocodb it in the background
./Noco-linux-x64 --host 0.0.0.0 --port "$NOCODB_PORT" &




# Create a default base only in debug mode
if [ "$DEBUG" = "True" ]; then
  response=$(curl -s -X POST "http://localhost:$NOCODB_PORT/api/v1/db/meta/projects/" \
    -H "Content-Type: application/json" \
    -H "xc-auth: $user_token" \
    -d '{"title":"Default-Base"}')
  base_id=$(echo "$response" | jq -r '.id')
  export BASE_ID="$base_id"
fi

echo "export NOCODB_TOKEN=\"$token\""
export NOCODB_TOKEN="$token"

# Start the webhook app
python /app/gitlab_webhooks/webhook.py &

#wait -n
wait # for now wait for all

