import json
import os

from app.email import send_published_decreased

class PublishedMonitor:
  """
  Usage:
    published_monitor = PublishedMonitor()
    all_records = ckan.get_records(resource_id)
    published_monitor.process(all_records)

  Call this from cron e.g. each hour:
    `sudo docker exec stm-app-1 flask ckan monitor-published`
  Calling `process` will compare the municipalities that have published data
  to the list determined earlier. If a municipality disappears, which never should be the
  case, send an e-mail to the admins.

  During the very first run it cannot compare data to a previous run. It will simply save the data
  to `MONITOR_FILE` so that the next run can compare.
  """
  GEMEENTE = 'Gemeente'
  CBS_GEMEENTECODE = 'CBS gemeentecode'
  MONITOR_FILE = f'previously_published.json'

  def process(self, records):
    currently_published = self.get_currently_published(records)
    previously_published = self.get_previously_published()

    disappeared = {}
    if previously_published:
      disappeared = self.compare_current_to_previous(previously_published, currently_published)

    if len(disappeared) > 0:
      print("\nFor some municipalities all published data has disappeared")
      send_published_decreased(disappeared)
    else:
      print("\nNo problems detected")
      # Only in this case write the current list
      self.write_published(currently_published)

  def get_currently_published(self, records):
    h = {}
    for record in records:
      gemeente_code = record[self.CBS_GEMEENTECODE]

      if not gemeente_code in h:
        h[gemeente_code] = record[self.GEMEENTE]

    return h

  def get_previously_published(self):
    if not os.path.exists(self.MONITOR_FILE):
      return

    with open(self.MONITOR_FILE) as f:
      h = json.load(f)
      return h
    
  def write_published(self, published):
    with open(self.MONITOR_FILE, 'w') as f:
      json.dump(published, f, indent=4)

  def compare_current_to_previous(self, previously_published, currently_published):
    disappeared = {}

    for key in previously_published:
      if not key in currently_published:
        disappeared[key] = previously_published[key]
    
    return disappeared