import unittest

from test_config import TestConfig

class BaseTestClass(unittest.TestCase):
    AFFECTS_DB = False

    def setUp(self):
        from app.models import db, create_all, drop_all
        from app import create_app
        self.app = create_app(TestConfig)
        self.appctx = self.app.app_context()
        self.appctx.push()

        if self.AFFECTS_DB:
            drop_all(self.app)
            create_all()
            from tests import insert_db_test_records
            insert_db_test_records(db)

    def tearDown(self):
        self.appctx.pop()
        self.app = None
        self.appctx = None

