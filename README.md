# Stembureaus
Collecting and presenting stembureaus


## Requirements
[Docker Compose](https://docs.docker.com/compose/install/)

## Run
- Clone or download this project from GitHub:
- Copy `docker/docker-compose.yml.example` to `docker/docker-compose.yml` and edit it
   - Fill in a password at `<DB_PASSWORD>`
- Copy `app/config.py.example` to `app/config.py` and edit it
   - Create a SECRET_KEY as per the instructions in the file
   - Fill in your CKAN API key
   - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
   - Specify the name(s) of the election(s) and its corresponding CKAN draft and publish resource IDs
      - NOTE: Use the exact same '<name of election>' values in the 'verkiezingen' field in 'app/data/gemeenten.json'
   - Specify email related information in order for the application to send emails
- Copy `app/data/gemeenten.json.example` to `app/data/gemeenten.json` and edit it
   - Fill in the email addresses of the gemeenten
   - Add the name(s) of the election(s) for each gemeenten in which it participates. NOTE: make sure that these names are exactly the same as the name(s) of the election(s) in `app/config.py`
- Production
   - First time set up
      - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d' if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
      - `cd docker`
      - `sudo docker-compose up -d`
      - Compile the assets, see the section below
      - Set up backups
         - Copy `docker/backup.sh.example` to `docker/backup.sh` and edit it
            - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
         - To run manually use `sudo ./backup.sh`
         - To set a daily cronjob at 03:46
            - `sudo crontab -e` and add the following line (change the path below to your `stembureaus/docker` directory path)
            - `46 3 * * * (cd <PATH_TO_stembureaus/docker> && sudo ./backup.sh)`
         - The resulting SQL backup files are saved in `docker/docker-entrypoint-initdb.d`
- Development; Flask debug will be turned on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - `cd docker`
   - `docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Compile the assets, see the section below
   - Retrieve the IP address of the nginx container `docker inspect stm_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> waarismijnstemlokaal.nl`
- Useful commands
   - Remove and rebuild everything
      - Production: `docker-compose down --rmi all && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec stm_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `sudo touch app/uwsgi-touch-reload`

## Compile assets
Run the following commands once after a new install:
- `sudo docker exec -it stm_nodejs_1 bash`
- `npm install -g gulp bower`
- `npm install`
- `bower install --allow-root`

To compile the assets in production:
- `gulp --production`

To compile the assets in development (this generates map files):
- `gulp`

To compile the assets in development on any file changes:
- `gulp watch`

## To enter the MySQL database
   - `sudo docker run -it --rm --network stm_stm mysql bash`
   - `mysql -h docker_c-wordpress-mysql_1 -u root -p`
   - Retrieve database password from `docker/docker-compose.yml` and enter it in the prompt
