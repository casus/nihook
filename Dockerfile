FROM python:3.12-slim


# Install git
RUN apt-get update && apt-get install -y git openssh-client && rm -rf /var/lib/apt/lists/*

# ===
# This is temporary until the nocodb repo is public
# Add SSH key & known hosts
ENV GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no"

# Set up SSH
RUN mkdir -p /root/.ssh
COPY id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa

# Add Git server to known_hosts to avoid prompt
RUN ssh-keyscan codebase.helmholtz.cloud >> /root/.ssh/known_hosts
# ===

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

