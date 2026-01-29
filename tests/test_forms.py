#!/usr/bin/env python

from app.utils import get_gemeente
from tests import app
from tests.base_test_class import BaseTestClass
from werkzeug.datastructures import MultiDict
from app.models import Record

from tests.record_to_test import record_to_test

class TestEditForm(BaseTestClass):
    AFFECTS_DB = True

    def test_good(self):
        from app.forms import EditForm
        with self.app.test_request_context('/'):
            r = Record(**record_to_test(self.app.config["ELECTION_DATE"]))
            form = EditForm(MultiDict(r.record))
            result = form.validate()
            self.assertEqual(result, True)

    def test_bag_same_municipality(self):
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_request_context('/'):
            r = Record(**record_to_test(app.config["ELECTION_DATE"]))
            form = EditForm(MultiDict(r.record))
            gemeente = get_gemeente('GM0518')
            result = form.validate_using_gemeente(gemeente)
            self.assertEqual(result, True)

    def test_bag_different_municipality(self):
        # Record is for Den Haag, BAG is from Alkmaar
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_request_context('/'):
            r = Record(**record_to_test(app.config["ELECTION_DATE"]))
            r.record['bag_nummeraanduiding_id'] = '0361200000200962'
            form = EditForm(MultiDict(r.record))
            gemeente = get_gemeente('GM0518')
            result = form.validate_using_gemeente(gemeente)
            self.assertEqual(result, False)

            error = form.errors['bag_nummeraanduiding_id'][0]
            assert 'Het ingevulde nummer (0361200000200962) is niet geldig voor deze gemeente' in error
