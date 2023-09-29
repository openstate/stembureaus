from app import app, db
from app.models import ckan
from app.email import send_email
from app.parser import BaseParser, valid_headers
from app.validator import Validator
from app.routes import create_record
from app.utils import get_gemeente, publish_gemeente_records

from app.stembureaumanager import BaseAPIParser, APIManager
from urllib.parse import urljoin
from pprint import pprint

from dateutil import parser
import requests

from app import app


class TSAParser(BaseAPIParser):
    def convert_to_record(self, data):
        pprint(data)
        type_stemburo = data['Type stembureau']
        # Normaal should be regulier
        if type_stemburo.strip() == 'Normaal':
            type_stemburo = 'regulier'

        kenmerken = data['Locaties'][0].get('Kenmerken', {})

        record = {
            'nummer_stembureau': data['Nummer stembureau'],
            'naam_stembureau': data['Naam stembureau'],
            'type_stembureau': type_stemburo.lower(),
            'website_locatie': data['Locaties'][0]['Website locatie'],
            'bag_nummeraanduiding_id': data['Locaties'][0]['BAG Nummeraanduiding ID'],
            'extra_adresaanduiding': data['Locaties'][0]['Extra adresaanduiding'],
            'latitude': str(data['Locaties'][0]['Latitude']),
            'longitude': str(data['Locaties'][0]['Longitude']),
            # 'x': None,
            # 'y': None,
            'openingstijd': data['Locaties'][0]['Openingstijden'][0]['Openingstijd'],
            'sluitingstijd': data['Locaties'][0]['Openingstijden'][0]['Sluitingstijd'],
            'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': kenmerken.get('TOEGANKELIJK VOOR MINDERVALIDEN', ''),
            'toegankelijke_ov_halte': data['Locaties'][0].get('Toegankelijke ov-halte', ''),
            'akoestiek_geschikt_voor_slechthorenden': data['Locaties'][0].get('Akoestiek geschikt voor slechthorenden', ''),
            'auditieve_hulpmiddelen': data['Locaties'][0].get('Auditieve hulpmiddelen', ''),
            'visuele_hulpmiddelen': kenmerken.get('Leesloep', ''),
            'gehandicaptentoilet': kenmerken.get('Invalidentoilet aanwezig voor kiezers', ''),
            'extra_toegankelijkheidsinformatie': data['Locaties'][0].get('Extra toegankelijkheidsinformatie'),
            'tellocatie': data['Locaties'][0].get('Tellocatie', ''),
            'contactgegevens_gemeente': data['Contactgegevens gemeente'],
            'verkiezingswebsite_gemeente': data['Verkiezingswebsite gemeente']
        }

        # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field
        # to the record
        if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            record['Verkiezingen'] = data['Verkiezingen']

        return record

    def _get_records(self, data, headers):
        result = []
        for d in data:
            r = self.convert_to_record(d)
            result.append(r)
        return result

    def parse(self, data):
        headers = valid_headers
        records = self._get_records(data, headers)
        clean_records = self._clean_records(records)
        return clean_records


class TSAManager(APIManager):
    def _request(self, endpoint, params=None):
        url = urljoin(app.config['TSA_BASE_URL'], endpoint)
        print(url,params)
        return requests.get(url, params=params, headers={
            'x-api-key': app.config['TSA_API_KEY']
        }).json()

    # Overview of all the municipalities in the API and their 'gewijzigd'
    # timestamp
    def _request_overview(self):
        return self._request('index')

    # Retrieve the stembureaus of a municipality from the API
    def _request_municipality(self, municipality_id):
        #  [API_DOMAIN]/api/stembureau/gemeente?id=<GM_CODE>
        return self._request('gemeente/%s' % (municipality_id,))

    def run(self):
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

            # Skip this municipality if the API data wasn't changed since the
            # from_date (by default 2 hours before now); don't skip if a gm_code
            # is set as we then explicitly want to load that gemeente
            m_updated = m['gewijzigd']  # parser.parse(m['gewijzigd'])
            if m_updated <= self.from_date.isoformat() and not self.gm_code:
                continue

            gemeente = get_gemeente(m['gemeente_code'])
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

            # Special case for Amersfoort which has a 'fake' stembureau that
            # needs to be removed at our side
            if m['gemeente_code'] == 'GM0307':
                data = [s for s in data if s['Naam stembureau'] != 'Voorzitterspool extra werving']

            records = TSAParser().parse(data)
            validator = Validator()
            results = validator.validate(records)

            if not results['no_errors']:
                print("Errors were found in the results")
                self._send_error_email(gemeente, records, results)
                continue

            self._save_draft_records(gemeente, gemeente_draft_records, elections, results)
            self._publish_records(gemeente)

            gemeente.source = 'api[stembureaumanager]'
            db.session.commit()
