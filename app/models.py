from time import time
from decimal import Decimal
import json
import os

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ckanapi import RemoteCKAN
from ckanapi.errors import CKANAPIError
import jwt

from app import app, db, login_manager
from app.email import send_email, send_invite


class CKAN():
    def __init__(self):
        self.ua = (
            'waarismijnstemlokaal/1.0 (+https://waarismijnstemlokaal.nl/)'
        )
        self.ckanapi = RemoteCKAN(
            app.config['CKAN_URL'],
            apikey=app.config['CKAN_API_KEY'],
            user_agent=self.ua
        ).action
        self.elections = app.config['CKAN_CURRENT_ELECTIONS']
        self.resources_metadata = self._get_resources_metadata()

    def create_datastore(self, resource_id, fields):
        self.ckanapi.datastore_create(
            resource_id=resource_id,
            force=True,
            fields=fields,
            primary_key=['UUID']
        )

    def resource_show(self, resource_id):
        return self.ckanapi.resource_show(
            id=resource_id
        )

    def delete_datastore(self, resource_id):
        self.ckanapi.datastore_delete(
            resource_id=resource_id,
            force=True
        )

    def _get_resources_metadata(self):
        resources_metadata = {}
        for election_key, election_value in self.elections.items():
            resources_metadata[election_key] = {}
            try:
                resources_metadata[election_key]['publish_resource'] = (
                    self.ckanapi.resource_show(
                        id=election_value['publish_resource']
                    )
                )
            except CKANAPIError as e:
                app.logger.error(
                    'Can\'t get publish resource metadata: %s' % (e)
                )

            try:
                resources_metadata[election_key]['draft_resource'] = (
                    self.ckanapi.resource_show(id=election_value['draft_resource'])
                )
            except CKANAPIError as e:
                app.logger.error(
                    'Can\'t get draft resource metadata: %s' % (e)
                )
        return resources_metadata

    def get_records(self, resource_id):
        try:
            return self.ckanapi.datastore_search(
                resource_id=resource_id, limit=15000)
        except CKANAPIError as e:
            app.logger.error(
                'Can\'t get records: %s' % (e)
            )
            return {'records': []}

    def filter_records(self, resource_id, datastore_filters={}):
        try:
            return self.ckanapi.datastore_search(
                resource_id=resource_id, filters=datastore_filters, limit=15000)
        except CKANAPIError as e:
            app.logger.error(
                'Can\'t filter records: %s' % (e)
            )
            return {'records': []}

    def save_records(self, resource_id, records):
        self.ckanapi.datastore_upsert(
            resource_id=resource_id,
            force=True,
            records=records,
            method='upsert'
        )

    def delete_records(self, resource_id, filters=None):
        self.ckanapi.datastore_delete(
            resource_id=resource_id,
            force=True,
            filters=filters
        )

    # First delete all records in the publish_resource for the current
    # gemeente, then upsert all draft_records of the current gemeente
    # to the publish_resource
    def publish(self, verkiezing, gemeente_code, draft_records):
        election = self.elections[verkiezing]
        self.delete_records(
            election['publish_resource'],
            {'CBS gemeentecode': gemeente_code}
        )

        self.save_records(election['publish_resource'], draft_records)


ckan = CKAN()


