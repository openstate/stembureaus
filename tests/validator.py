#!/usr/bin/env python

import unittest

from app.validator import Validator, RecordValidator
import app


class TestRecordValidator(unittest.TestCase):
    def setUp(self):
        self.record_validator = RecordValidator()

    def test_parse(self):
        record = {
            'gemeente': 'Utrecht',
            'gemeente_code': 'GM0344',
            'stembureau_nummer': 1,
            'stembureau_naam': 'Utrecht Centraal'
        }
        with app.app.test_request_context('/'):
            validated, errors = self.record_validator.validate(
                1, record=record)
        self.assertEqual(validated, True)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()

    def test_parse(self):
        validated, result = self.validator.validate()
        self.assertEqual(validated, True)
        self.assertEqual(result, [])
