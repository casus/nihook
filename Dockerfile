FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y curl jq pwgen && rm -rf /var/lib/apt/lists/*


# install NocoDB
RUN curl -L -o Noco-linux-x64 https://github.com/nocodb/nocodb/releases/download/0.265.1/Noco-linux-x64
RUN chmod +x Noco-linux-x64

# install webhook server
COPY src /app/src
COPY submodules /app/submodules

RUN pip install --upgrade pip
RUN pip install /app/submodules/nihook-client
RUN pip install --no-cache-dir -r /app/src/requirements.txt

COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh


CMD ["./start.sh"]

