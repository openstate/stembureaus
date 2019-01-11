#!/bin/sh

cd /opt/stm

./bin/run.py >./app/data/nieuwe-gemeenten.json
 flask mysql add_gemeenten_verkiezingen_users --json_file=app/data/nieuwe-gemeenten.json >>logs/auto_email.log
