from app.db_utils import db_exec_one, db_exec_one_optional
from app.models import Gemeente, User, add_user, login_manager
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