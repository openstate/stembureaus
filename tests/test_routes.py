#!/usr/bin/env python

import uuid

from tests.utils import login_test_source_user
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

class TestSubmitEditForm(unittest.TestCase):
  def setUp(self):
    self.client = login_test_source_user(app, 'GM0518', 'test_user_den_haag@openstate.eu')
    with app.test_request_context('/'):
      self.record = Record(**record_to_test(app.config["ELECTION_DATE"])).record

  def test_bag_same_municipality(self):
    result = self.client.post('/gemeente-stemlokalen-edit', data=self.record)
    assert result.status_code == 302
    with self.client.session_transaction() as session:
      assert session['_flashes'] == [('message', 'Stembureau opgeslagen')]

  def test_bag_different_municipality(self):
    # Record is for Den Haag, BAG is from Alkmaar
    self.record['bag_nummeraanduiding_id'] = '0361200000200962'

    result = self.client.post('/gemeente-stemlokalen-edit', data=self.record)
    assert result.status_code == 200
    with self.client.session_transaction() as session:
      assert '_flashes' not in session
    assert 'Het ingevulde nummer (0361200000200962) is niet geldig voor deze gemeente.' in result.text
