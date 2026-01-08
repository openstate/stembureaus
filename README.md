# Waar is mijn stemlokaal
Collecting and presenting stembureaus: [WaarIsMijnStemlokaal.nl](https://waarismijnstemlokaal.nl/)

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
      - NOTE: Use the exact same `<name of election>` values in the 'verkiezingen' field in 'app/data/gemeenten.json'
   - Specify email related information in order for the application to send emails
- Copy `app/data/gemeenten.json.example` to `app/data/gemeenten.json` and edit it
   - Fill in the email addresses of the gemeenten
   - Add the name(s) of the election(s) for each gemeenten in which it participates. NOTE: make sure that these names are exactly the same as the name(s) of the election(s) in `app/config.py`
- Buy and download the most recent 'BAG Adressen - Uitgebreid - CSV' from https://geotoko.nl/datasets?rid=24b6070d-5a92-4109-8fcd-a1d7cc000801 (NB: from the moment that gemeenten start to update the stembureaus till election day you need to buy and download the latest monthly released version of this file)
   - download the 'bag-adressen-full-nl.csv.zip' file into `docker/docker-entrypoint-initdb.d/`
   - `unzip bag-adressen-full-laatst.csv.zip`
   - `bag.sql` will automatically load the data when docker starts for the first time; if you want to update the data later the you can simply go to the `docker` folder and run `sudo ./update_bag.sh`
      - Copy `docker/update_bag.sh.example` to `docker/update_bag.sh` and edit it
         - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
- Production
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `sudo docker-compose up -d`
   - [Compile the assets](#compile-assets)
   - The `docker-compose up` command above also loads the BAG data in MySQL, this can take more than 1 hour on a server (without SSD), so wait until `WaarIsMijnStemlokaal.nl` loads without errors before continuing with the commands below
   - NOT NEEDED AS THIS DATA IS NOT UP TO DATE: Get buurt data: `sudo docker exec -it stm_app_1 /opt/stm/bin/get_address_data.sh`
   - Set up daily backups for MySQL and CKAN
      - Copy `docker/backup.sh.example` to `docker/backup.sh` and edit it
         - MySQL: Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
         - CKAN: Copy the CKAN backup command for each CKAN (concept) resource you want to backup and fill in the `<RESOURCE_ID>`
      - To run manually use `sudo ./backup.sh`
      - To set a daily cronjob at 03:46
         - `sudo crontab -e` and add the following line (change the path below to your `stembureaus/docker` directory path)
         - `46 3 * * * (cd <PATH_TO_stembureaus/docker> && sudo ./backup.sh)`
      - The resulting SQL backup files are saved in `docker/docker-entrypoint-initdb.d` and the CKAN exports in `exports`
- Development; Flask debug will be turned on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - [Compile the assets](#compile-assets)
   - If you ran the `docker-compose up` command above for the first time or if you removed the `stm_stm-mysql-volume` then the BAG data will be loaded in MySQL, this can take something like 15 minutes (with an SSD), so wait until `WaarIsMijnStemlokaal.nl` loads without errors before continuing with the commands below
   - NOT NEEDED AS THIS DATA IS NOT UP TO DATE: Get buurt data: `sudo docker exec -it stm_app_1 /opt/stm/bin/get_address_data.sh`
   - Retrieve the IP address of the nginx container `sudo docker inspect stm_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> waarismijnstemlokaal.nl`
- Useful commands
   - Run the tests: `sudo docker exec -it stm_app_1 nose2`
   - Remove and rebuild everything (this also removes the MySQL volume containing all gemeente, verkiezingen and BAG data (this is required if you want to load the .sql files from `docker/docker-entrypoint-initdb.d` again), but not the stembureaus data stored in CKAN)
      - Production: `sudo docker-compose down --rmi all && sudo docker volume rm stm_stm-mysql-volume && sudo docker-compose up -d`
      - Development: `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && sudo docker volume rm stm_stm-mysql-volume && sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec stm_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `touch uwsgi-touch-reload`

## Compile assets
- Install all packages (only need to run once after installation or when you change packages): `sudo docker exec stm_nodejs_1 yarn`

Production
- Compile CSS/JS to `static/dist` directory: `sudo docker exec stm_nodejs_1 yarn build`

Development
- Compile CSS/JS to `static/dist` directory (with map files): `sudo docker exec stm_nodejs_1 yarn build`
- Automatically compile CSS/JS when a file changes (simply refresh the page in your browser after a change): `sudo docker exec stm_nodejs_1 yarn watch`

## CLI
To access the CLI of the app run `sudo docker exec -it stm_app_1 bash` and run `flask`, `flask ckan` and `flask mysql` to see the available commands. Here are some CLI commands:

- `flask mysql add-admin-user <email>` add a new admin user with the specified email
- `flask ckan add-new-datastore <ID_of_resource>` add a new datastore in a CKAN resource; this needs to be run once after you've created a new CKAN resource, see [Create new CKAN datasets and resources for new elections](#create-new-ckan-datasets-and-resources-for-new-elections)
- `flask mysql add-gemeenten-verkiezingen-users` add all gemeenten, verkiezingen and users specified in 'app/data/gemeenten.json' to the MySQL database and send new users an invitation email

## Create new CKAN datasets and resources for new elections
- If you want to add new elections, log in to https://data.waarismijnstemlokaal.nl/dashboard/datasets (until July 2025 this was https://ckan.dataplatform.nl/dashboard/datasets) and click 'Dataset toevoegen'. Fill in the metadata (see earlier elections to see what to fill in). Make sure to create a 'concept' dataset besides the actual dataset. The concept dataset is used to store the stembureau data that isn't ready to be published yet.
- After filling the dataset information, click 'Data toevoegen' in order to add a new resource/bron.

## To enter the MySQL database
- `sudo docker exec -it stm_mysql_1 bash`
- `mysql -p`
- Retrieve database password from `docker/docker-compose.yml` and enter it in the prompt

## Update Nginx
- On development:
   - `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml build --pull nginx`
   - `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d nginx`
- On production:
   - `sudo docker-compose build --pull nginx`
   - `sudo docker-compose up -d nginx`

## Update App (Python)
- On development:
   - `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml build --pull app`
   - `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d app`
- On production:
   - `sudo docker-compose build --pull app`
   - `sudo docker-compose up -d app`

## Update MySQL
- `sudo docker-compose pull mysql`
- `sudo docker-compose up -d mysql`
- Note: if you change the major version of Mysql, then also change the version used in update_bag.sh(.example)

## Deploying
Use Fabric 2.x on your development machine to pull new changes from GitHub on a server and compile assets

- `fab deploy`

## Troubleshooting
If you try to visit WaarIsMijnStemlokaal.nl and get a '502 Bad Gateway', then open the console in your browser. If you see a message like (this is in Firefox):

> The character encoding of the HTML document was not declared. The document will render with garbled text in some browser configurations if the document contains characters from outside the US-ASCII range. The character encoding of the page must be declared in the document or in the transfer protocol.

or if you see something like this in your Docker logs:

> app_1     | invalid request block size: 21573 (max 4096)...skip
> nginx_1   | 2021/12/20 16:12:40 [error] 30#30: *1 upstream prematurely closed connection while reading response header from upstream, client: 172.18.0.1, server: waarismijnstemlokaal.nl, request: "GET / HTTP/1.1", upstream: "http://172.18.0.3:5000/", host: "waarismijnstemlokaal.nl"


then you are probably mixing up development and production images for the `app` and `nginx` services (to be precise, nginx uses a normal HTTP request in the development environment, but uses uwsgi in production). Stop and remove the app and nginx containers and remove the app and nginx images. Build again (use the `--no-cache` option) and *make sure* that you use `sudo docker-compose -f docker-compose.yml -f docker-compose-dev.yml build --no-cache app nginx` for development and simply `sudo docker-compose build --no-cache app nginx` for production.
