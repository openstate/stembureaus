CREATE DATABASE IF NOT EXISTS `stembureaus`;
CREATE TABLE IF NOT EXISTS `stembureaus`.`bag` (
  `object_id` VARCHAR(14) PRIMARY KEY,
  `gem_code` VARCHAR(6),
  `gem_naam` VARCHAR(255),
  `wijk_code` VARCHAR(8),
  `wijk_naam` VARCHAR(255),
  `buurt_code` VARCHAR(10),
  `buurt_naam` VARCHAR(255),
  `huisnummer` VARCHAR(10),
  `huisletter` VARCHAR(10),
  `huisnummertoevoeging` VARCHAR(10),
  `postcode` VARCHAR(6),
  `woonplaats` VARCHAR(255),
  INDEX `gem_naam_FI_1` (`gem_naam`),
  INDEX `wijk_naam_FI_1` (`wijk_naam`),
  INDEX `buurt_naam_FI_1` (`buurt_naam`),
  INDEX `postcode_FI_1` (`postcode`)
) CHARACTER SET=utf8;
