import threading
import requests

from flask import url_for

class CachePurger:
  # Uses a background daemon to purge the nginx caches for
  #   - the home page /
  #   - the gemeente page
  #   - all stembureau pages for the gemeente
  # Note that when logged in, `Cache-Control` is set to `private` in `routes.py` meaning pages
  # you request that are not yet cached will not be cached.
  #
  # Development
  #   - When you are using the production environment on your development laptop, you are using
  #     a dedicated local hostname such as `dev.waarismijnstemlokaal.nl`. To test the purging of
  #     nginx caches, pass the IP address (stm network) of the nginx container via `extra_hosts`
  #     so that cache purging actually works. On the production server `waarismijnstemlokaal.nl`
  #     will be resolved without additional measures. See `docker-compose.yml.example`.


  def __init__(self, gemeente, gemeente_records, current_app):
    self.gemeente = gemeente
    self.gemeente_code = gemeente.gemeente_code
    self.gemeente_records = gemeente_records
    self.current_app = current_app


  def purge(self):
    self.current_app.logger.info(f"Purging nginx caches started for {self.gemeente_code}")

    try:
        uuids = map(lambda record: record['UUID'], self.gemeente_records)
        args = [self.current_app._get_current_object(), uuids]
        thread = threading.Thread(target=self.purge_target, args=args, daemon=True)
        thread.start()

        self.current_app.logger.info(f"Purging nginx caches sent to background for {self.gemeente_code}")
    except Exception as e:
        print(f"Exception occurred in CachePurger: {e}")
        self.current_app.logger.info(f"Exception occurred in CachePurger: {e}")


  def purge_target(self, app, uuids):
    app.logger.info(f"Purging nginx caches started in background for {self.gemeente_code}")

    try:
        with app.app_context():
            self.purge_for_url(app, url_for('index'))

            self.purge_for_url(app, url_for('show_gemeente', gemeente=self.gemeente.gemeente_naam))
            self.purge_for_url(app, url_for('embed_gemeente', gemeente=self.gemeente.gemeente_naam))

            for uuid in uuids:
              self.purge_for_url(app, url_for('show_stembureau', gemeente=self.gemeente.gemeente_naam, primary_key=uuid))
              self.purge_for_url(app, url_for('embed_stembureau', gemeente=self.gemeente.gemeente_naam, primary_key=uuid))

            app.logger.info(f"Successfully purged nginx caches for {self.gemeente_code}")
    except Exception as e:
        app.logger.info(f"Error purging nginx caches for {self.gemeente_code}: {e}")


  def purge_for_url(self, app, url):
      cache_purge_key = f"{app.config['CACHE_PURGE_KEY']}"
      return requests.get(url, headers={
          cache_purge_key: 'true'
      })
