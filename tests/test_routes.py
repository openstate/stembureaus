#!/usr/bin/env python

import uuid

from tests.base_test_class import BaseTestClass
from werkzeug.datastructures import MultiDict
from app.models import Record

from tests.record_to_test import record_to_test


class TestCreateRecord(BaseTestClass):
  AFFECTS_DB = True
  gemeente_code='GM0518'

  def setUp(self):
    super().setUp()
    from tests.utils import add_gemeente
    self.gemeente = add_gemeente(self, gemeente_code=self.gemeente_code)

  def test_emptying_address_fields_for_zerosbag(self):
    # When user fills in 0000000000000000 for BAG id, any pre-existing address fields should be emptied
    from app.routes import create_record
    from app.forms import EditForm
    from app.utils import get_gemeente

    with self.app.test_request_context('/'):
      r = Record(**record_to_test(self.app.config["ELECTION_DATE"]))
      r.record['bag_nummeraanduiding_id'] = '0000000000000000'
      form = EditForm(MultiDict(r.record))

      # Pre-conditions
      self.assertEqual(r.record['straatnaam'], 'Spui')

      stemlokaal_id = uuid.uuid4().hex
      gemeente = get_gemeente(self.gemeente_code)
      election = f'{self.app.config["ELECTION_TYPE"]} {self.app.config["ELECTION_DATE"][0:4]}'
      record = create_record(form, stemlokaal_id, gemeente, election)

      # Post-conditions
      self.assertEqual(record['Straatnaam'], '')

  def test_keeping_address_fields(self):
    # When user fills in a real BAG id, any pre-existing address fields should not be emptied
    from app.routes import create_record
    from app.forms import EditForm
    from app.utils import get_gemeente

    with self.app.test_request_context('/'):
      r = Record(**record_to_test(self.app.config["ELECTION_DATE"]))
      r.record['bag_nummeraanduiding_id'] = '0518200000747446'
      form = EditForm(MultiDict(r.record))

      # Pre-conditions
      self.assertEqual(r.record['straatnaam'], 'Spui')

      stemlokaal_id = uuid.uuid4().hex
      gemeente = get_gemeente(self.gemeente_code)
      election = f'{self.app.config["ELECTION_TYPE"]} {self.app.config["ELECTION_DATE"][0:4]}'
      record = create_record(form, stemlokaal_id, gemeente, election)

      # Post-conditions
      self.assertEqual(record['Straatnaam'], 'Spui')
