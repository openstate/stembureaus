from app import app, db
from app.models import Gemeente, User, Gemeente_user, Election, BAG, ckan, add_user
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

    def overview(self):
        url = urljoin(app.config['STEMBUREAUMANAGER_BASE_URL'], 'overzicht')
        print(url)
        return requests.get(url, headers={
            'x-api-key': app.config['STEMBUREAUMANAGER_API_KEY']
        }).json()

    def run(self):
        municipalities = self.overview()
        for m in municipalities:
            m_updated = parser.parse(m['gewijzigd'])
            if m_updated > self.from_date:
                pprint(m)
        #pprint(result)
