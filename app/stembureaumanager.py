from flask import current_app
from datetime import datetime

from app.ckan import ckan
from app.models import db
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
            record['toilet'] = locatie.get('Toilet', '')
            record['host'] = locatie.get('Host', '')
            record['geleidelijnen'] = locatie.get('Geleidelijnen', '')
            record['stemmal_met_audio_ondersteuning'] = locatie.get('Stemmal met audio-ondersteuning', '')
            record['kandidatenlijst_in_braille'] = locatie.get('Kandidatenlijst in braille', '')
            record['kandidatenlijst_met_grote_letters'] = locatie.get('Kandidatenlijst met grote letters', '')
            record['gebarentolk_ngt'] = locatie.get('Gebarentolk (NGT)', '')
            record['gebarentalig_stembureaulid_ngt'] = locatie.get('Gebarentalig stembureaulid (NGT)', '')
            record['akoestiek_geschikt_voor_slechthorenden'] = locatie.get('Akoestiek geschikt voor slechthorenden', '')
            record['prikkelarm'] = locatie.get('Prikkelarm', '')
            record['prokkelduo'] = locatie.get('Prokkelduo', '')
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
        publish_gemeente_records(gemeente.gemeente_code, current_app)

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

    def _skip_gemeente(self, m_updated, gemeente, gemeente_draft_records):
        # Don't skip this gemeente, if the gm_code was specified in the command
        # line (i.e. we explicitly want to import this gemeente)
        if self.gm_code:
            return False

        # Skip a gemeente if it already contains (draft) stembureaus and if the
        # source is different. This prevents accidentally deleting data. E.g.,
        # if a gemeente has already added stembureaus manually, we don't want
        # this data to be automatically overwritten with API data. Also if a
        # gemeente is available in more than one API, we don't want to load the
        # data from different APIs.
        if gemeente_draft_records and gemeente.source != self.SOURCE_STRING:
            send_email(
                f"[WaarIsMijnStemlokaal.nl] {gemeente.gemeente_naam} ({gemeente.gemeente_code}) heeft al data via andere bron",
                sender=current_app.config['FROM'],
                recipients=current_app.config['ADMINS'],
                text_body=f'{gemeente.gemeente_naam} ({gemeente.gemeente_code}) is niet ingeladen via de API van {self.SOURCE_STRING}, want deze gemeente heeft al (concept) data beschikbaar via {gemeente.source if gemeente.source else "handmatige invoer"}.',
                html_body=None
            )
            return True

        # Don't skip this gemeente, if
        # - the SOURCE_STRING is not set (i.e., the gemeente was never
        #   imported before via this API),
        # - api_laatste_wijziging is not set in the database (i.e. the
        #   gemeente was never imported before via an API)
        if gemeente.source != self.SOURCE_STRING or not gemeente.api_laatste_wijziging:
            return False

        # If a timestamp was specified in the command line
        if self.from_date:
            # Skip this gemeente, if the updated timestamp from the API is
            # smaller than or equal to the timestamp specified in the command
            # line
            if m_updated <= self.from_date:
                return True
            # Else don't skip this gemeente
            else:
                return False

        # Skip this gemeente, if the updated timestamp from the API is smaller
        # than or equal to the last updated timestamp in the database
        if m_updated <= gemeente.api_laatste_wijziging:
            return True
        # Else don't skip this gemeente
        else:
            return False


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
            # Some APIs return microseconds; set these to 0. This is necessary
            # because the database will round the timestamp so some gemeenten
            # will then be imported every hour while their gewijzigd timestamp
            # hasn't changed
            m_updated = m_updated.replace(microsecond=0)
            elections = gemeente.elections
            # Pick the first election. In the case of multiple elections we only
            # retrieve the stembureaus of the first election as the records for
            # both elections are the same (at least for the GR2018 + referendum
            # elections on March 21st 2018).
            verkiezing = elections[0].verkiezing
            gemeente_draft_records = ckan.filter_draft_records(verkiezing, m['gemeente_code'])
            if self._skip_gemeente(m_updated, gemeente, gemeente_draft_records):
                continue

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
