# NGINX Reverse Proxy for Dynamic Container Ports

## Prerequisites

1) NGINX installed on the server.

2) SSL certificate and key at:

    `/etc/nginx/certs/selfsigned.crt`

    `/etc/nginx/certs/selfsigned.key`


3) Web services running on the VM, accessible on 127.0.0.1:<port_number>.

## Usage

1)  Add your services in Docker or otherwise, ensuring they listen on local ports.
2) Access your services via:
    https://webhook.test/<port_number>/<optional_path>


Examples:

https://webhook.test/7993/

https://webhook.test/5993/api

https://webhook.test/7993/dashboard



NGINX automatically proxies the request to the correct backend port.