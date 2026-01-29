#!/usr/bin/env python

from tests.base_test_class import BaseTestClass
from werkzeug.datastructures import MultiDict
from app.models import Record

from tests.record_to_test import record_to_test

class TestEditForm(BaseTestClass):
    def test_good(self):
        from app.forms import EditForm
        with self.app.test_request_context('/'):
            r = Record(**record_to_test(self.app.config["ELECTION_DATE"]))
            form = EditForm(MultiDict(r.record))
            result = form.validate()
            for field, errors in form.errors.items():
                print(field)
                print(errors)
                print()
            self.assertEqual(result, True)
