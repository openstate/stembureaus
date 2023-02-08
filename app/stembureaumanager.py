from app import app, db
from app.models import Gemeente, User, Gemeente_user, Election, BAG, ckan, add_user, Record
from app.email import send_invite, send_update, send_email
from app.parser import BaseParser, UploadFileParser, valid_headers
from app.validator import Validator
from app.routes import _remove_id, _create_record, kieskringen
from app.utils import find_buurt_and_wijk, get_gemeente

from datetime import datetime
from urllib.parse import urljoin
from pprint import pprint

from dateutil import parser
import requests
from flask import url_for

class BaseAPIParser(BaseParser):
    pass


class StembureauManagerParser(BaseAPIParser):
    def convert_to_record(self, data):
        return {
            'nummer_stembureau': data['Nummer stembureau'],
            'naam_stembureau': data['Naam stembureau'],
            'type_stembureau': data['Type stembureau'],
            'website_locatie': data['Locaties'][0]['Website locatie'],
            'bag_nummeraanduiding_id': data['Locaties'][0]['BAG Nummeraanduiding ID'],
            'extra_adresaanduiding': data['Locaties'][0]['Extra adresaanduiding'],
            'latitude': str(data['Locaties'][0]['Latitude']),
            'longitude': str(data['Locaties'][0]['Longitude']),
            # 'x': None,
            # 'y': None,
            'openingstijd': data['Locaties'][0]['Openingstijden'][0]['Openingstijd'],
            'sluitingstijd': data['Locaties'][0]['Openingstijden'][0]['Sluitingstijd'],
            'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': data['Locaties'][0][
                'Toegankelijk voor mensen met een lichamelijke beperking'],
            'toegankelijke_ov_halte': data['Locaties'][0]['Toegankelijke ov-halte'],
            'akoestiek': data['Locaties'][0]['Akoestiek'],
            'auditieve_hulpmiddelen': data['Locaties'][0]['Auditieve hulpmiddelen'],
            'visuele_hulpmiddelen': data['Locaties'][0]['Visuele hulpmiddelen'],
            'gehandicaptentoilet': data['Locaties'][0]['Gehandicaptentoilet'],
            'extra_toegankelijkheidsinformatie': data['Locaties'][0]['Extra toegankelijkheidsinformatie'],
            'tellocatie': data['Locaties'][0]['Tellocatie'],
            'contactgegevens_gemeente': data['Contactgegevens gemeente'],
            'verkiezingswebsite_gemeente': data['Verkiezingswebsite gemeente'],
            'verkiezingen': data['Verkiezingen']
        }

    def _get_records(self, data, headers):
        result = []
        for d in data:
            r = self.convert_to_record(d)
            result.append(r)
        return result

    def parse(self, path):
        headers = valid_headers
        records = self._get_records(path, headers)
        clean_records = self._clean_records(records)
        return clean_records


class APIManager(object):
    def __init__(self, *arg, **kwargs):
        for kwarg, v in kwargs.items():
            setattr(self, kwarg, v)

    def _get_draft_and_publish_records_for_gemeente(self, verkiezing, gemeente_code):
        """
        Gets draft and published records for the speicified municipality
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
                        _create_record(
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

    def _publish_draft_records(self, gemeente, gemeente_draft_records, elections):
        _remove_id(gemeente_draft_records)
        for election in [x.verkiezing for x in elections]:
            ckan.publish(election, gemeente.gemeente_code, gemeente_draft_records)

    def _send_error_email(self, gemeente, records, results):
        output = 'Er zijn fouten aangetroffen in de resultaten voor de gemeente %s :\n\n' % (
            gemeente.gemeente_naam,)
        for idx, details in results['results'].items():
            if len(details['errors'].keys()) > 0:
                # the spreadsheet starts at row 5 ...
                real_idx = idx - 6
                s = records[real_idx]
                output += 'Stembureau %s. %s :\n' % (s['nummer_stembureau'], s['naam_stembureau'])
                for fld, fld_errors in details['errors'].items():
                    output += '%s: %s\n' % (fld, fld_errors[0],)
                output += '\n\n'
        print(output)
        send_email(
            "[WaarIsMijnStemlokaal.nl] Fouten bij het inladen van %s via API" % (
                gemeente.gemeente_naam,),
            sender=app.config['FROM'],
            recipients=app.config['ADMINS'],
            text_body=output,
            html_body=None)



class StembureauManager(APIManager):
    def _request(self, method, params=None):
        url = urljoin(app.config['STEMBUREAUMANAGER_BASE_URL'], method)
        print(url)
        return requests.get(url, params=params, headers={
            'x-api-key': app.config['STEMBUREAUMANAGER_API_KEY']
        }).json()

    def overview(self):
        return self._request('overzicht')

    def get_municipality(self, municipality_id):
        #  https://test-opendata.stembureaumanager.nl/api/stembureau/gemeente?id=GM<code>
        return self._request('gemeente', params={'id': municipality_id})

    def run(self):
        municipalities = self.overview()
        for m in municipalities:
            m_updated = parser.parse(m['gewijzigd'])
            if m_updated <= self.from_date:
                continue
            gemeente = get_gemeente(m['gemeente_code'])
            print(gemeente)
            elections = gemeente.elections.all()
            # Pick the first election. In the case of multiple elections we only
            # retrieve the stembureaus of the first election as the records for
            # both elections are the same (at least for the GR2018 + referendum
            # elections on March 21st 2018).
            verkiezing = elections[0].verkiezing
            gemeente_draft_records, gemeente_publish_records = self._get_draft_and_publish_records_for_gemeente(
                verkiezing, m['gemeente_code'])
            print("Loaded %s draft records and %s published records" % (
                len(gemeente_draft_records), len(gemeente_publish_records),))
            # print(elections)
            # print(verkiezing)
            data = self.get_municipality(m['gemeente_code'])
            if not isinstance(data, list):
            #if data.get('statusCode', 200) >= 400:
                print("Could not get data for %s" % (m,))
                continue
            records = StembureauManagerParser().parse(data)
            #pprint(records[0])
            validator = Validator()
            results = validator.validate(records)
            #pprint(results)
            self._save_draft_records(gemeente, gemeente_draft_records, elections, results)
            self._publish_draft_records(gemeente, gemeente_draft_records, elections)

            if not results['no_errors']:
                print("Errors where found in the results")
                self._send_error_email(gemeente, records, results)
            #print(results['results'])
