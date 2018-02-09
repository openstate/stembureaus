#!/usr/bin/env python

import unittest

from app.validator import Validator, RecordValidator
import app
from app.models import Record

class TestRecordValidator(unittest.TestCase):
    def setUp(self):
        self.record_validator = RecordValidator()
        self.test_record = Record(**{
            'gemeente': 'Juinen',
            'cbs gemeentecode': 'GM9999',
            'nummer stembureau': 1.0,
            'naam stembureau': 'Stadhuis I',
            'gebruikersdoel het gebouw': 'Kantoor',
            'wijknaam': 'Centrum',
            'cbs wijknummer': 'WK999999',
            'buurtnaam': 'Centrum',
            'cbs buurtnummer': 'BU99999999',
            'bag referentie nummer': '0518200000747446',
            'straatnaam': 'Dorpstraat',
            'huisnummer': 1.0,
            'huisnummertoevoeging': '',
            'postcode': '1111 AA',
            'plaats': 'Juinen',
            'extra adresaanduiding': '',
            'x': 81611.0,
            'y': 454909.0,
            'longitude': 4.3166395,
            'latitude': 52.0775912,
            'districtcode': '',
            'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
            'mindervaliden toegankelijk': 'Y',
            'invalidenparkeerplaatsen': 'N',
            'akoestiek': 'N',
            'mindervalide toilet aanwezig': 'Y',
            'kieskring id': '',
            'hoofdstembureau': '',
            'contactgegevens': '',
            'beschikbaarheid': '',
            'website locatie': 'https://www.juinen.nl/',
            'contactgegevens': 'info@juinen.nl',
            'beschikbaarheid': 'https://www.juinen.nl/'
        })

    def test_parse(self):
        with app.app.test_request_context('/'):
            validated, errors = self.record_validator.validate(
                1, record=self.test_record.record)
        self.assertEqual(validated, True)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()
        self.test_records = [Record(**x).record for x in [
            {
                'gemeente': 'Juinen',
                'cbs gemeentecode': 'GM9999',
                'nummer stembureau': 1.0,
                'naam stembureau': 'Stadhuis I',
                'gebruikersdoel het gebouw': 'Kantoor',
                'wijknaam': 'Centrum',
                'cbs wijknummer': 'WK999999',
                'buurtnaam': 'Centrum',
                'cbs buurtnummer': 'BU99999999',
                'bag referentie nummer': '0518200000747446',
                'straatnaam': 'Dorpstraat',
                'huisnummer': 1.0,
                'huisnummertoevoeging': '',
                'postcode': '1111 AA',
                'plaats': 'Juinen',
                'extra adresaanduiding': '',
                'x': 81611.0,
                'y': 454909.0,
                'longitude': 4.3166395,
                'latitude': 52.0775912,
                'districtcode': '',
                'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
                'mindervaliden toegankelijk': 'Y',
                'invalidenparkeerplaatsen': 'N',
                'akoestiek': 'N',
                'mindervalide toilet aanwezig': 'Y',
                'kieskring id': '',
                'hoofdstembureau': '',
                'contactgegevens': '',
                'beschikbaarheid': '',
                'website locatie': 'https://www.juinen.nl/',
                'contactgegevens': 'info@juinen.nl',
                'beschikbaarheid': 'https://www.juinen.nl/'
            }, {
                'gemeente': 'Juinen',
                'cbs gemeentecode': 'GM9999',
                'nummer stembureau': 2.0,
                'naam stembureau': 'Stadhuis I',
                'gebruikersdoel het gebouw': 'Kantoor',
                'wijknaam': 'Centrum',
                'cbs wijknummer': 'WK999999',
                'buurtnaam': 'Centrum',
                'cbs buurtnummer': 'BU99999999',
                'bag referentie nummer': '0518200000747446',
                'straatnaam': 'Dorpstraat',
                'huisnummer': 1.0,
                'huisnummertoevoeging': '',
                'postcode': '1111 AA',
                'plaats': 'Juinen',
                'extra adresaanduiding': '',
                'x': 81611.0,
                'y': 454909.0,
                'longitude': 4.3166395,
                'latitude': 52.0775912,
                'districtcode': '',
                'openingstijden': '2017-03-21T07:30:00 tot 2017-03-21T21:00:00',
                'mindervaliden toegankelijk': 'Y',
                'invalidenparkeerplaatsen': 'N',
                'akoestiek': 'N',
                'mindervalide toilet aanwezig': 'Y',
                'kieskring id': '',
                'hoofdstembureau': '',
                'contactgegevens': '',
                'beschikbaarheid': '',
                'website locatie': 'https://www.juinen.nl/',
                'contactgegevens': 'info@juinen.nl',
                'beschikbaarheid': 'https://www.juinen.nl/'
            }]]

    def test_parse_empty(self):
        validated, result = self.validator.validate()
        self.assertEqual(validated, True)
        self.assertEqual(result, [])

    def test_parse_one(self):
        with app.app.test_request_context('/'):
            validated, result = self.validator.validate(
                records=self.test_records)
        self.assertEqual(validated, True)
        self.assertEqual(result, [])
