CREATE DATABASE IF NOT EXISTS `stembureaus`;
CREATE TABLE IF NOT EXISTS `stembureaus`.`bag` (
  openbareruimte VARCHAR(255),
  huisnummer varchar(5),
  huisletter varchar(5),
  huisnummertoevoeging varchar(5),
  postcode varchar(6),
  woonplaats varchar(255),
  gemeente varchar(255),
  provincie varchar(255),
  nummeraanduiding varchar(24) primary key,
  verblijfsobjectgebruiksdoel varchar(255),
  oppervlakteverblijfsobject varchar(10),
  verblijfsobjectstatus varchar(255),
  object_id varchar(24),
  object_type varchar(10),
  nevenadres varchar(1),
  pandid varchar(24),
  pandstatus varchar(255),
  pandbouwjaar varchar(20),
  x DECIMAL(25,9),
  y DECIMAL(25,9),
  lon decimal(24, 16),
  lat decimal(24, 16),
  index qidx (openbareruimte, huisnummer, huisnummertoevoeging, woonplaats)
) CHARACTER SET=utf8;

LOAD DATA LOCAL INFILE "/docker-entrypoint-initdb.d/bagadres-full.csv"
INTO TABLE `stembureaus`.`bag`
COLUMNS TERMINATED BY ';'
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;
