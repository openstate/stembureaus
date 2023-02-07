from app import app, db
from app.models import Gemeente, User, Gemeente_user, Election, BAG, ckan, add_user, Record
from app.email import send_invite, send_update
from app.parser import UploadFileParser
from app.validator import Validator
from app.routes import _remove_id, _create_record, kieskringen
from app.utils import find_buurt_and_wijk

from datetime import datetime
from urllib.parse import urljoin
from pprint import pprint

from dateutil import parser
import requests
from flask import url_for

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

    def convert_to_record(self, data):
        pprint(data)
        return Record(**{
            'nummer stembureau': data['Nummer stembureau'],
            'naam stembureau': data['Naam stembureau'],
            'type stembureau': data['Type stembureau'],
            'website locatie': data['Locaties'][0]['Website locatie'],
            'bag nummeraanduiding id': data['Locaties'][0]['BAG Nummeraanduiding ID'],
            'extra adresaanduiding': data['Locaties'][0]['Extra adresaanduiding'],
            'latitude': data['Locaties'][0]['Latitude'],
            'longitude': data['Locaties'][0]['Longitude'],
            'x': None,
            'y': None,
            'openingstijd': data['Locaties'][0]['Openingstijden'][0]['Openingstijd'],
            'sluitingstijd': data['Locaties'][0]['Openingstijden'][0]['Sluitingstijd'],
            'toegankelijk voor mensen met een lichamelijke beperking': data['Locaties'][0][
                'Toegankelijk voor mensen met een lichamelijke beperking'],
            'toegankelijke ov-halte': data['Locaties'][0]['Toegankelijke ov-halte'],
            'akoestiek': data['Locaties'][0]['Akoestiek'],
            'auditieve hulpmiddelen': data['Locaties'][0]['Auditieve hulpmiddelen'],
            'visuele hulpmiddelen': data['Locaties'][0]['Visuele hulpmiddelen'],
            'gehandicaptentoilet': data['Locaties'][0]['Gehandicaptentoilet'],
            'extra toegankelijkheidsinformatie': data['Locaties'][0]['Extra toegankelijkheidsinformatie'],
            'tellocatie': data['Locaties'][0]['Tellocatie'],
            'contactgegevens gemeente': data['Contactgegevens gemeente'],
            'verkiezingswebsite gemeente': data['Verkiezingswebsite gemeente'],
            'verkiezingen': data['Verkiezingen']
        })

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
            pprint(data)
            for d in data:
                r = self.convert_to_record(d)
        #pprint(result)
