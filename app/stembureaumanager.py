from flask import current_app
from datetime import datetime

from app import db, ckan
from app.email import send_email
from app.parser import BaseParser, valid_headers
from app.validator import Validator
from app.routes import create_record
from app.utils import get_gemeente, publish_gemeente_records

from urllib.parse import urljoin

from dateutil import parser
import copy
import requests

class BaseAPIParser(BaseParser):
    pass


class StembureauManagerParser(BaseAPIParser):
    def convert_to_record(self, data):
        records = []

        record = {
            'nummer_stembureau': data['Nummer stembureau'],
            'naam_stembureau': data.get('Naam stembureau', ''),
            'type_stembureau': data['Type stembureau'],
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
            record['toegankelijke_ov_halte'] = locatie['Toegankelijke ov-halte']
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
            record['extra_toegankelijkheidsinformatie'] = locatie['Extra toegankelijkheidsinformatie']
            record['overige_informatie'] = locatie.get('Overige informatie', '')
            record['tellocatie'] = locatie['Tellocatie']

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


class APIManager(object):
    SOURCE_STRING = None

    def __init__(self, from_date: datetime, gm_code: str):
        self.from_date = from_date
        self.gm_code = gm_code

    def _get_draft_and_publish_records_for_gemeente(self, verkiezing, gemeente_code):
        """
        Gets draft and published records for the specified municipality
        """
        all_publish_records = ckan.get_records(
            ckan.elections[verkiezing]['publish_resource']
        )
        all_draft_records = ckan.get_records(
            ckan.elections[verkiezing]['draft_resource']
        )

        gemeente_publish_records = [
            record for record in all_publish_records['records']
            if record['CBS gemeentecode'] == gemeente_code
        ]
        gemeente_draft_records = [
            record for record in all_draft_records['records']
            if record['CBS gemeentecode'] == gemeente_code
        ]
        return gemeente_draft_records, gemeente_publish_records

    def _save_draft_records(self, gemeente, gemeente_draft_records, elections, results):
        # Delete all stembureaus of current gemeente
        if gemeente_draft_records:
            for election in [x.verkiezing for x in elections]:
                ckan.delete_records(
                    ckan.elections[election]['draft_resource'],
                    {
                        'CBS gemeentecode': gemeente.gemeente_code
                    }
                )

        # Create and save records
        for election in [x.verkiezing for x in elections]:
            records = []
            for _, result in results['results'].items():
                if result['form']:
                    records.append(
                        create_record(
                            result['form'],
                            result['uuid'],
                            gemeente,
                            election
                        )
                    )
            ckan.save_records(
                ckan.elections[election]['draft_resource'],
                records=records
            )

    def _publish_records(self, gemeente):
        publish_gemeente_records(gemeente.gemeente_code)

    def _send_error_email(self, gemeente, records, results, current_api):
        output = 'Er zijn fouten aangetroffen in de resultaten voor de gemeente %s (%s) via %s:\n\n' % (
            gemeente.gemeente_naam, gemeente.gemeente_code, current_api)
        for idx, details in results['results'].items():
            if len(details['errors'].keys()) > 0:
                # the spreadsheet starts at row 5 ...
                real_idx = idx - 6
                s = records[real_idx]
                output += 'Stembureau #%s %s:\n' % (s['nummer_stembureau'], s['naam_stembureau'])
                for fld, fld_errors in details['errors'].items():
                    output += '%s: %s\n' % (fld, fld_errors[0],)
                output += '\n\n'
        print(output)
        send_email(
            "[WaarIsMijnStemlokaal.nl] Fouten bij het inladen van %s via %s" % (
                gemeente.gemeente_naam, current_api
            ),
            sender=current_app.config['FROM'],
            recipients=current_app.config['ADMINS'],
            text_body=output,
            html_body=None
        )

    def _skip_based_on_date(self, m_updated, gemeente):
        # Skip this municipality if the API data wasn't changed since the
        # from_date (by default 2 hours before now) and since the last-changed-date in the API;
        # don't skip if a gm_code is set as we then explicitly want to load that gemeente
        if gemeente.source != self.SOURCE_STRING or self.gm_code or not gemeente.api_laatste_wijziging:
            return False

        if m_updated <= gemeente.api_laatste_wijziging:
            return True
        if (m_updated <= self.from_date):
            return True

class StembureauManager(APIManager):
    SOURCE_STRING = 'api[stembureaumanager]'

    def _request(self, endpoint, params=None):
        url = urljoin(current_app.config['STEMBUREAUMANAGER_BASE_URL'], endpoint)
        return requests.get(url, params=params, headers={
            'x-api-key': current_app.config['STEMBUREAUMANAGER_API_KEY']
        }).json()

    # Overview of all the municipalities in the API and their 'gewijzigd'
    # timestamp
    def _request_overview(self):
        return self._request('overzicht')

    # Retrieve the stembureaus of a municipality from the API
    def _request_municipality(self, municipality_id):
        # [API_DOMAIN]/api/stembureau/gemeente?id=<GM_CODE>
        return self._request('gemeente', params={'id': municipality_id})

    def run(self):
        municipalities = self._request_overview()
        if 'statusCode' in municipalities:
            send_email(
                "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van SBM API overzicht",
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


            elections = gemeente.elections.all()
            # Pick the first election. In the case of multiple elections we only
            # retrieve the stembureaus of the first election as the records for
            # both elections are the same (at least for the GR2018 + referendum
            # elections on March 21st 2018).
            verkiezing = elections[0].verkiezing
            gemeente_draft_records, gemeente_publish_records = self._get_draft_and_publish_records_for_gemeente(
                verkiezing, m['gemeente_code'])
            data = self._request_municipality(m['gemeente_code'])
            # Make sure that we retrieve a list and that it is not empty
            if not isinstance(data, list) or not data:
            #if data.get('statusCode', 200) >= 400:
                send_email(
                    "[WaarIsMijnStemlokaal.nl] Fout bij het ophalen van SBM API gemeente data %s" % (gemeente.gemeente_naam),
                    sender=current_app.config['FROM'],
                    recipients=current_app.config['ADMINS'],
                    text_body="Fout bij het ophalen van SBM API gemeente data %s" % (gemeente.gemeente_naam),
                    html_body=None
                )
                continue

            # Special case for Amersfoort which has a 'fake' stembureau that
            # needs to be removed at our side
            if m['gemeente_code'] == 'GM0307':
                data = [s for s in data if s['Naam stembureau'] != 'Voorzitterspool extra werving']

            records = StembureauManagerParser().parse(data)
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
