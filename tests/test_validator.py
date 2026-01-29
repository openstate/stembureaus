#!/usr/bin/env python

from app.models import Record
from tests.base_test_class import BaseTestClass
from tests.record_to_test import record_to_test


class TestRecordValidator(BaseTestClass):
    def setUp(self):
        super().setUp()
        from app.validator import RecordValidator
        self.record_validator = RecordValidator()
        self.test_record = Record(**record_to_test(self.app.config["ELECTION_DATE"]))

    def test_parse(self):
        with self.app.test_request_context('/'):
            result, errors, form = self.record_validator.validate(
                record=self.test_record.record
            )
        self.assertEqual(result, True)


class TestValidator(BaseTestClass):
    def setUp(self):
        super().setUp()
        from app.validator import Validator
        self.validator = Validator()
        test_rec = record_to_test(self.app.config["ELECTION_DATE"])
        self.test_records = [
            Record(**x).record for x in [test_rec, test_rec]
        ]

    def test_parse_empty(self):
        results = self.validator.validate()
        self.assertEqual(results['no_errors'], True)
        self.assertEqual(results['results'], {})

    def test_parse_one(self):
        with self.app.test_request_context('/'):
            results = self.validator.validate(
                records=self.test_records)
        self.assertEqual(results['no_errors'], True)
        # TODO test results['results'] output
        #self.assertEqual(results['results'], {})


class TestClosingTimeValidation(BaseTestClass):
    def setUp(self):
        super().setUp()
        from app.validator import RecordValidator
        self.record_validator = RecordValidator()
        self.test_record = Record(**record_to_test(self.app.config["ELECTION_DATE"], closing_time='21:01:00'))

    def test_parse(self):
        with self.app.test_request_context('/'):
            result, errors, form = self.record_validator.validate(
                record=self.test_record.record
            )
        self.assertEqual(result, False)
        self.assertEqual(errors, {'sluitingstijd': ['De sluitingstijd mag niet later zijn dan 21:00.']})
