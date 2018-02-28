from app import app, db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
from ckanapi import RemoteCKAN
import jwt


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
            primary_key=['primary_key']
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
            resources_metadata[election_key]['publish_resource'] = (
                self.ckanapi.resource_show(
                    id=election_value['publish_resource']
                )
            )
            resources_metadata[election_key]['draft_resource'] = (
                self.ckanapi.resource_show(id=election_value['draft_resource'])
            )
        return resources_metadata

    def get_records(self, resource_id):
        return self.ckanapi.datastore_search(
            resource_id=resource_id, limit=10000
        )

    def filter_records(self, resource_id, datastore_filters={}):
        return self.ckanapi.datastore_search(
            resource_id=resource_id, filters=datastore_filters, limit=10000
        )

    def save_records(self, resource_id, records):
        self.ckanapi.datastore_upsert(
            resource_id=resource_id,
            force=True,
            records=records,
            method='upsert'
        )

    def delete_records(self, resource_id, filters):
        self.ckanapi.datastore_delete(
            resource_id=resource_id,
            force=True,
            filters=filters
        )

    # First delete all records in the publish_resource for the current
    # gemeente, then upsert all draft_records of the current gemeenten
    # to the publish_resource
    def publish(self, verkiezing, draft_records):
        election = self.elections[verkiezing]
        self.delete_records(
            election['publish_resource'],
            {'CBS gemeentecode': draft_records[0]['CBS gemeentecode']}
        )

        self.save_records(election['publish_resource'], draft_records)


ckan = CKAN()


# The users are gemeenten
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gemeente_naam = db.Column(db.String(120), index=True, unique=True)
    gemeente_code = db.Column(db.String(6), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    elections = db.relationship('Election', backref='gemeente', lazy='dynamic')

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
        ).decode('utf-8')

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    verkiezing = db.Column(db.String(250), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


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
    lon = db.Column(db.Numeric(precision=24, scale=16))
    lat = db.Column(db.Numeric(precision=24, scale=16))


class Record(object):
    def __init__(self, *args, **kwargs):
        self.record = {}
        self.populate(kwargs)
        self.expand()

    def populate(self, record):
        try:
            bag_ref = record['bag referentienummer']
        except KeyError:
            bag_ref = record['bag referentie nummer']
        self.record = {
            'nummer_stembureau': record['nummer stembureau'],
            'naam_stembureau': record['naam stembureau'],
            'website_locatie': record['website locatie'],
            'bag_referentienummer': bag_ref,
            'extra_adresaanduiding': record['extra adresaanduiding'],
            'longitude': record['longitude'],
            'latitude': record['latitude'],
            'districtcode': record['districtcode'],
            'openingstijden': record['openingstijden'],
            'mindervaliden_toegankelijk': record['mindervaliden toegankelijk'],
            'invalidenparkeerplaatsen': record['invalidenparkeerplaatsen'],
            'akoestiek': record['akoestiek'],
            'mindervalide_toilet_aanwezig': record[
                'mindervalide toilet aanwezig'],
            'contactgegevens': record['contactgegevens'],
            'beschikbaarheid': record['beschikbaarheid']
        }

    def expand(self):
        record = BAG.query.get(self.record['bag_referentienummer'])

        for fld in [
            'gemeente',
            'straatnaam',
            'huisnummer',
            'huisnummetoevoeging',
            'postcode',
            'plaats',
            # wijknaam
            # cbs wijknummer
            # buurtnaam
            # cbs buurtnummer
            # x
            # y
        ]:
            # TODO: we need to know if these are the righ fields for in CKAN.
            self.record[fld] = getattr(record, fld, None)

# Create the 'User' table above if it doesn't exist
db.create_all()
