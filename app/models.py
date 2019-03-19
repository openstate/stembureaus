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
            resource_id=resource_id, limit=10000)

    def filter_records(self, resource_id, datastore_filters={}):
        return self.ckanapi.datastore_search(
            resource_id=resource_id, filters=datastore_filters, limit=10000)

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
    def publish(self, verkiezing, draft_records):
        election = self.elections[verkiezing]
        self.delete_records(
            election['publish_resource'],
            {'CBS gemeentecode': draft_records[0]['CBS gemeentecode']}
        )

        self.save_records(election['publish_resource'], draft_records)


ckan = CKAN()


class Gemeente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gemeente_naam = db.Column(db.String(120), index=True, unique=True)
    gemeente_code = db.Column(db.String(6), index=True, unique=True)
    elections = db.relationship('Election', backref='gemeente', lazy='dynamic')
    users = db.relationship('User', secondary='gemeente_user')

    def __repr__(self):
        return '<Gemeente {}>'.format(self.gemeente_naam)


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


# Association table for the many-to-many relationship
# between Gemeente and User
class Gemeente_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gemeente_id = db.Column(db.Integer, db.ForeignKey('gemeente.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    gemeente = db.relationship(Gemeente, backref="Gemeente_user")
    user = db.relationship(User, backref="Gemeente_user")


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
            'x': record['x'],
            'y': record['y'],
            'openingstijden': record['openingstijden'],
            'mindervaliden_toegankelijk': record['mindervaliden toegankelijk'],
            'akoestiek': record['akoestiek'],
            'mindervalide_toilet_aanwezig': record[
                'mindervalide toilet aanwezig'],
            'contactgegevens': record['contactgegevens'],
            'beschikbaarheid': record['beschikbaarheid'],
            'verkiezingen': record['verkiezingen'],
            'v1_1_a_aanduiding_aanwezig': record['1.1.a aanduiding aanwezig'],
            'v1_1_b_aanduiding_duidelijk_zichtbaar': record['1.1.b aanduiding duidelijk zichtbaar'],
            'v1_1_c_aanduiding_goed_leesbaar': record['1.1.c aanduiding goed leesbaar'],
            'v1_2_a_gpa_aanwezig': record['1.2.a gpa aanwezig'],
            'v1_2_b_aantal_vrij_parkeerplaatsen_binnen_50m_van_de_entree': record['1.2.b aantal vrij parkeerplaatsen binnen 50m van de entree'],
            'v1_2_c_hoogteverschil_tussen_parkeren_en_trottoir': record['1.2.c hoogteverschil tussen parkeren en trottoir'],
            'v1_2_d_hoogteverschil': record['1.2.d hoogteverschil'],
            'v1_2_e_type_overbrugging': record['1.2.e type overbrugging'],
            'v1_2_f_overbrugging_conform_itstandaard': record['1.2.f overbrugging conform itstandaard'],
            'v1_3_a_vlak_verhard_en_vrij_van_obstakels': record['1.3.a vlak, verhard en vrij van obstakels'],
            'v1_3_b_hoogteverschil': record['1.3.b hoogteverschil'],
            'v1_3_c_type_overbrugging': record['1.3.c type overbrugging'],
            'v1_3_d_overbrugging_conform_itstandaard': record['1.3.d overbrugging conform itstandaard'],
            'v1_3_e_obstakelvrije_breedte_van_de_route': record['1.3.e obstakelvrije breedte van de route'],
            'v1_3_f_obstakelvrije_hoogte_van_de_route': record['1.3.f obstakelvrije hoogte van de route'],
            'v1_4_a_is_er_een_route_tussen_gebouwentree_en_stemruimte': record['1.4.a is er een route tussen gebouwentree en stemruimte'],
            'v1_4_b_route_duidelijk_aangegeven': record['1.4.b route duidelijk aangegeven'],
            'v1_4_c_vlak_en_vrij_van_obstakels': record['1.4.c vlak en vrij van obstakels'],
            'v1_4_d_hoogteverschil': record['1.4.d hoogteverschil'],
            'v1_4_e_type_overbrugging': record['1.4.e type overbrugging'],
            'v1_4_f_overbrugging_conform_itstandaard': record['1.4.f overbrugging conform itstandaard'],
            'v1_4_g_obstakelvrije_breedte_van_de_route': record['1.4.g obstakelvrije breedte van de route'],
            'v1_4_h_obstakelvrije_hoogte_van_de_route': record['1.4.h obstakelvrije hoogte van de route'],
            'v1_4_i_deuren_in_route_bedien_en_bruikbaar': record['1.4.i deuren in route bedien- en bruikbaar'],
            'v2_1_a_deurtype': record['2.1.a deurtype'],
            'v2_1_b_opstelruimte_aan_beide_zijden_van_de_deur': record['2.1.b opstelruimte aan beide zijden van de deur'],
            'v2_1_c_bedieningskracht_buitendeur': record['2.1.c bedieningskracht buitendeur'],
            'v2_1_d_drempelhoogte_t_o_v_straat_vloer_niveau': record['2.1.d drempelhoogte (t.o.v. straat/vloer niveau)'],
            'v2_1_e_vrije_doorgangsbreedte_buitendeur': record['2.1.e vrije doorgangsbreedte buitendeur'],
            'v2_2_a_tussendeuren_aanwezig_in_eventuele_route': record['2.2.a tussendeuren aanwezig in eventuele route'],
            'v2_2_b_deurtype': record['2.2.b deurtype'],
            'v2_2_c_opstelruimte_aan_beide_zijden_van_de_deur': record['2.2.c opstelruimte aan beide zijden van de deur'],
            'v2_2_d_bedieningskracht_deuren': record['2.2.d bedieningskracht deuren'],
            'v2_2_e_drempelhoogte_t_o_v_vloer_niveau': record['2.2.e drempelhoogte (t.o.v. vloer niveau)'],
            'v2_2_f_vrije_doorgangsbreedte_deur': record['2.2.f vrije doorgangsbreedte deur'],
            'v2_3_a_deur_aanwezig_naar_van_stemruimte': record['2.3.a deur aanwezig naar/van stemruimte'],
            'v2_3_b_deurtype': record['2.3.b deurtype'],
            'v2_3_c_opstelruimte_aan_beide_zijden_van_de_deur': record['2.3.c opstelruimte aan beide zijden van de deur'],
            'v2_3_d_bedieningskracht_deur': record['2.3.d bedieningskracht deur'],
            'v2_3_e_drempelhoogte_t_o_v_vloer_niveau': record['2.3.e drempelhoogte (t.o.v. vloer niveau)'],
            'v2_3_f_vrije_doorgangsbreedte_deur': record['2.3.f vrije doorgangsbreedte deur'],
            'v2_4_a_zijn_er_tijdelijke_voorzieningen_aangebracht': record['2.4.a zijn er tijdelijke voorzieningen aangebracht'],
            'v2_4_b_vloerbedekking_randen_over_de_volle_lengte_deugdelijk_afgeplakt': record['2.4.b vloerbedekking: randen over de volle lengte deugdelijk a'],
            'v2_4_c_hellingbaan_weerbestendig_alleen_van_toepassing_bij_buitentoepassing': record['2.4.c hellingbaan: weerbestendig (alleen van toepassing bij bu'],
            'v2_4_d_hellingbaan_deugdelijk_verankerd_aan_ondergrond': record['2.4.d hellingbaan: deugdelijk verankerd aan ondergrond'],
            'v2_4_e_leuning_bij_hellingbaan_trap_leuning_aanwezig_en_conform_criteria': record['2.4.e leuning bij hellingbaan/trap: leuning aanwezig en confor'],
            'v2_4_f_dorpeloverbrugging_weerbestendig_alleen_van_toepassing_bij_buitentoepassing': record['2.4.f dorpeloverbrugging: weerbestendig (alleen van toepassing'],
            'v2_4_g_dorpeloverbrugging_deugdelijk_verankerd_aan_ondergrond': record['2.4.g dorpeloverbrugging: deugdelijk verankerd aan ondergrond'],
            'v3_1_a_obstakelvrije_doorgangen': record['3.1.a obstakelvrije doorgangen'],
            'v3_1_b_vrije_draaicirkel_manoeuvreerruimte': record['3.1.b vrije draaicirkel / manoeuvreerruimte'],
            'v3_1_c_idem_voor_stemtafel_en_stemhokje': record['3.1.c idem voor stemtafel en stemhokje'],
            'v3_1_d_opstelruimte_voor_naast_stembus': record['3.1.d opstelruimte voor/naast stembus'],
            'v3_2_a_stoelen_in_stemruimte_aanwezig': record['3.2.a stoelen in stemruimte aanwezig'],
            'v3_2_b_1_op_5_stoelen_uitgevoerd_met_armleuningen': record['3.2.b 1 op 5 stoelen uitgevoerd met armleuningen'],
            'v3_3_a_hoogte_van_het_laagste_schrijfblad': record['3.3.a hoogte van het laagste schrijfblad'],
            'v3_3_b_schrijfblad_onderrijdbaar': record['3.3.b schrijfblad onderrijdbaar'],
            'v3_4_a_hoogte_inworpgleuf_stembiljet': record['3.4.a hoogte inworpgleuf stembiljet'],
            'v3_4_b_afstand_inwerpgleuf_t_o_v_de_opstelruimte': record['3.4.b afstand inwerpgleuf t.o.v. de opstelruimte'],
            'v3_5_a_leesloep_zichtbaar_aanwezig': record['3.5.a leesloep (zichtbaar) aanwezig'],
            'v3_6_a_kandidatenlijst_in_stemlokaal_aanwezig': record['3.6.a kandidatenlijst in stemlokaal aanwezig'],
            'v3_6_b_opstelruimte_voor_de_kandidatenlijst_aanwezig': record['3.6.b opstelruimte voor de kandidatenlijst aanwezig']
        }

    def expand(self):
        record = BAG.query.get(self.record['bag_referentienummer'])

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
                self.record[fld] = fld_val.encode('latin1').decode()
            else:
                self.record[fld] = None

# Create the MySQL tables if they don't exist
db.create_all()
