from app import create_app

app = create_app()

with app.app_context():
  from .parser import TestBaseParser, TestExcelParser
  from .validator import TestValidator, TestRecordValidator
  from .forms import TestEditForm
