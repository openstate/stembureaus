import geoip2.database

class GeoLocator:

  def __init__(self, config, logger):
    self.mapping = config['COUNTRY_CODE_TO_MAP']
    self.logger = logger
    try:
      self.country_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
      self.logger.info("Successfully initialized GeoLocator reader")
    except Exception as e:
      self.logger.error(f"Error initializing GeoLocator reader: {str(e)}")
      self.country_reader = None


  def get_longitude_and_latitude(self, ip_address):
    country_code = self.get_country_code(ip_address)

    if country_code and country_code in self.mapping:
      return self.mapping[country_code]
    else:
      return self.mapping['NL']


  def get_country_code(self, ip_address):
    if not self.country_reader:
      return

    try:
      response = self.country_reader.country(ip_address)
      return response.country.iso_code
    except Exception as e:
      self.logger.error(f"Error getting geolocation for ip address {ip_address}, error: {str(e)}")
      return 'error'
