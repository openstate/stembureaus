import geoip2.database

class GeoLocator:
  CARIBBEAN_NETHERLANDS_ISO_CODE = 'BQ'
  BONAIRE_CUSTOM_CODE = 'BQ-Bonaire'
  SINT_EUSTATIUS_CUSTOM_CODE = 'BQ-Sint-Eustatius'
  SABA_CUSTOM_CODE = 'BQ-Saba'

  def __init__(self, config, logger):
    self.mapping = config['COUNTRY_CODE_TO_MAP']
    self.logger = logger
    try:
      self.country_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
      self.city_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-City.mmdb')
      self.logger.info("Successfully initialized GeoLocator reader")
    except Exception as e:
      self.logger.error(f"Error initializing GeoLocator reader: {str(e)}")
      self.country_reader = None
      self.city_reader = None


  def get_longitude_and_latitude(self, ip_address):
    country_code = self.get_country_code(ip_address)
    if not country_code:
      return self.mapping['NL']

    if country_code == self.CARIBBEAN_NETHERLANDS_ISO_CODE:
      country_code = self.get_island_code(ip_address)

    if country_code in self.mapping:
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

  # Try to determine which island. If that fails, return CARIBBEAN_NETHERLANDS_ISO_CODE to center map so that
  # all three islands are visible
  def get_island_code(self, ip_address):
    if not self.city_reader:
      return self.CARIBBEAN_NETHERLANDS_ISO_CODE

    try:
      response = self.city_reader.city(ip_address)
      longitude = response.location.longitude
      latitude = response.location.latitude

      if longitude > -68.49 and longitude < -68.10 and latitude > 11.94 and latitude < 12.38:
        return self.BONAIRE_CUSTOM_CODE
      elif longitude > -63.03 and longitude < -62.90 and latitude > 17.43 and latitude < 17.55:
        return self.SINT_EUSTATIUS_CUSTOM_CODE
      elif longitude > -63.28 and longitude < -63.18 and latitude > 17.58 and latitude < 17.67:
        return self.SABA_CUSTOM_CODE
      else:
        return self.CARIBBEAN_NETHERLANDS_ISO_CODE
    except Exception as e:
      self.logger.error(f"Error getting island geolocation for ip address {ip_address}, error: {str(e)}")
      return self.CARIBBEAN_NETHERLANDS_ISO_CODE
