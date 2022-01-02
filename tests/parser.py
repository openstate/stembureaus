#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app.parser import BaseParser, ExcelParser

test_record1 = {
    'nummer_stembureau': 516.0,
    'naam_stembureau': 'Stadhuis',
    'website_locatie': (
        'https://www.denhaag.nl/nl/bestuur-en-organisatie/'
        'contact-met-de-gemeente/stadhuis-den-haag.htm'
    ),
    'bag_nummeraanduiding_id': '0518200000747446',
    'extra_adresaanduiding': 'Ingang aan achterkant gebouw',
    'x': '81611.0',
    'y': '454909.0',
    'latitude': '52.0775912',
    'longitude': '4.3166395',
    'openingstijden_14_03_2022': '2022-03-14T07:30:00 tot 2022-03-14T21:00:00',
    'openingstijden_15_03_2022': '2022-03-15T07:30:00 tot 2022-03-15T21:00:00',
    'openingstijden_16_03_2022': '2022-03-16T07:30:00 tot 2022-03-16T21:00:00',
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'ja',
    'akoestiek': 'ja',
    'auditieve_hulpmiddelen': 'gebarentolk',
    'visuele_hulpmiddelen': 'leesloep, stemmal, vrijwilliger/host aanwezig',
    'gehandicaptentoilet': 'ja',
    'tellocatie': 'ja',
    'contactgegevens gemeente': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'verkiezingswebsite gemeente': 'https://www.stembureausindenhaag.nl/'
    #'verkiezingen': ['waterschapsverkiezingen voor Delfland']
}

test_record2 = {
    'nummer_stembureau': 517.0,
    'naam_stembureau': 'Stadhuis',
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
    'openingstijden_14_03_2022': '2022-03-14T07:30:00 tot 2022-03-14T21:00:00',
    'openingstijden_15_03_2022': '2022-03-15T07:30:00 tot 2022-03-15T21:00:00',
    'openingstijden_16_03_2022': '2022-03-16T07:30:00 tot 2022-03-16T21:00:00',
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'nee',
    'akoestiek': 'nee',
    'auditieve_hulpmiddelen': '',
    'visuele_hulpmiddelen': '',
    'gehandicaptentoilet': 'nee',
    'tellocatie': 'nee',
    'contactgegevens gemeente': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'verkiezingswebsite gemeente': 'https://www.stembureausindenhaag.nl/'
    #'verkiezingen': ['waterschapsverkiezingen voor Delfland']
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

    # After running _get_headers and _clean_headers the list
    # of headers should contain all values from column A in
    # the spreadsheet, even the ones that don't hold values
    # (e.g. 'bereikbaarheid')
    def test_get_headers_good(self):
        wb = open_workbook(self.file_path)
        sh = wb.sheet_by_index(1)
        headers = self.parser._get_headers(sh)
        clean_headers = self.parser._clean_headers(headers)
        self.assertListEqual(
            clean_headers,
            [
                'nummer_stembureau',
                'naam_stembureau',
                'website_locatie',
                'bag_nummeraanduiding_id',
                'extra_adresaanduiding',
                'x',
                'y',
                'latitude',
                'longitude',
                'openingstijden_14_03_2022',
                'openingstijden_15_03_2022',
                'openingstijden_16_03_2022',
                'toegankelijk_voor_mensen_met_een_lichamelijke_beperking',
                'akoestiek',
                'auditieve_hulpmiddelen',
                'visuele_hulpmiddelen',
                'gehandicaptentoilet',
                'tellocatie',
                'contactgegevens',
                'verkiezingswebsite gemeente',
                #'verkiezingen'
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
