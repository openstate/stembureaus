from config import basedir
from sqlalchemy import text

def insert_db_test_records(db):
  with open(f"{basedir}/tests/db/bag.sql") as file:
      queries = file.read().split(";")
      for query in queries:
        db.session.execute(text(query))
  with open(f"{basedir}/tests/db/test_bag.sql") as file:
      query = text(file.read())
      db.session.execute(query)
  db.session.commit()

