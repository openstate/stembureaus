#!/usr/bin/env python

import unittest

from werkzeug.datastructures import MultiDict
from app.forms import EditForm
from app.models import Record
import app


class TestEditForm(unittest.TestCase):
    def test_good(self):
        record = {
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
        }
        app.app.config['WTF_CSRF_ENABLED'] = False
        with app.app.test_request_context('/'):
            r = Record(**record)
            form = EditForm(MultiDict(r.record))
            result = form.validate()
            self.assertEqual(result, True)
