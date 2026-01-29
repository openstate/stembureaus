#!/usr/bin/env python
import os

import pyexcel

from tests.base_test_class import BaseTestClass


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
    'toilet',
    'host',
    'geleidelijnen',
    'stemmal_met_audio_ondersteuning',
    'kandidatenlijst_in_braille',
    'kandidatenlijst_met_grote_letters',
    'gebarentolk_ngt',
    'gebarentalig_stembureaulid_ngt',
    'akoestiek_geschikt_voor_slechthorenden',
    'prikkelarm',
    'prokkelduo',
    'extra_toegankelijkheidsinformatie',
    'overige_informatie',
    'tellocatie',
    'contactgegevens_gemeente',
    'verkiezingswebsite_gemeente'
]

# From https://gist.github.com/twolfson/13f5f5784f67fd49b245
class BaseTestParsing(BaseTestClass):
    file_name = ''

    @classmethod
    def setUpClass(cls):
        """On inherited classes, run our `setUp` method"""
        if cls is not BaseTestParsing and cls.setUp is not BaseTestParsing.setUp:
            orig_setUp = cls.setUp
            def setUpOverride(self, *args, **kwargs):
                BaseTestParsing.setUp(self)
                return orig_setUp(self, *args, **kwargs)
            cls.setUp = setUpOverride

    def setUp(self):
        super().setUp()
        from app.parser import UploadFileParser
        self.parser = UploadFileParser()
        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.file_name)
        self.parser._set_parser(self.file_path)
        self.records = [self.get_test_record1(), self.get_test_record2()]
        self.accepted_headers = accepted_headers

    def get_headers_good_impl(self):
        with self.app.test_request_context('/'):
            sh = pyexcel.get_array(file_name = self.file_path, sheet_name='Attributen')
            headers = self.parser.parser._get_headers(sh)
        # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
        # to the accepted_headers
        if [x for x in self.app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            self.accepted_headers += ['verkiezingen']
        self.assertListEqual(headers, self.accepted_headers)

    def get_rows_good_impl(self):
        rows = self.parser.parse(self.file_path)
        self.maxDiff = None
        self.assertDictEqual(rows[0], self.records[0])
        self.assertDictEqual(rows[1], self.records[1])

    def get_test_record1(self):
        test_record1 = {
            'nummer_stembureau': 517,
            'naam_stembureau': 'Stadhuis',
            'type_stembureau': 'regulier',
            'website_locatie': (
                'https://www.denhaag.nl/nl/contact-met-de-gemeente/stadhuis-den-haag/'
            ),
            'bag_nummeraanduiding_id': '0518200000747446',
            'extra_adresaanduiding': 'Ingang aan achterkant gebouw',
            'x': '81611',
            'y': '454909',
            'latitude': '52.0775912',
            'longitude': '4.3166395',
            'openingstijd': '2026-03-18T07:30:00',
            'sluitingstijd': '2026-03-18T21:00:00',
            'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'ja',
            'toegankelijke_ov_halte': 'ja',
            'toilet': 'ja, toegankelijk toilet',
            'host': 'ja',
            'geleidelijnen': 'buiten en binnen',
            'stemmal_met_audio_ondersteuning': 'ja',
            'kandidatenlijst_in_braille': 'ja',
            'kandidatenlijst_met_grote_letters': 'ja',
            'gebarentolk_ngt': 'op locatie',
            'gebarentalig_stembureaulid_ngt': 'ja',
            'akoestiek_geschikt_voor_slechthorenden': 'ja',
            'prikkelarm': 'ja',
            'prokkelduo': 'ja',
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
            'verkiezingswebsite_gemeente': 'https://www.denhaag.nl/nl/verkiezingen/'
        }

        # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
        # to test_record1
        if [x for x in self.app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            test_record1['verkiezingen'] = 'waterschapsverkiezingen voor Delfland'

        return test_record1

    def get_test_record2(self):
        test_record2 = {
            'nummer_stembureau': 516,
            'naam_stembureau': 'Stadhuis',
            'type_stembureau': 'bijzonder',
            'website_locatie': (
                'https://www.denhaag.nl/nl/contact-met-de-gemeente/stadhuis-den-haag/'
            ),
            'bag_nummeraanduiding_id': '0518200000747446',
            'extra_adresaanduiding': '',
            'x': '81611',
            'y': '454909',
            'latitude': '52.0775912',
            'longitude': '4.3166395',
            'openingstijd': '2026-03-18T02:30:00',
            'sluitingstijd': '2026-03-18T20:00:00',
            'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': 'nee',
            'toegankelijke_ov_halte': 'nee',
            'toilet': 'nee',
            'host': 'nee',
            'geleidelijnen': 'nee',
            'stemmal_met_audio_ondersteuning': 'nee',
            'kandidatenlijst_in_braille': 'nee',
            'kandidatenlijst_met_grote_letters': 'nee',
            'gebarentolk_ngt': 'nee',
            'gebarentalig_stembureaulid_ngt': 'nee',
            'akoestiek_geschikt_voor_slechthorenden': 'nee',
            'prikkelarm': 'nee',
            'prokkelduo': 'nee',
            'extra_toegankelijkheidsinformatie': '',
            'overige_informatie': '',
            'tellocatie': 'nee',
            'contactgegevens_gemeente': (
                'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
                'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
            ),
            'verkiezingswebsite_gemeente': 'https://www.denhaag.nl/nl/verkiezingen/'
        }

        # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
        # to test_record2
        if [x for x in self.app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            test_record2['verkiezingen'] = ''

        return test_record2

class TestXlsxParsing(BaseTestParsing):
    file_name = 'data/waarismijnstemlokaal.nl_invulformulier.xlsx'

    # After running _get_headers the list
    # of headers should contain all values from column A in
    # the spreadsheet, even the ones that don't hold values
    def test_get_headers_good(self):
        self.get_headers_good_impl()

    # Test if the records are parsed correctly. This should still
    # include the fields that will not hold any value (e.g.,
    # 'bereikbaarheid') and exclude all fields that are added
    # later (e.g., 'gemeente')
    def test_get_rows_good(self):
        self.get_rows_good_impl()


class TestXlsParsing(BaseTestParsing):
    file_name = 'data/waarismijnstemlokaal.nl_invulformulier.xls'

    # After running _get_headers the list
    # of headers should contain all values from column A in
    # the spreadsheet, even the ones that don't hold values
    def test_get_headers_good(self):
        self.get_headers_good_impl()

    # Test if the records are parsed correctly. This should still
    # include the fields that will not hold any value (e.g.,
    # 'bereikbaarheid') and exclude all fields that are added
    # later (e.g., 'gemeente')
    def test_get_rows_good(self):
        self.get_rows_good_impl()


class TestOdsParsing(BaseTestParsing):
    file_name = 'data/waarismijnstemlokaal.nl_invulformulier.ods'

    # After running _get_headers the list
    # of headers should contain all values from column A in
    # the spreadsheet, even the ones that don't hold values
    def test_get_headers_good(self):
        self.get_headers_good_impl()

    # Test if the records are parsed correctly. This should still
    # include the fields that will not hold any value (e.g.,
    # 'bereikbaarheid') and exclude all fields that are added
    # later (e.g., 'gemeente')
    def test_get_rows_good(self):
        self.get_rows_good_impl()
