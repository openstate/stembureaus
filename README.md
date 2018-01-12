# Stembureaus
Collecting and presenting stembureaus


## Requirements
[Docker Compose](https://docs.docker.com/compose/install/)

## Run
- Production
   - First time use
      - `cd docker`
      - `sudo docker-compose up -d`
   - After the first time use: `docker-compose start`
- Development; Flask debug will be set to on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - `cd docker`
   - `docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Retrieve the IP address of the nginx container `docker inspect stm_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> waarismijnstemlokaal.nl`
- Useful commands
   - Remove and rebuild everything
      - Production: `docker-compose down --rmi all && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec stm_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `sudo touch app/uwsgi-touch-reload`
