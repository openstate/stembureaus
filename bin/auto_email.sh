#!/bin/sh

cd /opt/stm

./bin/run.py > ./app/data/nieuwe-gemeenten.json
flask mysql add-gemeenten-verkiezingen-users --json_file=app/data/nieuwe-gemeenten.json >> logs/auto_email.log
