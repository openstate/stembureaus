#!/usr/bin/env python

import unittest

from app.validator import Validator, RecordValidator


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()

    def test_parse(self):
        validated, result = self.validator.validate()
        self.assertEqual(validated, True)
        self.assertEqual(result, [])
