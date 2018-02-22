#!/bin/sh

cd /opt/stm
mkdir -p data/adressen
cd data/adressen

# first get the BAG
# if [ -s bag-adressen-full-laatst.csv.zip ];
# then
#   echo "Have BAG data"
# else
#   wget -nd 'https://data.nlextract.nl/bag/csv/bag-adressen-full-laatst.csv.zip'
#   unzip -a -o bag-adressen-full-laatst.csv.zip
# fi
#rm -f bag-adressen-full-laatst.csv.zip

# now get the wijken en buurten
if [ -s buurt_2017.zip ];
then
  echo "Has buurt shapes"
else
  wget -nd 'https://www.cbs.nl/-/media/_pdf/2017/36/buurt_2017.zip'
  unzip -a -o buurt_2017.zip
fi
#rm -f buurt_2017.zip

for t in gem buurt wijk;
do
  ogr2ogr -f "ESRI Shapefile" "${t}_2017_recoded" "${t}_2017.shp" -s_srs EPSG:28992 -t_srs EPSG:4326
done

# cp bagadres-full.csv ../../docker/docker-entrypoint-initdb.d

# /opt/stm/bin/shape-props-to-json.py wijk_2017_recoded/wijk_2017.shp >data/adressen/wijken.json
# /opt/stm/bin/shape-props-to-json.py buurt_2017_recoded/buurt_2017.shp >data/adressen/buurten.json
