from flask import current_app

from app import ckan
from app.models import db
from app.email import send_email
from app.parser import valid_headers
from app.validator import Validator
from app.utils import get_gemeente

from app.stembureaumanager import BaseAPIParser, APIManager
from urllib.parse import urljoin

from dateutil import parser
import copy
import requests

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
        if [x for x in current_app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
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
            record['gehandicaptentoilet'] = locatie.get('Gehandicaptentoilet', '')
            record['host'] = locatie.get('Host', '')
            record['geleidelijnen'] = locatie.get('Geleidelijnen', '')
            record['stemmal_met_audio_ondersteuning'] = locatie.get('Stemmal met audio-ondersteuning', '')
            record['kandidatenlijst_in_braille'] = locatie.get('Kandidatenlijst in braille', '')
            record['kandidatenlijst_met_grote_letters'] = locatie.get('Kandidatenlijst met grote letters', '')
            record['gebarentolk_ngt'] = locatie.get('Gebarentolk (NGT)', '')
            record['gebarentalig_stembureaulid_ngt'] = locatie.get('Gebarentalig stembureaulid (NGT)', '')
            record['akoestiek_geschikt_voor_slechthorenden'] = locatie.get('Akoestiek geschikt voor slechthorenden', '')
            record['prikkelarm'] = locatie.get('Prikkelarm', '')
            record['extra_toegankelijkheidsinformatie'] = locatie.get('Extra toegankelijkheidsinformatie', '')
            record['overige_informatie'] = ', '.join(kenmerken_tekst)
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

                records.append(copy.deepcopy(record))

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
    SOURCE_STRING = 'api[TSA Verkiezingen]'

    def _request(self, endpoint, params=None):
        url = urljoin(current_app.config['TSA_BASE_URL'], endpoint)
        return requests.get(url, params=params, headers={
            'x-api-key': current_app.config['TSA_API_KEY']
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

        municipalities = self._request_overview()
        if 'statusCode' in municipalities:
            send_email(
                "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van TSA API overzicht",
                sender=current_app.config['FROM'],
                recipients=current_app.config['ADMINS'],
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
            m_updated = parser.parse(m['gewijzigd'], ignoretz=True)
            if self._skip_based_on_date(m_updated, gemeente):
                continue

            elections = gemeente.elections
            # Pick the first election. In the case of multiple elections we only
            # retrieve the stembureaus of the first election as the records for
            # both elections are the same (at least for the GR2018 + referendum
            # elections on March 21st 2018).
            verkiezing = elections[0].verkiezing
            gemeente_draft_records = ckan.filter_draft_records(verkiezing, m['gemeente_code'])
            data = self._request_municipality(m['gemeente_code'])
            # Make sure that we retrieve a list and that it is not empty
            if not isinstance(data, list) or not data:
            #if data.get('statusCode', 200) >= 400:
                send_email(
                    "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van TSA API gemeente data %s" % (gemeente.gemeente_naam),
                    sender=current_app.config['FROM'],
                    recipients=current_app.config['ADMINS'],
                    text_body="Fout bij het ophalen van TSA API gemeente data %s" % (gemeente.gemeente_naam),
                    html_body=None
                )
                continue

            records = TSAParser().parse(data)
            records = self._bugfix(gemeente, records)
            validator = Validator()
            results = validator.validate(records)

            if not results['no_errors']:
                print("Errors were found in the results")
                self._send_error_email(gemeente, records, results, self.SOURCE_STRING)
                continue

            self._save_draft_records(gemeente, gemeente_draft_records, elections, results)
            self._publish_records(gemeente)

            gemeente.source = self.SOURCE_STRING
            gemeente.api_laatste_wijziging = m_updated
            db.session.commit()

    # To fix some (hopefully temporary) errors for some stembureaus
    def _bugfix(self, gemeente, records):
        if gemeente.gemeente_code == 'GM0150': # Deventer
            for record in records:
                if record['nummer_stembureau'] == 113:
                    self._fix_latlon(record, "52.26087196869886", "6.153974536599161")

        if gemeente.gemeente_code == 'GM0779': # Geertruidenberg
            for record in records:
                if record['nummer_stembureau'] == 6:
                    self._fix_latlon(record, "51.68887590155298", "4.872133492118168")
                if record['nummer_stembureau'] == 4:
                    self._fix_latlon(record, "51.703441296183556", "4.871675635316138")

        return records

    def _fix_latlon(self, record, latitude, longitude):
        if not record['latitude'] or record['latitude'] == 'None':
            record['latitude'] = latitude
        if not record['longitude'] or record['longitude'] == 'None':
            record['longitude'] = longitude
