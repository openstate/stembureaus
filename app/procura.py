from flask import current_app

from app import db
from app.email import send_email
from app.parser import valid_headers
from app.validator import Validator
from app.utils import get_gemeente

from app.stembureaumanager import BaseAPIParser, APIManager
from urllib.parse import urljoin

import copy
import requests


class ProcuraParser(BaseAPIParser):
    def convert_to_record(self, data):
        records = []

        record = {
            'nummer_stembureau': data['Nummer stembureau'],
            'naam_stembureau': data['Naam stembureau'],
            'type_stembureau': data['Type stembureau'],
            'contactgegevens_gemeente': data.get('Contactgegevens gemeente', ''),
            'verkiezingswebsite_gemeente': data.get('Verkiezingswebsite gemeente', '')
        }

        # If there are 'waterschapsverkiezingen', add the 'verkiezingen' field
        # to the record
        if [x for x in current_app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            record['verkiezingen'] = data['Verkiezingen']

        for locatie in data['Locaties']:
            record['website_locatie'] = locatie.get('Website locatie', '')
            record['bag_nummeraanduiding_id'] = locatie.get('BAG Nummeraanduiding ID', '')
            record['extra_adresaanduiding'] = locatie.get('Extra adresaanduiding', '')
            record['latitude'] = str(locatie.get('Latitude', ''))
            record['longitude'] = str(locatie.get('Longitude', ''))
            # 'x' = None
            # 'y' = None
            record['toegankelijk_voor_mensen_met_een_lichamelijke_beperking'] = locatie[
                'Toegankelijk voor mensen met een lichamelijke beperking']
            record['toegankelijke_ov_halte'] = locatie.get('Toegankelijke ov-halte', '')
            record['gehandicaptentoilet'] = locatie.get('Gehandicaptentoilet', '')
            record['host'] = locatie.get('Host', '')
            record['geleidelijnen'] = locatie.get('Geleidelijnen', '')
            record['stemmal_met_audio_ondersteuning'] = locatie.get('Stemmal met audio-ondersteuning', '').lower()
            record['kandidatenlijst_in_braille'] = locatie.get('Kandidatenlijst in braille', '')
            record['kandidatenlijst_met_grote_letters'] = locatie.get('Kandidatenlijst met grote letters', '')
            record['gebarentolk_ngt'] = locatie.get('Gebarentolk (NGT)', '')
            record['gebarentalig_stembureaulid_ngt'] = locatie.get('Gebarentalig stembureaulid (NGT)', '')
            record['akoestiek_geschikt_voor_slechthorenden'] = locatie.get('Akoestiek geschikt voor slechthorenden', '')
            record['prikkelarm'] = locatie.get('Prikkelarm', '')
            record['extra_toegankelijkheidsinformatie'] = locatie.get('Extra toegankelijkheidsinformatie', '')
            record['tellocatie'] = locatie.get('Tellocatie', '')

            if record['extra_adresaanduiding'] is None:
                record['extra_adresaanduiding'] = ''

            if record['bag_nummeraanduiding_id'] is None:
                record['bag_nummeraanduiding_id'] = '0000000000000000'

            #if record['bag_nummeraanduiding_id'] == '0000000000000000' and not record['extra_adresaanduiding']:
            #    record['extra_adresaanduiding'] = 'Adres niet bekend'

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


class ProcuraManager(APIManager):
    def _request(self, endpoint, params=None):
        url = urljoin(current_app.config['PROCURA_BASE_URL'], endpoint)
        return requests.get(url, params=params, headers={
            'x-api-key': current_app.config['PROCURA_API_KEY']
        }).json()

    # Overview of all the municipalities in the API and their 'gewijzigd'
    # timestamp
    def _request_overview(self):
        return self._request('overzicht')

    # Retrieve the stembureaus of a municipality from the API
    def _request_municipality(self, municipality_id):
        #  [API_DOMAIN]/wims/api/v1/gemeente?gemeente_code=<4_DIGIT_GM_CODE_>
        return self._request('gemeente?gemeente_code=%s' % (municipality_id[2:],))

    def run(self):
        SOURCE_STRING = 'api[Procura Verkiezingen]'

        municipalities = self._request_overview()
        if 'statusCode' in municipalities:
            send_email(
                "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van Procura API overzicht",
                sender=current_app.config['FROM'],
                recipients=current_app.config['ADMINS'],
                text_body=municipalities,
                html_body=None
            )
            return
        for m in municipalities:
            gemeente_code = 'GM' + m['gemeente_code']
            # If the gm_code parameter is set then only process that specific
            # gemeente
            if self.gm_code:
                if gemeente_code != self.gm_code:
                    continue

            gemeente = get_gemeente(gemeente_code)

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
                verkiezing, gemeente_code)
            data = self._request_municipality(gemeente_code)
            # Make sure that we retrieve a list and that it is not empty
            if not isinstance(data, list) or not data:
            #if data.get('statusCode', 200) >= 400:
                send_email(
                    "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van Procura API gemeente data %s" % (gemeente.gemeente_naam),
                    sender=current_app.config['FROM'],
                    recipients=current_app.config['ADMINS'],
                    text_body="Fout bij het ophalen van Procura API gemeente data %s" % (gemeente.gemeente_naam),
                    html_body=None
                )
                continue

            records = ProcuraParser().parse(data)
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
