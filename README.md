# Stembureaus
Collecting and presenting stembureaus


## Requirements
[Docker Compose](https://docs.docker.com/compose/install/)

## Run
- Clone or download this project from GitHub:
- Copy `docker/docker-compose.yml.example` to `docker/docker-compose.yml` and edit it
   - Fill in a password at `<DB_PASSWORD>`
- Copy `config.py.example` to `config.py` and edit it
   - Create a SECRET_KEY as per the instructions in the file
   - Fill in your CKAN URL and CKAN API key
   - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
   - Specify the name(s) of the election(s) and its corresponding CKAN draft and publish resource IDs
      - NOTE: Use the exact same '<name of election>' values in the 'verkiezingen' field in 'app/data/gemeenten.json'
   - Specify email related information in order for the application to send emails
- Copy `app/data/gemeenten.json.example` to `app/data/gemeenten.json` and edit it
   - Fill in the email addresses of the gemeenten
   - Add the name(s) of the election(s) for each gemeenten in which it participates. NOTE: make sure that these names are exactly the same as the name(s) of the election(s) in `app/config.py`
- Download the most recent BAG
   - `cd docker/docker-entrypoint-initdb.d/`
   - `wget -nd 'https://data.nlextract.nl/bag/csv/bag-adressen-full-laatst.csv.zip'`
   - `unzip bag-adressen-full-laatst.csv.zip`
- Production
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `sudo docker-compose up -d`
   - Compile the assets, see the section below
   - The `docker-compose up` command above also loads the BAG data in MySQL, this can take something like 10 minutes, so wait until `waarismijnstemlokaal.nl/` loads without errors before continuing with the commands below
   - Get buurt data: `sudo docker exec -it stm_app_1 /opt/stm/bin/get_address_data.sh`
   - Set up backups
      - Copy `docker/backup.sh.example` to `docker/backup.sh` and edit it
         - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
      - To run manually use `sudo ./backup.sh`
      - To set a daily cronjob at 03:46
         - `sudo crontab -e` and add the following line (change the path below to your `stembureaus/docker` directory path)
         - `46 3 * * * (cd <PATH_TO_stembureaus/docker> && sudo ./backup.sh)`
      - The resulting SQL backup files are saved in `docker/docker-entrypoint-initdb.d`
- Development; Flask debug will be turned on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Compile the assets, see the section below
   - If you ran the `docker-compose up` command above for the first time or if you removed the `stm_stm-mysql-volume` then the BAG data will beloaded in MySQL, this can take something like 10 minutes, so wait until `waarismijnstemlokaal.nl/` loads without errors before continuing with the commands below
   - Get buurt data: `sudo docker exec -it stm_app_1 /opt/stm/bin/get_address_data.sh`
   - Retrieve the IP address of the nginx container `docker inspect stm_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> waarismijnstemlokaal.nl`
- Useful commands
   - Remove and rebuild everything (this also removes the MySQL volume containing all gemeente, verkiezingen and BAG data (this is required if you want to load the .sql files from `docker/docker-entrypoint-initdb.d` again), but not the stembureaus data stored in CKAN)
      - Production: `docker-compose down --rmi all && docker volume rm stm_stm-mysql-volume && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker volume rm stm_stm-mysql-volume && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec stm_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `sudo touch uwsgi-touch-reload`

## Compile assets
All the following commands have to be run in the `stm_nodejs_1` container, so first enter it using:
- `sudo docker exec -it stm_nodejs_1 bash`

Run the following commands once after a new install:
- `npm install -g gulp bower`
- `npm install`
- `bower install --allow-root`

To compile the assets:
- `gulp`

To automatically compile the assets in development on any file changes (always run `gulp` first to compile any changes up till now):
- `gulp watch`

## CLI
To access the CLI of the app run `sudo docker exec -it stm_app_1 bash` and run `flask`. Here are some CLI commands:

- `flask ckan maak_nieuwe_datastore <ID_of_resource>` creates a new datastore in a CKAN resource; this needs to be run once after you've created a new CKAN resource
- `flask gemeenten eenmalig_gemeenten_en_verkiezingen_aanmaken` creates the gemeenten and verkiezingen tables in the MySQL database
- `flask gemeenten eenmalig_gemeenten_uitnodigen` sends an email to each municipality inviting them to create an account

## To enter the MySQL database
   - `sudo docker exec -it stm_mysql_1 bash`
   - `mysql -p`
   - Retrieve database password from `docker/docker-compose.yml` and enter it in the prompt
