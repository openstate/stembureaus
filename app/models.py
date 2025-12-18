from time import time
from decimal import Decimal
from datetime import datetime
import json
import os
import re

from flask import current_app
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import ForeignKey, String, DECIMAL, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy_lite import SQLAlchemy
from typing import List
import jwt
import pyotp

from app.email import send_email, send_invite

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(engine_options = {'connect_args': {'connect_timeout': 10, 'read_timeout': 20}})
login_manager = LoginManager()

from app.db_utils import db_count, db_exec_by_id, db_exec_one, db_exec_one_optional

def create_all():
    Base.metadata.create_all(db.engine)


# Association table for the many-to-many relationship
# between Gemeente and User
class Gemeente_user(Base):
    __tablename__ = "gemeente_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    gemeente_id: Mapped[int] = mapped_column(ForeignKey('gemeente.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))


class Gemeente(Base):
    __tablename__ = "gemeente"
    id: Mapped[int] = mapped_column(primary_key=True)
    gemeente_naam: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    gemeente_code: Mapped[str] = mapped_column(String(6), index=True, unique=True)
    source: Mapped[str] = mapped_column(String(32), nullable=True)
    api_laatste_wijziging: Mapped[datetime] = mapped_column(nullable=True)
    elections: Mapped[List['Election']] = relationship('Election', back_populates='gemeente')
    users: Mapped[List['User']] = relationship(secondary=Gemeente_user.__table__, back_populates='gemeenten')

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


class User(UserMixin, Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(162), nullable=True)
    admin: Mapped[bool] = mapped_column(default=False, nullable=True)
    has_2fa_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    secret_token: Mapped[str] = mapped_column(String(32), unique=True, nullable=True)

    gemeenten: Mapped[List[Gemeente]] = relationship(secondary=Gemeente_user.__table__, back_populates="users")


    def __init__(self, email, admin=False):
        self.email = email
        self.admin = admin
        self.secret_token = pyotp.random_base32()

    def get_authentication_setup_uri(self):
        return pyotp.totp.TOTP(self.secret_token).provisioning_uri(
            name=self.email, issuer_name=current_app.config['SERVER_NAME'])

    def is_otp_valid(self, user_otp):
        totp = pyotp.parse_uri(self.get_authentication_setup_uri())
        return totp.verify(user_otp)

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
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms='HS256'
            )['reset_password']
        except:
            return
        return db_exec_by_id(User, user_id)

    def __repr__(self):
        return '<User {} {}>'.format(self.id, self.email)


# Add a user and link it to a gemeente by specifying the gemeente,
# user's email address and name. Also allow to enable or disable sending
# of a logging mail to the admins.
def add_user(gemeente_id, email, name='', send_logging_mail=True):
    user_created = 0

    # Add user
    user = db_exec_one_optional(User, email=email)

    # Make sure the user doesn't exist already
    if not user:
        user = User(
            email=email
        )
        user.set_password(str(os.urandom(24)))
        db.session.add(user)
        db.session.commit()
        user_created = 1

        # Send the new user an invitation email
        send_invite(user)

        # Send logging mail
        if send_logging_mail:
            selected_gemeente = db_exec_one(select(Gemeente).filter_by(id=gemeente_id))
            body = (
                f"Gemeente: {selected_gemeente.gemeente_naam}<br>"
                f"E-mailadres: {email}<br>"
                f"Naam contactpersoon: {name}"
            )
            send_email(
                '[WaarIsMijnStemlokaal.nl] Nieuwe account aanvraag',
                sender=current_app.config['FROM'],
                recipients=current_app.config['ADMINS'],
                text_body=body,
                html_body=body
            )
    else:
        print(
            "User already exists (might be because it is part of "
            "multiple municipalities): %s" % (email)
        )

    # Safety check
    if not _add_gemeente_allowed(user, gemeente_id):
        return 0

    # Add record to the Gemeente_user association table
    gemeente_user = db_exec_one_optional(Gemeente_user, gemeente_id=gemeente_id, user_id=user.id)

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

def _add_gemeente_allowed(user, gemeente_id):
    existing_gemeenten_count = db_count(Gemeente_user, user_id=user.id)
    if existing_gemeenten_count < current_app.config['MAX_GEMEENTEN_PER_USER']:
        return True

    allowed = user.email in current_app.config['MAX_GEMEENTEN_PER_USER_EXCEPTIONS']
    add_to_email = ''
    if allowed:
        title = '[WaarIsMijnStemlokaal.nl] Toegestaan: teveel gemeenten aan 1 gebruiker koppelen'
        add_to_email = ' (whitelisted)'
    else:
        title = '[WaarIsMijnStemlokaal.nl] GEBLOKKEERD: Poging om teveel gemeenten aan 1 gebruiker te koppelen'

    body = (
        f"E-mailadres: {user.email}{add_to_email}<br>"
        f"Te koppelen gemeente id: {gemeente_id}<br>"
        f"Aantal gemeenten al gekoppeld: {existing_gemeenten_count}"
    )
    send_email(
        title,
        sender=current_app.config['FROM'],
        recipients=current_app.config['ADMINS'],
        text_body=body,
        html_body=body
    )

    return allowed


