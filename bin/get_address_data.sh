#!/bin/sh

cd /opt/stm
mkdir -p data/adressen
cd data/adressen

# first get the BAG
wget -nd 'https://data.nlextract.nl/bag/csv/bag-adressen-full-laatst.csv.zip'
unzip -a bag-adressen-full-laatst.csv.zip
rm -f bag-adressen-full-laatst.csv.zip

# now get the wijken en buurten
wget -nd 'https://www.cbs.nl/-/media/_pdf/2017/36/buurt_2017.zip'
unzip -a buurt_2017.zip
rm -f buurt_2017.zip

# TODO: match ....

# TODO: load ...
