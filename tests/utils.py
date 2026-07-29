import os

from app.models import Election, Gemeente_user, User, db, Gemeente
from app.utils import get_gemeente

from app.db_utils import db_exec_one_optional


def login_test_source_user(app, gemeente_code, user):
  client = app.test_client(user=user)
  with client.session_transaction() as session:
    session['selected_gemeente_code'] = gemeente_code

  return client

def add_election(gemeente):
  election = Election(
    verkiezing="gemeenteraadsverkiezingen 2026", gemeente=gemeente
  )
  db.session.add(election)

def add_gemeente(testcase, gemeente_code='GM0518', gemeente_naam="'s-Gravenhage"):
  gemeente = Gemeente(gemeente_naam=gemeente_naam, gemeente_code=gemeente_code)
  db.session.add(gemeente)
  add_election(gemeente)
  db.session.commit()

  testcase.assertIsNotNone(get_gemeente(gemeente_code))

  return gemeente


def add_test_user(testcase, gemeente, email):
  user = User(email=email)
  user.set_password(str(os.urandom(24)))
  db.session.add(user)
  db.session.commit()

  gemeente_user = Gemeente_user(gemeente_id=gemeente.id, user_id=user.id)
  db.session.add(gemeente_user)
  db.session.commit()

  testcase.assertIsNotNone(get_user(email))
  testcase.assertIsNotNone(get_gemeente_user(user, gemeente))

  return user


def add_user_to_gemeente(testcase, user, gemeente):
  gemeente_user = Gemeente_user(gemeente_id=gemeente.id, user_id=user.id)
  db.session.add(gemeente_user)
  db.session.commit()

  testcase.assertIsNotNone(get_gemeente_user(user, gemeente))


def get_user(email):
  user = db_exec_one_optional(User, email=email)
  return user


def get_gemeente_user(user, gemeente):
  gemeente_user = db_exec_one_optional(Gemeente_user, user_id=user.id, gemeente_id=gemeente.id)
  return gemeente_user
