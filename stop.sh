#!/bin/bash

docker rm -f $(docker ps -aq)
docker volume rm $(docker volume ls -q)
sudo rm -rf ./volumes
# dir=$(basename "$PWD") && cd .. && rm -rf "$dir"
