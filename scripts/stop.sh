#!/bin/bash

docker rm -f $(docker ps -aq)
docker volume rm $(docker volume ls -q)
sudo rm -rf ./volumes ./nocodb_webhook_instance_*/
# dir=$(basename "$PWD") && cd .. && rm -rf "$dir"

docker container prune -f
