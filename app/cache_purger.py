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


  def __init__(self, current_app, join_thread = False):
    self.current_app = current_app
    self.join_thread = join_thread


  def purge(self, gemeente, gemeente_records):
    self.current_app.logger.info(f"Purging nginx caches started for {gemeente.gemeente_code}")

    try:
        uuids = map(lambda record: record['UUID'], gemeente_records)
        args = [self.current_app._get_current_object(), gemeente, uuids]
        thread = threading.Thread(target=self.purge_target, args=args, daemon=True)
        thread.start()

        self.current_app.logger.info(f"Purging nginx caches sent to background for {gemeente.gemeente_code}")

        if self.join_thread:
          thread.join()
          self.current_app.logger.info(f"Purging nginx caches finished after joining thread for {gemeente.gemeente_code}")

    except Exception as e:
        print(f"Exception occurred in CachePurger: {e}")
        self.current_app.logger.info(f"Exception occurred in CachePurger: {e}")


  def purge_target(self, app, gemeente, uuids):
    app.logger.info(f"Purging nginx caches started in background for {gemeente.gemeente_code}")

    try:
        with app.app_context():
            self.purge_for_url(app, url_for('index'))

            self.purge_for_url(app, url_for('show_gemeente', gemeente=gemeente.gemeente_naam))
            self.purge_for_url(app, url_for('embed_gemeente', gemeente=gemeente.gemeente_naam))

            for uuid in uuids:
              self.purge_for_url(app, url_for('show_stembureau', gemeente=gemeente.gemeente_naam, primary_key=uuid))
              self.purge_for_url(app, url_for('embed_stembureau', gemeente=gemeente.gemeente_naam, primary_key=uuid))

            self.purge_for_url(app, url_for('embed_alles'))

            app.logger.info(f"Successfully purged nginx caches for {gemeente.gemeente_code}")
    except Exception as e:
        app.logger.info(f"Error purging nginx caches for {gemeente.gemeente_code}: {e}")


  def purge_for_url(self, app, url):
      cache_purge_key = f"{app.config['CACHE_PURGE_KEY']}"
      return requests.get(url, headers={
          cache_purge_key: 'true'
      })