@login_manager.user_loader
def load_user(user_id):
    return db_exec_by_id(User, int(user_id))


class Election(Base):
    __tablename__ = "election"
    id: Mapped[int] = mapped_column(primary_key=True)
    verkiezing: Mapped[str] = mapped_column(String(250), index=True)
    gemeente_id: Mapped[int] = mapped_column(ForeignKey("gemeente.id"))
    gemeente = relationship('Gemeente', back_populates='elections')


class BAG(Base):
    __tablename__ = 'bag'

    openbareruimte: Mapped[str] = mapped_column(String(250), nullable=True)
    huisnummer: Mapped[str] = mapped_column(String(5), nullable=True)
    huisletter: Mapped[str] = mapped_column(String(5), nullable=True)
    huisnummertoevoeging: Mapped[str] = mapped_column(String(5), nullable=True)
    postcode: Mapped[str] = mapped_column(String(6), nullable=True)
    woonplaats: Mapped[str] = mapped_column(String(255), nullable=True)
    gemeente: Mapped[str] = mapped_column(String(255), nullable=True)
    provincie: Mapped[str] = mapped_column(String(255), nullable=True)
    nummeraanduiding: Mapped[str] = mapped_column(String(24), primary_key=True)
    verblijfsobjectgebruiksdoel: Mapped[str] = mapped_column(String(255), nullable=True)
    oppervlakteverblijfsobject: Mapped[str] = mapped_column(String(10), nullable=True)
    verblijfsobjectstatus: Mapped[str] = mapped_column(String(255), nullable=True)
    object_id: Mapped[str] = mapped_column(String(24), nullable=True)
    object_type: Mapped[str] = mapped_column(String(10), nullable=True)
    nevenadres: Mapped[str] = mapped_column(String(1), nullable=True)
    pandid: Mapped[str] = mapped_column(String(24), nullable=True)
    pandstatus: Mapped[str] = mapped_column(String(255), nullable=True)
    pandbouwjaar: Mapped[str] = mapped_column(String(20), nullable=True)
    x: Mapped[Decimal] = mapped_column(DECIMAL(precision=25, scale=9), nullable=True)
    y: Mapped[Decimal] = mapped_column(DECIMAL(precision=25, scale=9), nullable=True)
    lat: Mapped[Decimal] = mapped_column(DECIMAL(precision=24, scale=16), nullable=True)
    lon: Mapped[Decimal] = mapped_column(DECIMAL(precision=24, scale=16), nullable=True)
    verkorteopenbareruimte: Mapped[str] = mapped_column(String(255), nullable=True)

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

    def _strip_spaces(self, value):
        return (value or '').strip()

    def populate(self, record):
        self.record = {
            'nummer_stembureau': record['nummer stembureau'],
            'naam_stembureau': self._strip_spaces(record['naam stembureau']),
            'type_stembureau': record['type stembureau'],
            'website_locatie': self._strip_spaces(record['website locatie']),
            'bag_nummeraanduiding_id': self._strip_spaces(record['bag nummeraanduiding id']),
            'extra_adresaanduiding': self._strip_spaces(record['extra adresaanduiding']),
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
            'overige_informatie': self._strip_spaces(record['overige informatie']),
            'tellocatie': record['tellocatie'],
            'contactgegevens_gemeente': self._strip_spaces(record['contactgegevens gemeente']),
            'verkiezingswebsite_gemeente': self._strip_spaces(record['verkiezingswebsite gemeente'])
        }

        # If there are 'waterschapsverkiezingen', add the 'verkiezingen' field
        # to the record
        if [x for x in current_app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
            self.record['verkiezingen'] = record['verkiezingen']

    def expand(self):
        bag_record = db_exec_by_id(BAG, self.record['bag_nummeraanduiding_id'])

        if bag_record is not None:
            full_address =  bag_record.openbareruimte + ' ' + bag_record.huisnummer + bag_record.huisletter
            if (bag_record.huisnummertoevoeging is not None) and (bag_record.huisnummertoevoeging != ''):
                full_address += '-%s' % (bag_record.huisnummertoevoeging)
            full_address += f' ({bag_record.woonplaats}) [{bag_record.nummeraanduiding}]'
            self.record['adres_stembureau'] = full_address

            geofields = {
                'lat': 'latitude',
                'lon': 'longitude',
                'x': 'x',
                'y': 'y'
            }
            for f, rf in geofields.items():
                if not self.record.get(rf):
                    self.record[rf] = getattr(bag_record, f)
        elif self.record['bag_nummeraanduiding_id'] and re.match("^0+$", self.record['bag_nummeraanduiding_id']):
            full_address = f"[{self.record['bag_nummeraanduiding_id']}]"
            self.record['adres_stembureau'] = full_address

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
            fld_val = getattr(bag_record, fld, None)
            if fld_val is not None:
                self.record[fld] = fld_val.encode('utf-8').decode()
            else:
                self.record[fld] = None
