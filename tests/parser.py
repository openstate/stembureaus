#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app.parser import BaseParser, ExcelParser


class TestBaseParser(unittest.TestCase):
    def setUp(self):
        self.parser = BaseParser()

    def test_parse(self):
        with self.assertRaises(NotImplementedError):
            self.parser.parse('/dev/null')


class TestExcelParser(unittest.TestCase):
    def setUp(self):
        self.parser = ExcelParser()
        self.file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data/juinen.xlsx')
        self.records = [{
            'nummer_stembureau': 1.0,
            'naam_stembureau': 'Stadhuis I',
            'gebruikersdoel_het_gebouw': 'Kantoor',
            'bag_referentienummer': '0518200000747446',
            'extra_adresaanduiding': '',
            'longitude': '4.3166395',
            'latitude': '52.0775912',
            'districtcode': '',
            'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
            'mindervaliden_toegankelijk': 'Y',
            'invalidenparkeerplaatsen': 'N',
            'akoestiek': 'N',
            'mindervalide_toilet_aanwezig': 'Y',
            'kieskring_id': 'Juinen',
            'hoofdstembureau': '',
            'website_locatie': 'https://www.juinen.nl/',
            'contactgegevens': 'info@juinen.nl',
            'beschikbaarheid': 'https://www.juinen.nl/verkiezingen-2018/'
        }, {
            'nummer_stembureau': 2.0,
            'naam_stembureau': 'Stadhuis II',
            'gebruikersdoel_het_gebouw': 'Kantoor',
            'bag_referentienummer': '0518200000747446',
            'extra_adresaanduiding': '',
            'longitude': '4.3166395',
            'latitude': '52.0775912',
            'districtcode': '',
            'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
            'mindervaliden_toegankelijk': 'Y',
            'invalidenparkeerplaatsen': 'N',
            'akoestiek': 'N',
            'mindervalide_toilet_aanwezig': 'Y',
            'kieskring_id': 'Juinen',
            'hoofdstembureau': '',
            'website_locatie': 'https://www.juinen.nl/',
            'contactgegevens': 'info@juinen.nl',
            'beschikbaarheid': 'https://www.juinen.nl/verkiezingen-2018/'
        }]

    def test_get_headers_good(self):
        wb = open_workbook(self.file_path)
        sh = wb.sheet_by_index(1)
        headers = self.parser._get_headers(sh)
        self.assertListEqual(headers, [
            'nummer_stembureau',
            'naam_stembureau',
            'gebruikersdoel_het_gebouw',
            'website_locatie',
            'bag_referentie_nummer',
            'extra_adresaanduiding',
            'longitude',
            'latitude',
            'districtcode',
            'openingstijden',
            'mindervaliden_toegankelijk',
            'invalidenparkeerplaatsen',
            'akoestiek',
            'mindervalide_toilet_aanwezig',
            'kieskring_id',
            'hoofdstembureau',
            'contactgegevens',
            'beschikbaarheid'])

    def test_get_rows_good(self):
        rows = self.parser.parse(self.file_path)
        self.maxDiff = None
        self.assertDictEqual(rows[0], self.records[0])
        self.assertDictEqual(rows[1], self.records[1])
