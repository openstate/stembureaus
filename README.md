# Stembureaus
Collecting and presenting stembureaus


## Requirements
[Docker Compose](https://docs.docker.com/compose/install/)

## Run
- Clone or download this project from GitHub:
- Copy `app/config.py.example` to `app/config.py` and edit it
   - Create a SECRET_KEY as per the instructions in the file
   - Fill in your CKAN API key
   - Specify the name(s) of the election(s) and its corresponding CKAN draft and publish resource IDs
      - NOTE: Use the exact same '<name of election>' values in the 'verkiezingen' field in 'app/data/gemeenten.json'
   - Specify email related information in order for the application to send emails
- Copy `app/data/gemeenten.json.example` to `app/data/gemeenten.json` and edit it
   - Fill in the email addresses of the gemeenten
   - Add the name(s) of the election(s) for each gemeenten in which it participates. NOTE: make sure that these names are exactly the same as the name(s) of the election(s) in `app/config.py`
- Production
   - First time use
      - `cd docker`
      - `sudo docker-compose up -d`
   - After the first time use: `docker-compose start`
- Development; Flask debug will be turned on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - `cd docker`
   - `docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Retrieve the IP address of the nginx container `docker inspect stm_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> waarismijnstemlokaal.nl`
- Useful commands
   - Remove and rebuild everything
      - Production: `docker-compose down --rmi all && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec stm_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `sudo touch app/uwsgi-touch-reload`
