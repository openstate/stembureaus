from app import app, db
from app.models import Gemeente, User, Gemeente_user, Election, BAG, ckan, add_user, Record
from app.email import send_invite, send_update
from app.parser import BaseParser, UploadFileParser, valid_headers
from app.validator import Validator
from app.routes import _remove_id, _create_record, kieskringen
from app.utils import find_buurt_and_wijk

from datetime import datetime
from urllib.parse import urljoin
from pprint import pprint

from dateutil import parser
import requests
from flask import url_for

class StembureauManagerParser(BaseParser):
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
        pprint(data)
        for d in data:
            r = self.convert_to_record(d)
            result.append(r)
        return result

    def parse(self, path):
        headers = valid_headers
        records = self._get_records(path, headers)
        clean_records = self._clean_records(records)
        return clean_records


class StembureauManager(object):
    def __init__(self, *arg, **kwargs):
        for kwarg, v in kwargs.items():
            setattr(self, kwarg, v)

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
            data = self.get_municipality(m['gemeente_code'])
            if not isinstance(data, list):
            #if data.get('statusCode', 200) >= 400:
                print("Could not get data for %s" % (m,))
                continue
            records = StembureauManagerParser().parse(data)
            pprint(records[0])
            validator = Validator()
            results = validator.validate(records)
            pprint(results)
            for idx, details in results['results'].items():
                if len(details['errors'].keys()) > 0:
                    print(idx)
                    pprint(details['errors'])
                    if idx < len(records):
                        pprint(records[idx])
