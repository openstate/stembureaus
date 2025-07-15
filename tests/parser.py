#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app import app
from app.parser import BaseParser, ExcelParser

test_record1 = {
    'nummer_stembureau': 517.0,
    'naam_stembureau': 'Stadhuis',
    'type_stembureau': 'regulier',
    'website_locatie': (
        'https://www.denhaag.nl/nl/contact-met-de-gemeente/stadhuis-den-haag/'
    ),
    'bag_nummeraanduiding_id': '0518200000747446',
    'extra_adresaanduiding': 'Ingang aan achterkant gebouw',
    'x': '81611.0',
    'y': '454909.0',
    'latitude': '52.0775912',
    'longitude': '4.3166395',
    'openingstijd': '2025-10-29T07:30:00',
    'sluitingstijd': '2025-10-29T21:00:00',
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'ja',
    'toegankelijke_ov_halte': 'ja',
    'gehandicaptentoilet': 'ja',
    'host': 'ja',
    'geleidelijnen': 'buiten en binnen',
    'stemmal_met_audio_ondersteuning': 'ja',
    'kandidatenlijst_in_braille': 'ja',
    'kandidatenlijst_met_grote_letters': 'ja',
    'gebarentolk_ngt': 'op locatie',
    'gebarentalig_stembureaulid_ngt': 'ja',
    'akoestiek_geschikt_voor_slechthorenden': 'ja',
    'prikkelarm': 'ja',
    'extra_toegankelijkheidsinformatie': (
        'Dit stembureau is ingericht voor kwetsbare mensen, stembureau is '
        'volledig toegankelijk voor mensen met een lichamelijke beperking er '
        'is echter geen gehandicaptenparkeerplaats, gebarentolk op locatie '
        '(NGT) is aanwezig van 10:00-12:00 en 16:00-18:00, oefenstembureau'
    ),
    'overige_informatie': '',
    'tellocatie': 'ja',
    'contactgegevens_gemeente': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'verkiezingswebsite_gemeente': 'https://www.stembureausindenhaag.nl/'
}

# If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
# to test_record1
if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
    test_record1['verkiezingen'] = 'waterschapsverkiezingen voor Delfland'

test_record2 = {
    'nummer_stembureau': 516.0,
    'naam_stembureau': 'Stadhuis',
    'type_stembureau': 'bijzonder',
    'website_locatie': (
        'https://www.denhaag.nl/nl/contact-met-de-gemeente/stadhuis-den-haag/'
    ),
    'bag_nummeraanduiding_id': '0518200000747446',
    'extra_adresaanduiding': '',
    'x': '81611.0',
    'y': '454909.0',
    'latitude': '52.0775912',
    'longitude': '4.3166395',
    'openingstijd': '2025-10-29T02:30:00',
    'sluitingstijd': '2025-10-29T20:00:00',
    'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'nee',
    'toegankelijke_ov_halte': 'nee',
    'gehandicaptentoilet': 'nee',
    'host': 'nee',
    'geleidelijnen': 'nee',
    'stemmal_met_audio_ondersteuning': 'nee',
    'kandidatenlijst_in_braille': 'nee',
    'kandidatenlijst_met_grote_letters': 'nee',
    'gebarentolk_ngt': 'nee',
    'gebarentalig_stembureaulid_ngt': 'nee',
    'akoestiek_geschikt_voor_slechthorenden': 'nee',
    'prikkelarm': 'nee',
    'extra_toegankelijkheidsinformatie': '',
    'overige_informatie': '',
    'tellocatie': 'nee',
    'contactgegevens_gemeente': (
        'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
        'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
    ),
    'verkiezingswebsite_gemeente': 'https://www.stembureausindenhaag.nl/'
}

# If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
# to test_record2
if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
    test_record2['verkiezingen'] = ''


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
        accepted_headers = [
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
            'gehandicaptentoilet',
            'host',
            'geleidelijnen',
            'stemmal_met_audio_ondersteuning',
            'kandidatenlijst_in_braille',
            'kandidatenlijst_met_grote_letters',
            'gebarentolk_ngt',
            'gebarentalig_stembureaulid_ngt',
            'akoestiek_geschikt_voor_slechthorenden',
            'prikkelarm',
            'extra_toegankelijkheidsinformatie',
            'overige_informatie',
            'tellocatie',
            'contactgegevens_gemeente',
            'verkiezingswebsite_gemeente'
        ]
        # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
        # to the accepted_headers
        if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            accepted_headers += ['verkiezingen']
        self.assertListEqual(headers, accepted_headers)

    # Test if the records are parsed correctly. This should still
    # include the fields that will not hold any value (e.g.,
    # 'bereikbaarheid') and exclude all fields that are added
    # later (e.g., 'gemeente')
    def test_get_rows_good(self):
        rows = self.parser.parse(self.file_path)
        self.maxDiff = None
        self.assertDictEqual(rows[0], self.records[0])
        self.assertDictEqual(rows[1], self.records[1])
