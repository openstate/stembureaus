#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app.parser import BaseParser, ExcelParser

test_record1 = {
    'stembureau_of_afgiftepunt': 'Stembureau',
    'nummer_stembureau_of_afgiftepunt': 516.0,
    'naam_stembureau_of_afgiftepunt': 'Stadhuis',
    'website_locatie': (
        'https://www.denhaag.nl/nl/bestuur-en-organisatie/'
        'contact-met-de-gemeente/stadhuis-den-haag.htm'
    ),
    'bag_referentienummer': '0518200000747446',
    'extra_adresaanduiding': 'Via de deur links',
    'x': '81611.0',
    'y': '454909.0',
    'longitude': '4.3166395',
    'latitude': '52.0775912',
    'openingstijden_10_03_2021': '',
    'openingstijden_11_03_2021': '',
    'openingstijden_12_03_2021': '',
    'openingstijden_13_03_2021': '',
    'openingstijden_14_03_2021': '',
    'openingstijden_15_03_2021': '2021-03-15T07:30:00 tot 2021-03-15T21:00:00',
    'openingstijden_16_03_2021': '2021-03-16T07:30:00 tot 2021-03-16T21:00:00',
    'openingstijden_17_03_2021': '2021-03-17T07:30:00 tot 2021-03-17T21:00:00',
    'mindervaliden_toegankelijk': 'Y',
    'akoestiek': 'Y',
    'auditieve_hulpmiddelen': 'Doventolk, ringleiding',
    'visuele_hulpmiddelen': 'Leesloep',
    'mindervalide_toilet_aanwezig': 'Y',
    'tellocatie': 'Y',
    'contactgegevens': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'beschikbaarheid': 'https://www.stembureausindenhaag.nl/'
    #'verkiezingen': ['waterschapsverkiezingen voor Delfland']
}

test_record2 = {
    'stembureau_of_afgiftepunt': 'Afgiftepunt',
    'nummer_stembureau_of_afgiftepunt': 517.0,
    'naam_stembureau_of_afgiftepunt': 'Stadhuis',
    'website_locatie': (
        'https://www.denhaag.nl/nl/bestuur-en-organisatie/'
        'contact-met-de-gemeente/stadhuis-den-haag.htm'
    ),
    'bag_referentienummer': '0518200000747446',
    'extra_adresaanduiding': '',
    'x': '81611.0',
    'y': '454909.0',
    'longitude': '4.3166395',
    'latitude': '52.0775912',
    'openingstijden_10_03_2021': '2021-03-10T07:30:00 tot 2021-03-10T21:00:00',
    'openingstijden_11_03_2021': '2021-03-11T07:30:00 tot 2021-03-11T21:00:00',
    'openingstijden_12_03_2021': '2021-03-12T07:30:00 tot 2021-03-12T21:00:00',
    'openingstijden_13_03_2021': '2021-03-13T07:30:00 tot 2021-03-13T21:00:00',
    'openingstijden_14_03_2021': '2021-03-14T07:30:00 tot 2021-03-14T21:00:00',
    'openingstijden_15_03_2021': '2021-03-15T07:30:00 tot 2021-03-15T21:00:00',
    'openingstijden_16_03_2021': '2021-03-16T07:30:00 tot 2021-03-16T21:00:00',
    'openingstijden_17_03_2021': '2021-03-17T07:30:00 tot 2021-03-17T21:00:00',
    'mindervaliden_toegankelijk': 'N',
    'akoestiek': 'N',
    'auditieve_hulpmiddelen': '',
    'visuele_hulpmiddelen': '',
    'mindervalide_toilet_aanwezig': 'N',
    'tellocatie': 'N',
    'contactgegevens': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'beschikbaarheid': 'https://www.stembureausindenhaag.nl/'
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
                'stembureau_of_afgiftepunt',
                'nummer_stembureau_of_afgiftepunt',
                'naam_stembureau_of_afgiftepunt',
                'website_locatie',
                'bag_referentienummer',
                'extra_adresaanduiding',
                'x',
                'y',
                'longitude',
                'latitude',
                'openingstijden_10_03_2021',
                'openingstijden_11_03_2021',
                'openingstijden_12_03_2021',
                'openingstijden_13_03_2021',
                'openingstijden_14_03_2021',
                'openingstijden_15_03_2021',
                'openingstijden_16_03_2021',
                'openingstijden_17_03_2021',
                'mindervaliden_toegankelijk',
                'akoestiek',
                'auditieve_hulpmiddelen',
                'visuele_hulpmiddelen',
                'mindervalide_toilet_aanwezig',
                'tellocatie',
                'contactgegevens',
                'beschikbaarheid',
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
