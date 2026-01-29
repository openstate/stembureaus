import os

from app.models import Gemeente_user, User, db, Gemeente, add_user, login_manager
from app.utils import get_gemeente

from app.db_utils import db_exec_one, db_exec_one_optional
from sqlalchemy import select
from flask_login import FlaskLoginClient


def login_test_source_user(app, gemeente_code, email):
  login_manager.session_protection = None
  app.testing = True
  app.config['WTF_CSRF_ENABLED'] = False
  app.test_client_class = FlaskLoginClient

  # Check if test user already exists
  with app.test_request_context('/'):
    user = db_exec_one_optional(User, email=email)
    if not user:
      gemeente = db_exec_one(select(Gemeente).filter_by(gemeente_code=gemeente_code))
      add_user(gemeente.id, email, send_invite_mail=False, send_logging_mail=False)
      user = db_exec_one_optional(User, email=email)

  client = app.test_client(user=user)
  with client.session_transaction() as session:
    session['selected_gemeente_code'] = gemeente_code

  return client

def add_gemeente(testcase, gemeente_code='GM0518', gemeente_naam="'s-Gravenhage"):
  gemeente = Gemeente(gemeente_naam=gemeente_naam, gemeente_code=gemeente_code)
  db.session.add(gemeente)
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
