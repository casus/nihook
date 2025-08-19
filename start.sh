#!/bin/bash


# Download and install NocoDB binary
# curl http://get.nocodb.com/linux-x64 -o /usr/local/bin/nocodb -L
# chmod +x /usr/local/bin/nocodb

# # Start NocoDB in the background
# /usr/local/bin/nocodb &

# Define URL and binary name


# Run nocodb it in the background
export NC_TOOL_DIR=/app/db/
./Noco-linux-x64 --host 0.0.0.0 --port "$NOCODB_PORT" >/app/logs/nocodb.log 2>/app/logs/nocodb.error.log &


# Wait for NocoDB to be ready
TRIES=30
until curl -s "http://localhost:$NOCODB_PORT/api/v1/health" | grep -q 'OK'; do
  if (( $TRIES < 1 )); then
    echo "NocoDB did not become ready in time, exiting."
    exit 1
  fi
  echo "Waiting for NocoDB to start on port $HOSTNOCODB_PORT_PORT_NOCODB..."
  TRIES=$((TRIES-1))
  sleep 2
done
echo "NocoDB is up!"


if [ -f "/app/config/nocodb.json" ]; then

  token=`jq -r '.nocodb_secret_token' /app/config/nocodb.json`
  echo "Read NOCODB token from file: "$token

else

  echo "Generate NOCODB token"

  ADMIN_EMAIL="admin@gmail.com"
  ADMIN_PASSWORD=`/usr/bin/pwgen 20 1`

  # Sign up first user 
  response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{
          "email": "'$ADMIN_EMAIL'",
          "password": "'$ADMIN_PASSWORD'",
          "ignore_subscribe": true,
          "token": ""
        }' \
    "http://localhost:$NOCODB_PORT/api/v1/auth/user/signup")
  user_token=$(echo "$response" | jq -r '.token')

  if [[ -z "$user_token" || "$user_token" == "null" ]]; then
    echo "Failed to sign up as admin user:"
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

  jq --null-input \
    --arg email "${ADMIN_EMAIL}" \
    --arg password "${ADMIN_PASSWORD}" \
    --arg token "$token" \
  '{ "nocodb_email": $email, "nocodb_password": $password, "nocodb_secret_token": $token}' >/app/config/nocodb.json

  echo "Newly generated NOCODB token: "$token

  # Create a default base only in debug mode
  if [ "$DEBUG" = "True" ]; then
    response=$(curl -s -X POST "http://localhost:$NOCODB_PORT/api/v1/db/meta/projects/" \
      -H "Content-Type: application/json" \
      -H "xc-auth: $user_token" \
      -d '{"title":"Default-Base"}')
    base_id=$(echo "$response" | jq -r '.id')
    export BASE_ID="$base_id"
  fi

fi

echo "export NOCODB_TOKEN=\"$token\""
export NOCODB_TOKEN="$token"

#check all the files
ls -alh -R /app/ >/app/logs/ls-R.txt

# Start the webhook app
python /app/src/gitlab_webhooks/webhook.py >/app/logs/webhook.log 2>/app/logs/webhook.error.log &

wait -n

