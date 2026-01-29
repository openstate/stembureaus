
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:wims_tests@mysql-tests:3306/stembureaus_tests?local_infile=True'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ECHO = False