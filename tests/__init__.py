from config import basedir
from sqlalchemy import text

def insert_db_test_records(db):
  # Note that we are currently not reading/executing tests/db/bag.sql here.
  # It somehow leads to a `SAVEPOINT sa_savepoint_1 does not exist` error,
  # which is somehow caused by the use of `test_isolation` in `BaseTestClass`.
  # The tests succeed because the `bag` table is also created via `models.py`.
  # with open(f"{basedir}/tests/db/bag.sql") as file:
  #     queries = file.read().split(";")
  #     for query in queries:
  #       db.session.execute(text(query))
  #     db.session.commit()
  with open(f"{basedir}/tests/db/test_bag.sql") as file:
      query = text(file.read())
      db.session.execute(query)
      db.session.commit()