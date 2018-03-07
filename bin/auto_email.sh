#!/bin/sh

cd /opt/stm

./bin/run.py >./app/data/nieuwe-gemeenten.json
flask eenmalig_gemeenten_en_verkiezingen_aanmaken --json_file=app/data/nieuwe_gemeenten.json >>log/auto_email.log
