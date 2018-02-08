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
            'nummer stembureau': 1.0,
            'naam stembureau': 'Stadhuis I',
            'gebruikersdoel het gebouw': 'Kantoor',
            'bag referentie nummer': '0518200000747446',
            'extra adresaanduiding': '',
            'longitude': 4.3166395,
            'latitude': 52.0775912,
            'districtcode': '',
            'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
            'mindervaliden toegankelijk': 'Y',
            'invalidenparkeerplaatsen': 'N',
            'akoestiek': 'N',
            'mindervalide toilet aanwezig': 'Y',
            'kieskring id': 'Juinen',
            'hoofdstembureau': '',
            'website locatie': 'https://www.juinen.nl/',
            'contactgegevens': 'info@juinen.nl',
            'beschikbaarheid': 'https://www.juinen.nl/verkiezingen-2018/'
        }, {
            'nummer stembureau': 2.0,
            'naam stembureau': 'Stadhuis II',
            'gebruikersdoel het gebouw': 'Kantoor',
            'bag referentie nummer': '0518200000747446',
            'extra adresaanduiding': '',
            'longitude': 4.3166395,
            'latitude': 52.0775912,
            'districtcode': '',
            'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
            'mindervaliden toegankelijk': 'Y',
            'invalidenparkeerplaatsen': 'N',
            'akoestiek': 'N',
            'mindervalide toilet aanwezig': 'Y',
            'kieskring id': 'Juinen',
            'hoofdstembureau': '',
            'website locatie': 'https://www.juinen.nl/',
            'contactgegevens': 'info@juinen.nl',
            'beschikbaarheid': 'https://www.juinen.nl/verkiezingen-2018/'
        }]

    def test_has_correct_num_sheets(self):
        wb = open_workbook(self.file_path)
        self.assertTrue(self.parser._has_correct_sheet_count(wb))

    def test_get_headers_good(self):
        wb = open_workbook(self.file_path)
        sh = wb.sheet_by_index(1)
        headers = self.parser._get_headers(sh)
        self.assertListEqual(headers, [
            'nummer stembureau',
            'naam stembureau',
            'gebruikersdoel het gebouw',
            'website locatie',
            'bag referentie nummer',
            'extra adresaanduiding',
            'longitude',
            'latitude',
            'districtcode',
            'openingstijden',
            'mindervaliden toegankelijk',
            'invalidenparkeerplaatsen',
            'akoestiek',
            'mindervalide toilet aanwezig',
            'kieskring id',
            'hoofdstembureau',
            'contactgegevens',
            'beschikbaarheid'])

    def test_get_rows_good(self):
        headers, rows = self.parser.parse(self.file_path)
        self.assertEqual(len(rows), 2)
        self.maxDiff = None
        self.assertDictEqual(rows[0], self.records[0])
        self.assertDictEqual(rows[1], self.records[1])
