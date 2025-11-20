#!/usr/bin/env python

import unittest

from flask import current_app
from werkzeug.datastructures import MultiDict
from app.forms import EditForm
from app.models import Record

from tests.test_record import test_record


class TestEditForm(unittest.TestCase):
    def test_good(self):
        current_app.config['WTF_CSRF_ENABLED'] = False
        with current_app.test_request_context('/'):
            r = Record(**test_record)
            form = EditForm(MultiDict(r.record))
            result = form.validate()
            for field, errors in form.errors.items():
                print(field)
                print(errors)
                print()
            self.assertEqual(result, True)
