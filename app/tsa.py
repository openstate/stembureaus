from app import app, db
from app.models import ckan
from app.email import send_email
from app.parser import BaseParser, valid_headers
from app.validator import Validator
from app.routes import create_record
from app.utils import get_gemeente, publish_gemeente_records

from app.stembureaumanager import BaseAPIParser, APIManager
from urllib.parse import urljoin

from dateutil import parser
import requests

from app import app


class TSAParser(BaseAPIParser):
    def convert_to_record(self, data):
        type_stembureau = data['Type stembureau']
        if type_stembureau.strip() == 'Normaal':
            type_stembureau = 'regulier'

        # TSA allows for custom fields called 'kenmerken'
        kenmerken = data['Locaties'][0].get('Kenmerken', {})
        kenmerken_tekst = []
        if kenmerken:
            for k, v in kenmerken.items():
                kenmerken_tekst.append('%s: %s' % (k, v))

        records = []

        record = {
            'nummer_stembureau': data['Nummer stembureau'],
            'naam_stembureau': data['Naam stembureau'],
            'type_stembureau': type_stembureau.lower(),
            'contactgegevens_gemeente': data['Contactgegevens gemeente'],
            'verkiezingswebsite_gemeente': data['Verkiezingswebsite gemeente']
        }

        # If there are 'waterschapsverkiezingen', add the 'verkiezingen' field
        # to the record
        if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            record['verkiezingen'] = data['Verkiezingen']

        for locatie in data['Locaties']:
            record['website_locatie'] = locatie['Website locatie']
            record['bag_nummeraanduiding_id'] = locatie['BAG Nummeraanduiding ID']
            record['extra_adresaanduiding'] = locatie['Extra adresaanduiding']
            record['latitude'] = str(locatie['Latitude'])
            record['longitude'] = str(locatie['Longitude'])
            # 'x' = None
            # 'y' = None
            record['toegankelijk_voor_mensen_met_een_lichamelijke_beperking'] = locatie[
                'Toegankelijk voor mensen met een lichamelijke beperking']
            record['toegankelijke_ov_halte'] = locatie.get('Toegankelijke ov-halte', '')
            record['akoestiek_geschikt_voor_slechthorenden'] = locatie.get('Akoestiek geschikt voor slechthorenden', '')
            record['auditieve_hulpmiddelen'] = locatie.get('Auditieve hulpmiddelen', '')
            record['visuele_hulpmiddelen'] = locatie.get('Visuele hulpmiddelen', '')
            record['gehandicaptentoilet'] = locatie.get('Gehandicaptentoilet', '')
            record['extra_toegankelijkheidsinformatie'] = ', '.join(kenmerken_tekst)
            record['tellocatie'] = locatie.get('Tellocatie', '')

            if record['extra_adresaanduiding'] is None:
                record['extra_adresaanduiding'] = ''

            if record['bag_nummeraanduiding_id'] is None:
                record['bag_nummeraanduiding_id'] = '0000000000000000'

            if record['bag_nummeraanduiding_id'] == '0000000000000000' and not record['extra_adresaanduiding']:
                record['extra_adresaanduiding'] = 'Adres niet bekend'
            for periode in locatie['Openingstijden']:
                record['openingstijd'] = periode['Openingstijd']
                record['sluitingstijd'] = periode['Sluitingstijd']

                records.append(record)

        return records

    def _get_records(self, data, headers):
        result = []
        for d in data:
            result += self.convert_to_record(d)
        return result

    def parse(self, data):
        headers = valid_headers
        records = self._get_records(data, headers)
        clean_records = self._clean_records(records)
        return clean_records


class TSAManager(APIManager):
    def _request(self, endpoint, params=None):
        url = urljoin(app.config['TSA_BASE_URL'], endpoint)
        return requests.get(url, params=params, headers={
            'x-api-key': app.config['TSA_API_KEY']
        }).json()

    # Overview of all the municipalities in the API and their 'gewijzigd'
    # timestamp
    def _request_overview(self):
        return self._request('index')

    # Retrieve the stembureaus of a municipality from the API
    def _request_municipality(self, municipality_id):
        #  [API_DOMAIN]/api/gemeente/<GM_CODE>
        return self._request('gemeente/%s' % (municipality_id,))

    def run(self):
        SOURCE_STRING = 'api[TSA Verkiezingen]'

        municipalities = self._request_overview()
        if 'statusCode' in municipalities:
            send_email(
                "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van TSA API overzicht",
                sender=app.config['FROM'],
                recipients=app.config['ADMINS'],
                text_body=municipalities,
                html_body=None
            )
            return
        for m in municipalities:
            # If the gm_code parameter is set then only process that specific
            # gemeente
            if self.gm_code:
                if m['gemeente_code'] != self.gm_code:
                    continue

            gemeente = get_gemeente(m['gemeente_code'])

            # Skip this municipality if the API data wasn't changed since the
            # from_date (by default 2 hours before now); don't skip if a gm_code
            # is set as we then explicitly want to load that gemeente
            m_updated = m['gewijzigd']
            if (m_updated <= self.from_date.isoformat() and not self.gm_code) and gemeente.source == SOURCE_STRING:
                continue

            elections = gemeente.elections.all()
            # Pick the first election. In the case of multiple elections we only
            # retrieve the stembureaus of the first election as the records for
            # both elections are the same (at least for the GR2018 + referendum
            # elections on March 21st 2018).
            verkiezing = elections[0].verkiezing
            gemeente_draft_records, gemeente_publish_records = self._get_draft_and_publish_records_for_gemeente(
                verkiezing, m['gemeente_code'])
            data = self._request_municipality(m['gemeente_code'])
            if not isinstance(data, list):
            #if data.get('statusCode', 200) >= 400:
                send_email(
                    "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van TSA API gemeente data %s" % (gemeente.gemeente_naam),
                    sender=app.config['FROM'],
                    recipients=app.config['ADMINS'],
                    text_body="Fout bij het ophalen van TSA API gemeente data %s" % (gemeente.gemeente_naam),
                    html_body=None
                )
                continue

            records = TSAParser().parse(data)
            validator = Validator()
            results = validator.validate(records)

            if not results['no_errors']:
                print("Errors were found in the results")
                self._send_error_email(gemeente, records, results, SOURCE_STRING)
                continue

            self._save_draft_records(gemeente, gemeente_draft_records, elections, results)
            self._publish_records(gemeente)

            gemeente.source = SOURCE_STRING
            db.session.commit()
