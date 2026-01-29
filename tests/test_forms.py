#!/usr/bin/env python

import unittest

from tests import app
from werkzeug.datastructures import MultiDict
from app.forms import EditForm
from app.models import Record

from tests.record_to_test import record_to_test

class TestEditForm(unittest.TestCase):
    def test_good(self):
        with app.test_request_context('/'):
            r = Record(**record_to_test(app.config["ELECTION_DATE"]))
            form = EditForm(MultiDict(r.record))
            result = form.validate()
            for field, errors in form.errors.items():
                print(field)
                print(errors)
                print()
            self.assertEqual(result, True)
