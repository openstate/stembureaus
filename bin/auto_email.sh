#!/bin/sh

cd /opt/stm

./bin/run.py >./app/data/nieuwe-gemeenten.json
 flask gemeenten eenmalig_gemeenten_en_verkiezingen_aanmaken --json_file=app/data/nieuwe-gemeenten.json >>logs/auto_email.log
