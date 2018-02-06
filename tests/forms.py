#!/usr/bin/env python

import unittest

from werkzeug.datastructures import MultiDict
from app.forms import VotingStationForm
import app


class TestVotingStationForm(unittest.TestCase):
    def test_good(self):
        record = {
            'gemeente': 'Utrecht',
            'gemeente_code': 'GM0344',
            'stembureau_nummer': 1,
            'stembureau_naam': 'Utrecht Centraal'
        }
        app.app.config['WTF_CSRF_ENABLED'] = False
        with app.app.test_request_context('/'):
            form = VotingStationForm(MultiDict(record))
            result = form.validate()
            self.assertEqual(result, True)
