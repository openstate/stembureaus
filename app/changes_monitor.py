from contextlib import suppress
from datetime import datetime
from app.email import send_changed_data
from app.models import Gemeente, Gemeente_user, User, db
from app.db_utils import db_exec_all
from sqlalchemy import select
import json
import os
import pytz

class ChangesMonitor:
  """
  Usage:
    changes_monitor = ChangesMonitor()
    all_records = ckan.get_records(resource_id)
    changes_monitor.process_changes(all_records)

  Call this from cron near the end of each working day to inform the users about changed data.
    `sudo docker exec stm-app-1 flask ckan monitor-changes`
  To see what e-mails would be sent you can use the `debug` flag (see below).
  
  Calling `process_changes` will compare the provided (current) data with the data from the last run.
  Any changes found will be written to the `CHANGES_DIR` directory in a timestamped filename.
  A summary of the changes will also be sent by e-mail to the users of the municipality:
    - For added and deleted stembureaus only the name and number are sent, not the full records.
    - For changed stembureaus only the changed fields are sent
    - The text will include the time interval the changes were detected

  During the very first run it cannot compare data to a previous run. It will simply save the data
  to `MONITOR_FILE` so that the next run can compare.
  It will also write the data once to `INITIAL_FILE`. The combination of `INITIAL_FILE` and the files
  under `CHANGES_DIR` provide a full history of the stembureau data. 

  If `debug=True` is passed to `ChangesMonitor()` no changes will be made. In particular:
    - No file with changes will be written, so the timestamp for the previous run is not influenced.
    - The `MONITOR_FILE` and `INITIAL_FILE` will not be overwritten
    - No e-mails will be sent
  Instead, the e-mails that would be sent are written to `stdout` for examination.
  """
  ADDED = 'added'
  DELETED = 'deleted'
  CHANGED = 'changed'
  NUMMER_STEMBUREAU = 'Nummer stembureau'
  NAAM_STEMBUREAU = 'Naam stembureau'
  CBS_GEMEENTECODE = 'CBS gemeentecode'
  DATA_DIR = 'monitor_changes'
  CHANGES_DIR = f'{DATA_DIR}/changes'
  MONITOR_FILE = f'{DATA_DIR}/previous_data.json'
  INITIAL_FILE = f'{DATA_DIR}/initial_data.json'

  def __init__(self, debug = False):
    self.debug = debug
    self.all_changes = {}
    self.old_records = {}
    self.new_records = {}
    self.timestamp_previous_run = self.get_timestamp_previous_run()

    self.gemeente_data = {}
    for gemeente in db_exec_all(Gemeente):
      self.gemeente_data[gemeente.gemeente_code] = gemeente

  def process_changes(self, new_records):
    self.new_records = self.clean_and_transform_records(new_records)

    self.collect_changes()
    # Always write file even when no changes occurred. This way the timestamp used in
    # e-mails sent remains accurate.
    self.write_changes()

    if len(self.all_changes) == 0:
      return
    self.send_mails()

    self.write_records(self.new_records)


  def collect_changes(self):
    self.old_records = self.get_old_records()
    if not self.old_records:
      self.write_records(self.new_records)
      self.write_initial_records()
      return

    # Check changes in existing records and deletions
    for gemeente_code in self.old_records:
      for nummer_stembureau in self.old_records[gemeente_code]:
        old_record = self.old_records[gemeente_code][nummer_stembureau]

        # Has been deleted?
        if not gemeente_code in self.new_records or not nummer_stembureau in self.new_records[gemeente_code]:
          self.append_deletion(gemeente_code, old_record)
          continue

        # Has been changed?
        changes = self.get_changes(old_record, self.new_records[gemeente_code][nummer_stembureau])
        if changes:
          self.append_changes(gemeente_code, old_record[self.NUMMER_STEMBUREAU], changes)


    # Check added records
    for gemeente_code in self.new_records:
      for nummer_stembureau in self.new_records[gemeente_code]:
        if not gemeente_code in self.old_records or not nummer_stembureau in self.old_records[gemeente_code]:
          self.append_addition(gemeente_code, self.new_records[gemeente_code][nummer_stembureau])


  def write_changes(self):
    if self.debug: return

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{self.CHANGES_DIR}/{timestamp}.json"

    to_write = {**self.get_metadata(), **self.all_changes}
    with open(filename, 'w') as f:
      json.dump(to_write, f, indent=4)


  def send_mails(self):
    for gemeente_code in self.all_changes:
      gemeente = self.gemeente_data[gemeente_code]
      if gemeente.source: # Do not send changes to gemeenten using an API
        continue

      users_query = select(User).join(Gemeente_user).join(Gemeente).where(Gemeente.gemeente_code == gemeente_code)
      users = db.session.execute(users_query).scalars()

      messages = []
      for user in users:
        msg = send_changed_data(gemeente, user, self.get_time_phrase(), self.changes_for_email(gemeente_code), self.debug)
        messages.append(msg)

      if self.debug:
        for message in messages:
          print(message)


  #
  # Internal methods
  #


  def get_timestamp_previous_run(self):
    files = sorted((f for f in os.listdir(self.CHANGES_DIR) if not f.startswith(".")), reverse=True)
    if not files:
      return

    t = list(map(int, files[0].replace('.json', '').split('-'))) # [year, month, seconds, hours, minutes, seconds]
    return datetime(*t, tzinfo=pytz.utc)


  def get_time_phrase(self):
    if not self.timestamp_previous_run:
      return "Recentelijk"

    time_format = "%d %B %H:%M"
    tz = pytz.timezone('Europe/Amsterdam')
    previous_time = self.timestamp_previous_run.astimezone(tz).strftime(time_format)
    current_time = datetime.now(tz=tz).strftime(time_format)
    return f"Tussen {previous_time} en {current_time}"


  def get_old_records(self):
    if not os.path.exists(self.MONITOR_FILE):
      return
    with open(self.MONITOR_FILE) as f:
      records = json.load(f)
      return records

    return None


  def write_records(self, records):
    if self.debug: return

    with open(self.MONITOR_FILE, 'w') as f:
      json.dump(records, f, indent=4)


  def write_initial_records(self):
    if self.debug: return

    with open(self.INITIAL_FILE, 'w') as f:
      json.dump(self.new_records, f, indent=4)


  def clean_and_transform_records(self, records):
    h = {}
    for record in records:
      gemeente_code = record[self.CBS_GEMEENTECODE]
      nummer_stembureau = str(record[self.NUMMER_STEMBUREAU])

      with suppress(KeyError): del record['_id']
      with suppress(KeyError): del record['ID']
      with suppress(KeyError): del record['UUID']

      if not gemeente_code in h: h[gemeente_code] = {}
      h[gemeente_code][nummer_stembureau] = record

    return h


  def get_changes(self, old_record, new_record):
    changes = {}
    for key in old_record:
      if old_record[key] != new_record[key]:
        changes[key] = [old_record[key], new_record[key]]

    return changes


  def init_changes(self, gemeente_code):
    if not gemeente_code in self.all_changes:
      self.all_changes[gemeente_code] = {
        self.DELETED: [],
        self.ADDED: [],
        self.CHANGED: {}
      }


  def append_deletion(self, gemeente_code, record):
    self.init_changes(gemeente_code)
    self.all_changes[gemeente_code][self.DELETED].append(record)


  def append_addition(self, gemeente_code, record):
    self.init_changes(gemeente_code)
    self.all_changes[gemeente_code][self.ADDED].append(record)


  def append_changes(self, gemeente_code, stembureau_nummer, changes):
    self.init_changes(gemeente_code)
    self.all_changes[gemeente_code][self.CHANGED][stembureau_nummer] = changes


  def get_metadata(self):
    non_api_sources = {k: v for k,v in self.all_changes.items() if not self.gemeente_data[k].source}
    metadata = {'metadata': {
      'Aantal non-api gemeenten waarvoor stembureaus zijn toegevoegd':
        len([k for k, v in non_api_sources.items() if len(v[self.ADDED]) > 0]),
      'Aantal non-api gemeenten waarvoor stembureaus zijn verwijderd':
        len([k for k, v in non_api_sources.items() if len(v[self.DELETED]) > 0]),
      'Aantal non-api gemeenten waarvoor stembureaus zijn gewijzigd':
        len([k for k, v in non_api_sources.items() if len(v[self.CHANGED]) > 0]),
      'Totaal aantal stembureaus toegevoegd (non-api)':
        sum([len(v[self.ADDED]) for v in non_api_sources.values()]),
      'Totaal aantal stembureaus verwijderd (non-api)':
        sum([len(v[self.DELETED]) for v in non_api_sources.values()]),
      'Totaal aantal stembureaus gewijzigd (non-api)':
        sum([len(v[self.CHANGED]) for v in non_api_sources.values()]),
    }}

    return metadata


  def changes_for_email(self, gemeente_code):
    h = []

    added = self.all_changes[gemeente_code][self.ADDED]
    if len(added) > 0:
      h.append("Stembureaus toegevoegd:")
      for s in added:
        h.append(f"{self.indent_level1()}{s[self.NAAM_STEMBUREAU]} (nummer {s[self.NUMMER_STEMBUREAU]})")

    deleted = self.all_changes[gemeente_code][self.DELETED]
    if len(deleted) > 0:
      h.append("Stembureaus verwijderd:")
      for s in deleted:
        h.append(f"{self.indent_level1()}{s[self.NAAM_STEMBUREAU]} (nummer {s[self.NUMMER_STEMBUREAU]})")

    changed = self.all_changes[gemeente_code][self.CHANGED]
    if len(changed) > 0:
      h.append("Stembureaus aangepast:")
      for stembureau_nummer in changed:
        h.append(f"{self.indent_level1()}Nummer stembureau: {stembureau_nummer}")
        for field in changed[stembureau_nummer]:
          h.append(f"{self.indent_level2()}Veld: {field}")
          h.append(f"{self.indent_level3()}Oude waarde: {changed[stembureau_nummer][field][0]}")
          h.append(f"{self.indent_level3()}Nieuwe waarde: {changed[stembureau_nummer][field][1]}")

    return h


  def indent_level1(self):
    return self.space(6)


  def indent_level2(self):
    return self.space(12)


  def indent_level3(self):
    return self.space(18)


  def space(self, number):
    return " &nbsp;" * number