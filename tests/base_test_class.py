import contextlib
import unittest

from test_config import TestConfig

class BaseTestClass(unittest.TestCase):
    AFFECTS_DB = False

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

        if self.AFFECTS_DB:
            self.transaction = self.start_transaction()
            self.enterContext(self.transaction)

            from app.models import db
            from tests import insert_db_test_records
            insert_db_test_records(db)

    def tearDown(self):
        self.appctx.pop()
        self.app = None
        self.appctx = None
