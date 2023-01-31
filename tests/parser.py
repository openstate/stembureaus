#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app.parser import BaseParser, ExcelParser

test_record1 = {
    'nummer_stembureau': 516.0,
    'naam_stembureau': 'Stadhuis',
    'type_stembureau': 'regulier',
    'website_locatie': (
        'https://www.denhaag.nl/nl/bestuur-en-organisatie/'
        'contact-met-de-gemeente/stadhuis-den-haag.htm'
    ),
    'bag_nummeraanduiding_id': '0518200000747446',
    'extra_adresaanduiding': 'Via de deur links',
    'x': '81611.0',
    'y': '454909.0',
    'latitude': '52.0775912',
    'longitude': '4.3166395',
    'openingstijd': '2023-03-15T07:30:00',
    'sluitingstijd': '2023-03-15T21:00:00',
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'ja',
    'toegankelijke_ov_halte': 'binnen 100 meter, rolstoeltoegankelijk, geleidelijnen',
    'akoestiek': 'ja',
    'auditieve_hulpmiddelen': 'gebarentolk, schrijftolk',
    'visuele_hulpmiddelen': 'stemmal, soundbox, vrijwilliger/host aanwezig, geleidelijnen',
    'gehandicaptentoilet': 'ja',
    'extra_toegankelijkheidsinformatie': 'prikkelarm stembureau, stembureau is volledig toegankelijk voor mensen met een lichamelijke beperking er is echter geen gehandicaptenparkeerplaats',
    'tellocatie': 'ja',
    'contactgegevens_gemeente': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'verkiezingswebsite_gemeente': 'https://www.stembureausindenhaag.nl/',
    'verkiezingen': ['waterschapsverkiezingen voor Delfland']
}

test_record2 = {
    'nummer_stembureau': 517.0,
    'naam_stembureau': 'Stadhuis',
    'type_stembureau': 'bijzonder',
    'website_locatie': (
        'https://www.denhaag.nl/nl/bestuur-en-organisatie/'
        'contact-met-de-gemeente/stadhuis-den-haag.htm'
    ),
    'bag_nummeraanduiding_id': '0518200000747446',
    'extra_adresaanduiding': '',
    'x': '81611.0',
    'y': '454909.0',
    'latitude': '52.0775912',
    'longitude': '4.3166395',
    'openingstijd': '2023-03-15T02:30:00',
    'sluitingstijd': '2023-03-15T22:00:00',
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'nee',
    'toegankelijke_ov_halte': '',
    'akoestiek': 'nee',
    'auditieve_hulpmiddelen': '',
    'visuele_hulpmiddelen': '',
    'gehandicaptentoilet': 'nee',
    'extra_toegankelijkheidsinformatie': '',
    'tellocatie': 'nee',
    'contactgegevens_gemeente': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'verkiezingswebsite_gemeente': 'https://www.stembureausindenhaag.nl/',
    'verkiezingen': ''
}


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
            os.path.dirname(os.path.abspath(__file__)),
            'data/waarismijnstemlokaal.nl_invulformulier.xlsx'
        )
        self.records = [test_record1, test_record2]

    # After running _get_headers the list
    # of headers should contain all values from column A in
    # the spreadsheet, even the ones that don't hold values
    def test_get_headers_good(self):
        wb = open_workbook(self.file_path)
        sh = wb.sheet_by_index(1)
        headers = self.parser._get_headers(sh)
        self.assertListEqual(
            headers,
            [
                'nummer_stembureau',
                'naam_stembureau',
                'type_stembureau',
                'website_locatie',
                'bag_nummeraanduiding_id',
                'extra_adresaanduiding',
                'x',
                'y',
                'latitude',
                'longitude',
                'openingstijd',
                'sluitingstijd',
                'toegankelijk_voor_mensen_met_een_lichamelijke_beperking',
                'toegankelijke_ov_halte',
                'akoestiek',
                'auditieve_hulpmiddelen',
                'visuele_hulpmiddelen',
                'gehandicaptentoilet',
                'extra_toegankelijkheidsinformatie',
                'tellocatie',
                'contactgegevens_gemeente',
                'verkiezingswebsite_gemeente',
                'verkiezingen'
            ]
        )

    # Test if the records are parsed correctly. This should still
    # include the fields that will not hold any value (e.g.,
    # 'bereikbaarheid') and exclude all fields that are added
    # later (e.g., 'gemeente')
    def test_get_rows_good(self):
        rows = self.parser.parse(self.file_path)
        self.maxDiff = None
        self.assertDictEqual(rows[0], self.records[0])
        self.assertDictEqual(rows[1], self.records[1])
