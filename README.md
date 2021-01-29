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
- Buy and download the most recent 'BAG Adressen - Uitgebreid - CSV' from https://geotoko.nl/datasets?rid=24b6070d-5a92-4109-8fcd-a1d7cc000801 (NB: from the moment that gemeenten start to update the stembureaus till election day you need to buy and download the latest monthly released version of this file)
   - download the 'bag-adressen-full-nl.csv' file into `docker/docker-entrypoint-initdb.d/`
   - `unzip bag-adressen-full-laatst.csv.zip`
   - `bag.sql` will automatically load the data when docker starts for the first time; if you want to update the data later the you can simply go to the `docker` folder and run `sudo ./update_bag.sh`
      - Copy `docker/update_bag.sh.example` to `docker/update_bag.sh` and edit it
         - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
- Production
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `sudo docker-compose up -d`
   - Compile the assets, see the section below
   - The `docker-compose up` command above also loads the BAG data in MySQL, this can take more than 1 hour on a server (without SSD), so wait until `waarismijnstemlokaal.nl/` loads without errors before continuing with the commands below
   - # NOT NEEDED AS THIS DATA IS NOT UP TO DATE: Get buurt data: `sudo docker exec -it stm_app_1 /opt/stm/bin/get_address_data.sh`
   - Set up daily backups for MySQL and CKAN
      - Copy `docker/backup.sh.example` to `docker/backup.sh` and edit it
         - MySQL: Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
         - CKAN: Copy the CKAN backup command for each CKAN (concept) resource you want to backup and fill in the `<RESOURCE_ID>`
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
   - If you ran the `docker-compose up` command above for the first time or if you removed the `stm_stm-mysql-volume` then the BAG data will be loaded in MySQL, this can take something like 10 minutes (with an SSD), so wait until `waarismijnstemlokaal.nl/` loads without errors before continuing with the commands below
   - # NOT NEEDED AS THIS DATA IS NOT UP TO DATE: Get buurt data: `sudo docker exec -it stm_app_1 /opt/stm/bin/get_address_data.sh`
   - Retrieve the IP address of the nginx container `docker inspect stm_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> waarismijnstemlokaal.nl`
- Useful commands
   - Run the tests: `sudo docker exec -it stm_app_1 nosetests`
   - Remove and rebuild everything (this also removes the MySQL volume containing all gemeente, verkiezingen and BAG data (this is required if you want to load the .sql files from `docker/docker-entrypoint-initdb.d` again), but not the stembureaus data stored in CKAN)
      - Production: `docker-compose down --rmi all && docker volume rm stm_stm-mysql-volume && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker volume rm stm_stm-mysql-volume && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec stm_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `touch uwsgi-touch-reload`

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
To access the CLI of the app run `sudo docker exec -it stm_app_1 bash` and run `flask`, `flask ckan` and `flask mysql` to see the available commands. Here are some CLI commands:

- `flask ckan add-new-datastore <ID_of_resource>` add a new datastore in a CKAN resource; this needs to be run once after you've created a new CKAN resource, see the 'Create new CKAN datasets and resources for new elections' section below
- `flask mysql add-gemeenten-verkiezingen-users` add all gemeenten, verkiezingen and users specified in 'app/data/gemeenten.json' to the MySQL database and send new users an invitation email

## Create new CKAN datasets and resources for new elections
- If you want to add new elections, log in to https://ckan.dataplatform.nl/dashboard/datasets and click 'Dataset toevoegen'. Fill in the metadata (see earlier elections to see what to fill in). Make sure to create a 'concept' dataset besides the actual dataset. The concept dataset is used to store the stembureau data that isn't ready to be published yet.
- After filling the dataset information, click 'Data toevoegen' in order to add a new resource/bron.

## To enter the MySQL database
- `sudo docker exec -it stm_mysql_1 bash`
- `mysql -p`
- Retrieve database password from `docker/docker-compose.yml` and enter it in the prompt

## Update Nginx
- On development:
   - docker-compose -f docker-compose.yml -f docker-compose-dev.yml build --pull nginx
   - docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d nginx
- On production:
   - docker-compose build --pull nginx
   - docker-compose up -d nginx

## Update App (Python)
- On development:
   - docker-compose -f docker-compose.yml -f docker-compose-dev.yml build --pull app
   - docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d app
- On production:
   - docker-compose build --pull app
   - docker-compose up -d app

## Update MySQL
- docker-compose pull mysql
- docker-compose up -d mysql

## Deploying
Use Fabric 2.x on your development machine to pull new changes from GitHub on a server and compile assets

- fab deploy
