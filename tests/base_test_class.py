import contextlib
import unittest
from flask_login import FlaskLoginClient

from test_config import TestConfig

class BaseTestClass(unittest.TestCase):
    # If a test requires database transactions we want them to run within an outer transaction
    # so that the changes can be rolled back. This is accomplished in `db.test_isolation`.
    # In `setUp` all testcases will start an outer transaction,
    # then some standard db test records are inserted and then the test will run which
    # can insert more records as desired. The context exits in teardown which will rollback
    # the outer transaction.

    @contextlib.contextmanager
    def start_transaction(self):
        from app.models import db
        try:
            with db.test_isolation():
                yield
        finally:
            pass

    def setUp(self):
        from app import create_app
        self.app = create_app(TestConfig)
        self.appctx = self.app.app_context()
        self.appctx.push()

        self.transaction = self.start_transaction()
        self.enterContext(self.transaction)

        from app.models import db, login_manager
        from tests import insert_db_test_records
        insert_db_test_records(db)

        login_manager.session_protection = None
        self.app.test_client_class = FlaskLoginClient

    def tearDown(self):
        self.appctx.pop()
        self.app = None
        self.appctx = None
