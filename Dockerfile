FROM python:3.12-slim


# Install git
RUN apt-get update && apt-get install -y git openssh-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN apt-get update && apt-get install -y curl jq && rm -rf /var/lib/apt/lists/*

COPY src /app
COPY submodules /app
COPY config.yml .
RUN pip install /app/submodules/nocodb_automation/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh


CMD ["./start.sh"]

