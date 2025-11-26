from app import create_app

app = create_app()

with app.app_context():
  from .test_parser import TestBaseParser, TestExcelParser
  from .test_validator import TestValidator, TestRecordValidator
  from .test_forms import TestEditForm
