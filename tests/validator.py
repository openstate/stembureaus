#!/usr/bin/env python

import unittest

from app.validator import Validator, RecordValidator
import app
from app.models import Record
from tests.test_record import test_record


class TestRecordValidator(unittest.TestCase):
    def setUp(self):
        self.record_validator = RecordValidator()
        self.test_record = Record(**test_record)

    def test_parse(self):
        with app.app.test_request_context('/'):
            result, errors, form = self.record_validator.validate(
                record=self.test_record.record
            )
        self.assertEqual(result, True)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()
        self.test_records = [
            Record(**x).record for x in [test_record, test_record]
        ]

    def test_parse_empty(self):
        results = self.validator.validate()
        self.assertEqual(results['no_errors'], True)
        self.assertEqual(results['results'], {})

    def test_parse_one(self):
        with app.app.test_request_context('/'):
            results = self.validator.validate(
                records=self.test_records)
        self.assertEqual(results['no_errors'], True)
        # TODO test results['results'] output
        #self.assertEqual(results['results'], {})