class Gemeente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gemeente_naam = db.Column(db.String(120), index=True, unique=True)
    gemeente_code = db.Column(db.String(6), index=True, unique=True)
    source = db.Column(db.String(32))
    elections = db.relationship('Election', backref='gemeente', lazy='dynamic')
    users = db.relationship('User', secondary='gemeente_user')

    def __repr__(self):
        return '<Gemeente {}>'.format(self.gemeente_naam)

    def to_json(self):
        # an SQLAlchemy class
        fields = {}
        fields_not = [
            'query', 'query_class', 'to_json', 'registry', 'metadata']
        for field in [x for x in dir(self) if not x.startswith('_') and x not in fields_not]:
            data = self.__getattribute__(field)
            # Do this so we can convert the lat, lon, x and y fields
            if isinstance(data, Decimal):
                data = float(data)
            try:
                # This will fail on non-encodable values, like other classes
                json.dumps(data)
                fields[field] = data
            except TypeError:
                fields[field] = None
        # A json-encodable dict
        return fields


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    admin = db.Column(db.Boolean, default=False)

    gemeenten = db.relationship(
        'Gemeente',
        secondary='gemeente_user'
    )

    def set_password(self, password):
        if len(password) < 12:
            raise RuntimeError(
                'Attempted to set password with length less than 12 characters'
            )
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=86400):
        return jwt.encode(
            {
                'reset_password': self.id,
                'exp': time() + expires_in
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms='HS256'
            )['reset_password']
        except:
            return
        return User.query.get(user_id)

    def __repr__(self):
        return '<User {}>'.format(self.email)


# Association table for the many-to-many relationship
# between Gemeente and User
class Gemeente_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gemeente_id = db.Column(db.Integer, db.ForeignKey('gemeente.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    gemeente = db.relationship(Gemeente, backref="Gemeente_user")
    user = db.relationship(User, backref="Gemeente_user")


# Add a user and link it to a gemeente by specifying the gemeente,
# user's email address and name. Also allow to enable or disable sending
# of a logging mail to the admins.
def add_user(gemeente_id, email, name='', send_logging_mail=True):
    user_created = 0

    # Add user
    user = User.query.filter_by(
        email=email
    ).first()

    # Make sure the user doesn't exist already
    if not user:
        user = User(
            email=email
        )
        user.set_password(os.urandom(24))
        db.session.add(user)
        db.session.commit()
        user_created = 1

        # Send the new user an invitation email
        send_invite(user)

        # Send logging mail
        if send_logging_mail:
            selected_gemeente = Gemeente.query.filter_by(id=gemeente_id).first()
            body = (
                f"Gemeente: {selected_gemeente.gemeente_naam}<br>"
                f"E-mailadres: {email}<br>"
                f"Naam contactpersoon: {name}"
            )
            send_email(
                '[WaarIsMijnStemlokaal.nl] Nieuwe account aanvraag',
                sender=app.config['FROM'],
                recipients=app.config['ADMINS'],
                text_body=body,
                html_body=body
            )
    else:
        print(
            "User already exists (might be because it is part of "
            "multiple municipalities): %s" % (email)
        )

    # Add record to the Gemeente_user association table
    gemeente_user = Gemeente_user.query.filter_by(
        gemeente_id=gemeente_id,
        user_id=user.id
    ).first()

    # Make sure the record doesn't exist already
    if not gemeente_user:
        gemeente_user = Gemeente_user(
            gemeente_id=gemeente_id,
            user_id=user.id
        )
        db.session.add(gemeente_user)
        db.session.commit()

    # 1 if yes, otherwise 0. This is used by
    # add_gemeenten_verkiezingen_users to count the total number of
    # users created.
    return user_created


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    verkiezing = db.Column(db.String(250), index=True)
    gemeente_id = db.Column(db.Integer, db.ForeignKey("gemeente.id"))


class BAG(db.Model):
    __tablename__ = 'bag'

    openbareruimte = db.Column(db.String(250))
    huisnummer = db.Column(db.String(5))
    huisletter = db.Column(db.String(5))
    huisnummertoevoeging = db.Column(db.String(5))
    postcode = db.Column(db.String(6))
    woonplaats = db.Column(db.String(255))
    gemeente = db.Column(db.String(255))
    provincie = db.Column(db.String(255))
    nummeraanduiding = db.Column(db.String(24), primary_key=True)
    verblijfsobjectgebruiksdoel = db.Column(db.String(255))
    oppervlakteverblijfsobject = db.Column(db.String(10))
    verblijfsobjectstatus = db.Column(db.String(255))
    object_id = db.Column(db.String(24))
    object_type = db.Column(db.String(10))
    nevenadres = db.Column(db.String(1))
    pandid = db.Column(db.String(24))
    pandstatus = db.Column(db.String(255))
    pandbouwjaar = db.Column(db.String(20))
    x = db.Column(db.Numeric(precision=25, scale=9))
    y = db.Column(db.Numeric(precision=25, scale=9))
    lat = db.Column(db.Numeric(precision=24, scale=16))
    lon = db.Column(db.Numeric(precision=24, scale=16))
    verkorteopenbareruimte = db.Column(db.String(255))

    def to_json(self):
        # an SQLAlchemy class
        fields = {}
        fields_not = [
            'query', 'query_class', 'to_json', 'registry', 'metadata']
        for field in [x for x in dir(self) if not x.startswith('_') and x not in fields_not]:
            data = self.__getattribute__(field)
            # Do this so we can convert the lat, lon, x and y fields
            if isinstance(data, Decimal):
                data = float(data)
            try:
                # This will fail on non-encodable values, like other classes
                json.dumps(data)
                fields[field] = data
            except TypeError:
                fields[field] = None
        # A json-encodable dict
        return fields


class Record(object):
    def __init__(self, *args, **kwargs):
        self.record = {}
        self.populate(kwargs)
        self.expand()

    def populate(self, record):
        self.record = {
            'nummer_stembureau': record['nummer stembureau'],
            'naam_stembureau': record['naam stembureau'],
            'type_stembureau': record['type stembureau'],
            'website_locatie': record['website locatie'],
            'bag_nummeraanduiding_id': record['bag nummeraanduiding id'],
            'extra_adresaanduiding': record['extra adresaanduiding'],
            'latitude': record['latitude'],
            'longitude': record['longitude'],
            'x': record['x'],
            'y': record['y'],
            'openingstijd': record['openingstijd'],
            'sluitingstijd': record['sluitingstijd'],
            'toegankelijk_voor_mensen_met_een_lichamelijke_beperking': record[
                'toegankelijk voor mensen met een lichamelijke beperking'
            ],
            'toegankelijke_ov_halte': record['toegankelijke ov-halte'],
            'gehandicaptentoilet': record[
                'gehandicaptentoilet'
            ],
            'host': record['host'],
            'geleidelijnen': record['geleidelijnen'],
            'stemmal_met_audio_ondersteuning': record[
                'stemmal met audio-ondersteuning'
            ],
            'kandidatenlijst_in_braille': record['kandidatenlijst in braille'],
            'kandidatenlijst_met_grote_letters': record[
                'kandidatenlijst met grote letters'
            ],
            'gebarentolk_ngt': record['gebarentolk (ngt)'],
            'gebarentalig_stembureaulid_ngt': record[
                'gebarentalig stembureaulid (ngt)'
            ],
            'akoestiek_geschikt_voor_slechthorenden': record[
                'akoestiek geschikt voor slechthorenden'
            ],
            'prikkelarm': record['prikkelarm'],
            'extra_toegankelijkheidsinformatie': record[
                'extra toegankelijkheidsinformatie'
            ],
            'overige_informatie': record['overige informatie'],
            'tellocatie': record['tellocatie'],
            'contactgegevens_gemeente': record['contactgegevens gemeente'],
            'verkiezingswebsite_gemeente': record['verkiezingswebsite gemeente']
        }

        # If there are 'waterschapsverkiezingen', add the 'verkiezingen' field
        # to the record
        if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            self.record['verkiezingen'] = record['verkiezingen']

    def expand(self):
        record = BAG.query.get(self.record['bag_nummeraanduiding_id'])

        if record is not None:
            full_address =  record.openbareruimte + ' ' + record.huisnummer + record.huisletter
            if (record.huisnummertoevoeging is not None) and (record.huisnummertoevoeging != ''):
                full_address += '-%s' % (record.huisnummertoevoeging)
            full_address += f' ({record.woonplaats}) [{record.nummeraanduiding}]'
            self.record['adres_stembureau'] = full_address

            geofields = {
                'lat': 'latitude',
                'lon': 'longitude',
                'x': 'x',
                'y': 'y'
            }
            for f, rf in geofields.items():
                if not self.record.get(rf):
                    self.record[rf] = getattr(record, f)

        for fld in [
            'gemeente',
            'straatnaam',
            'huisnummer',
            'huisletter',
            'huisnummertoevoeging',
            'postcode',
            'plaats',
            # wijknaam
            # cbs wijknummer
            # buurtnaam
            # cbs buurtnummer
            # x
            # y
        ]:
            # TODO: we need to know if these are the right fields for in CKAN.
            fld_val = getattr(record, fld, None)
            if fld_val is not None:
                self.record[fld] = fld_val.encode('utf-8').decode()
            else:
                self.record[fld] = None

# Create the MySQL tables if they don't exist
db.create_all()
