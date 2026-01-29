from datetime import datetime

from app.models import BAG
from app.db_utils import db_exec_all, db_exec_one_optional
from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import (
    ValidationError, DataRequired, InputRequired, Optional, Email, EqualTo, Length, URL,
    NumberRange, AnyOf, Regexp
)
from wtforms import (
    BooleanField, StringField, IntegerField, FloatField, PasswordField,
    SubmitField, FormField, FieldList, SelectField, SelectMultipleField,
    RadioField, HiddenField
)
import re

from app.utils import convert_xy_to_latlong, convert_latlong_to_xy


# This custom FloatField allows for both commas and dots as decimal
# separator
class CommaDotFloatField(FloatField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(valuelist[0].replace(',', '.'))
            except ValueError:
                self.data = None
                raise ValueError('Geen geldige waarde.')


# The default pre_validate of SelectField only warned that a value is not
# valid without specifying why it was not valid. This message shows exactly
# which values can be used.
class CustomSelectField(SelectField):
    def pre_validate(self, form):
        if not self.data in [v for v, _ in self.choices]:
            raise ValidationError(
                "'%s' is een ongeldige keuze. Kies uit %s of als het "
                "attribuut niet verplicht is kan het leeg gelaten worden." % (
                    self.data,
                    '/'.join([v for v, _ in self.choices]).lstrip('/')
                )
            )


class CustomSelectMultipleField(SelectMultipleField):
    def pre_validate(self, form):
        choices = [v for v, _ in self.choices]
        for value in self.data:
            if not value in choices:
                raise ValueError(
                    "'%s' voldoet niet aan het format. De tekst moet beginnen "
                    "met 'waterschapsverkiezingen voor' gevolgd door de naam "
                    "van het waterschap zonder 'Waterschap' of "
                    "'Hoogheemraadschap' voor de naam. In het geval dat er in "
                    "dit stembureau voor meerdere waterschappen gestemd kan "
                    "worden dan scheidt u deze met een puntkomma. De keuzes "
                    "bestaan uit: %s" % (value, ', '.join(choices))
                )


# This custom StringField prepends URLs with 'http://' if the string
# doesn't start with either 'http://' or 'https://'
class URLStringField(StringField):
    def process_formdata(self, valuelist):
        if valuelist[0]:
            value = valuelist[0].strip()
            if value:
                if (not value.startswith('http://') and
                        not value.startswith('https://')):
                    self.data = 'http://' + value
                else:
                    self.data = value


class DeleteUserForm(FlaskForm):
    hidden = HiddenField(
        name="user_id",
        id="user_id"
    )

    submit = SubmitField(
        'Verwijderen',
        render_kw={
            'class': 'btn btn-danger'
        }
    )

    submit_one = SubmitField(
        'Verwijderen uit deze gemeente',
        render_kw={
            'class': 'btn btn-danger'
        }
    )

    submit_all = SubmitField(
        'Verwijderen uit alle gemeenten',
        render_kw={
            'class': 'btn btn-danger'
        }
    )

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    submit = SubmitField(
        'Bevestig',
        render_kw={
            'class': 'btn btn-info'
        }
    )


class ResetPasswordForm(FlaskForm):
    # Use 'Wachtwoord' instead of 'password' as the variable
    # is used in a user-facing error message when the passwords
    # don't match and we want it to show a Dutch word instead of
    # English
    Wachtwoord = PasswordField(
        'Wachtwoord',
        validators=[DataRequired(), Length(min=12)]
    )
    Wachtwoord2 = PasswordField(
        'Herhaal wachtwoord',
        validators=[DataRequired(), EqualTo('Wachtwoord')]
    )
    submit = SubmitField(
        'Bevestig',
        render_kw={
            'class': 'btn btn-info'
        }
    )


class LoginForm(FlaskForm):
    email = StringField('E-mailadres', validators=[InputRequired(), Email()])
    Wachtwoord = PasswordField('Wachtwoord', validators=[InputRequired()])
    submit = SubmitField(
        'Inloggen',
        render_kw={
            'class': 'btn btn-info'
        }
    )

class Setup2faForm(FlaskForm):
    submit = SubmitField(
        'Kopieer token',
        render_kw={
            'class': 'btn btn-info',
            'onclick': 'return copySecret()'
        }
    )

class TwoFactorForm(FlaskForm):
    otp = StringField('Authenticator code', validators=[
                      InputRequired(), Length(min=6, max=6)])
    submit = SubmitField(
        'Verifiëren',
        render_kw={
            'class': 'btn btn-info'
        }
    )

class SignupForm(FlaskForm):
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    gemeente = SelectField('Gemeente', validators=[DataRequired()], choices=[])
    # We don't store the name in the database, but it is sent in the
    # logging email to the admins so they can verify if this user is
    # allowed access to the specified gemeente (especially useful when
    # a person doesn't use a gemeente email address, but e.g. a private
    # email address)
    naam_contactpersoon = StringField('Naam contactpersoon', validators=[Optional()])
    submit = SubmitField(
        'Vraag account aan',
        render_kw={
            'class': 'btn btn-info',
            'data-none-selected-text': ''
        }
    )


class GemeenteSelectionForm(FlaskForm):
    gemeente = SelectField('Gemeente', validators=[DataRequired()], choices=[])
    submit = SubmitField(
        'Selecteer gemeente',
        render_kw={
            'class': 'btn btn-info',
            'data-none-selected-text': ''
        }
    )


class FileUploadForm(FlaskForm):
    data_file = FileField(
        'Bestand',
        validators=[
            FileRequired(),
            FileAllowed(
                ['xls', 'xlsx', 'ods'],
                (
                    'Alleen Excel (.xls, .xslx) of OpenDocument (.ods) '
                    'spreadsheets zijn toegestaan.'
                )
            )
        ],
        render_kw={
            'class': 'filestyle upload-form',
            'data-buttonName': 'btn-info',
            'data-buttonText': 'Voeg bestand toe',
            'data-icon': 'false',
            'data-buttonBefore': 'true',
            'data-size': 'sm'
        }
    )
    submit = SubmitField(
        'Uploaden',
        render_kw={
            'class': 'btn btn-info'
        }
    )


class PubliceerForm(FlaskForm):
    submit = SubmitField(
        'Publiceer',
        render_kw={
            'class': 'btn btn-info'
        }
    )


# Check if the BAG value is correct (sometimes people use the
# Verblijfsobject ID or Pand ID instead of the Nummeraanduiding ID)
def valid_bag(form, field):
    bag_record = db_exec_one_optional(BAG, nummeraanduiding=field.data)
    if not bag_record:
        if db_exec_one_optional(BAG, object_id=field.data):
            raise ValidationError(
                'Het ingevulde nummer ({0}) blijkt een BAG Verblijfsobject ID te '
                'zijn. In dit veld moet het BAG Nummeraanduiding ID ingevuld '
                'worden.'.format(field.data)
            )
        elif len(db_exec_all(BAG, pandid=field.data)) > 0:
            raise ValidationError(
                'Het ingevulde nummer ({0}) blijkt een BAG Pand ID te zijn. In dit '
                'veld moet het BAG Nummeraanduiding ID ingevuld worden.'.format(field.data)
            )
        elif field.data == "0000000000000000":
            return
        else:
            raise ValidationError(
                'Het ingevulde nummer ({0}) kan niet gevonden worden in onze BAG '
                'database. Dit kan gebeuren als de BAG nummeraanduiding ID '
                'zeer recent is toegevoegd aan de BAG. Onze BAG database '
                'wordt eens per maand bijgewerkt. Het kan ook zijn dat het '
                'nummer onjuist is of verouderd. Gebruik '
                '<a href="https://bagviewer.kadaster.nl/" '
                'target="_blank">bagviewer.kadaster.nl</a> '
                'om het juiste BAG Nummeraanduiding ID te vinden. Als dit '
                'niet beschikbaar is vul dan \'0000000000000000\' (zestien '
                'keer het getal \'0\') in en voer het adres of andere '
                'verduidelijking van de locatie in het \'Extra '
                'adresaanduiding\'-veld in.'.format(field.data)
            )


# Checks if 'nee' or similar is entered in a text field where we don't allow
# that. See https://github.com/openstate/stembureaus/issues/65 for more info.
def no_no(form, field):
    if re.match(r'^\s*(nee|geen|-|/|_|niks)\s*$', str(field.data), re.IGNORECASE):
        raise ValidationError(
            'Vul geen \'nee\', \'geen\' en dergelijke in; laat dit veld in '
            'zo\'n geval leeg'
        )


# Require at least four decimals and a point in between the numbers
def min_four_decimals(form, field):
    if not re.match(r'^-?\d+\.\d{4,}', str(field.data)):
        raise ValidationError(
            'De cijfers in de Latitude en Longitude velden moeten met een '
            'punt (of komma) gescheiden worden en moeten minimaal 4 '
            'decimalen achter de punt hebben.'
        )


def latitude_range(form, field):
    if type(field.data) != float:
        raise ValidationError(
            'Ongeldig getal. Het getal mag enkel uit cijfers en één punt of '
            'komma bestaan, bv. 52.0775912'
        )

    min_four_decimals(form, field)

    if field.data > 50 and field.data < 54:
        return
    elif field.data > 12 and field.data < 12.4:
        return
    elif field.data > 17.4 and field.data < 17.7:
        return
    else:
        raise ValidationError(
            'De latitude moet tussen 50 en 54 (Europees Nederland), 12 en '
            '12.4 (Bonaire) of 17.4 en 17.7 (Saba en Sint Eustatius) liggen '
            'anders ligt uw stembureau niet in Nederland.'
        )


def longitude_range(form, field):
    if type(field.data) != float:
        raise ValidationError(
            'Ongeldig getal. Het getal mag enkel uit cijfers en één punt of '
            'komma bestaan, bv. 4.3166395'
        )

    min_four_decimals(form, field)

    if type(field.data) == float:
        if field.data > 3 and field.data < 8:
            return
        if field.data > -68.5 and field.data < -68:
            return
        if field.data > -63.3 and field.data < -62.9:
            return
        else:
            raise ValidationError(
                'De longitude moet tussen 3 en 8 (Europees Nederland), -68.5 '
                'en -68 (Bonaire) of -63.3 en -62.9 (Saba en Sint Eustatius) '
                'liggen anders ligt uw stembureau niet in Nederland.'
            )


def x_range(form, field):
    if type(field.data) == float:
        if field.data >= 0 and field.data < 300000:
            return
    raise ValidationError(
        'De x-waarde moet tussen 0 of 300000 liggen, anders ligt de '
        'coördinaat niet op het vasteland van Europees Nederland.'
    )


def y_range(form, field):
    if type(field.data) == float:
        if field.data >= 300000 and field.data < 620000:
            return
    raise ValidationError(
        'De y-waarde moet tussen 300000 of 620000 liggen, anders ligt de '
        'coördinaat niet op het vasteland van Europees Nederland.'
    )


class EditForm(FlaskForm):
    # Override validate function in order to check if at least latitude
    # and longitude or x and y are filled in.
    def validate(self):
        valid = True

        # If both latitude and longitude are present then always use those
        # values to calculate x and y. Otherwise use x and y to calculate
        # the latitude and longitude values.
        if self.latitude.data and self.longitude.data:
            # Only convert lat/long to x/y for Europees Nederland, because
            # Caribisch Nederland doesn't have x/y
            if self.latitude.data > 50 and self.longitude.data > 3:
                self.x.data, self.y.data = convert_latlong_to_xy(
                    self.latitude.data, self.longitude.data
                )
        elif self.x.data and self.y.data:
            self.latitude.data, self.longitude.data = convert_xy_to_latlong(
                self.x.data, self.y.data
            )

        if not FlaskForm.validate(self):
            valid = False

        # Stembureaus require a nummer and naam
        if not self.nummer_stembureau.data:
            self.nummer_stembureau.errors.append(
                'Vul het nummer van het stembureau in.'
            )
            valid = False
        if not self.naam_stembureau.data:
            self.naam_stembureau.errors.append(
                'Vul de naam van het stembureau in.'
            )
            valid = False

        if not self.bag_nummeraanduiding_id.data:
            self.adres_stembureau.errors.append(
                "Vul het adres van het stembureau in; zoek op straatnaam of "
                "postcode of BAG ID en selecteer het adres uit de lijst"
            )
            valid = False

        # If BAG ID 0000000000000000 we require Extra adresaanduiding
        if (self.bag_nummeraanduiding_id.data == "0000000000000000" and
                not self.extra_adresaanduiding.data):
            self.extra_adresaanduiding.errors.append(
                'Aangezien u \'0000000000000000\' in het \'bag '
                'nummeraanduiding id\'-veld heeft ingevuld moet u het adres of '
                'andere verduidelijking van de locatie van stembureau in dit '
                'veld invullen.'
            )
            valid = False

        # If BAG ID 0000000000000000 we require either lat and long or x and y to be filled in
        if (self.bag_nummeraanduiding_id.data == "0000000000000000" and
                not ((self.latitude.data and self.longitude.data) or
                (self.x.data and self.y.data))):
            self.latitude.errors.append(
                'Aangezien u \'0000000000000000\' in het \'bag '
                'nummeraanduiding id\'-veld heeft ingevuld moet u '
                'minimaal Latitude én Longitude of X én Y invullen, '
                'zodat de exacte locatie van het stembureau bekend is.'
            )
            self.longitude.errors.append(
                'Aangezien u \'0000000000000000\' in het \'bag '
                'nummeraanduiding id\'-veld heeft ingevuld moet u '
                'minimaal Latitude én Longitude of X én Y invullen, '
                'zodat de exacte locatie van het stembureau bekend is.'
            )
            self.x.errors.append(
                'Aangezien u \'0000000000000000\' in het \'bag '
                'nummeraanduiding id\'-veld heeft ingevuld moet u '
                'minimaal Latitude én Longitude of X én Y invullen, '
                'zodat de exacte locatie van het stembureau bekend is.'
            )
            self.y.errors.append(
                'Aangezien u \'0000000000000000\' in het \'bag '
                'nummeraanduiding id\'-veld heeft ingevuld moet u '
                'minimaal Latitude én Longitude of X én Y invullen, '
                'zodat de exacte locatie van het stembureau bekend is.'
            )
            valid = False

        if self.sluitingstijd.data:
            try:
                time = datetime.fromisoformat(self.sluitingstijd.data)
                if time.hour > 21 or time.hour == 21 and time.minute > 0:
                    self.sluitingstijd.errors.append(
                        'De sluitingstijd mag niet later zijn dan 21:00.'
                    )
                    valid = False
            except:
                pass # There is a separate RegEx validator for checking the ISO format

        return valid

    submit = SubmitField(
        'Opslaan',
        render_kw={
            'class': 'btn btn-info'
        }
    )
    submit_annuleren = SubmitField(
        'Annuleren',
        render_kw={
            'class': 'btn btn-info'
        }
    )
    submit_verwijderen = SubmitField(
        'Verwijderen',
        render_kw={
            'class': 'btn btn-danger'
        }
    )

    nummer_stembureau = IntegerField(
        'Nummer stembureau',
        description=(
            'Een stembureau is gevestigd in een stemlokaal en elk stembureau '
            'heeft een eigen nummer. Sommige stemlokalen hebben meerdere '
            'stembureaus. Elk stembureau moet apart ingevoerd worden ook al '
            'is de locatie (het stemlokaal) hetzelfde aangezien elk '
            'stembureau een ander nummer heeft.'
            #'<br>'
            #'<br>'
            #'Als een stembureau meerdere dagen open is dan moet deze voor '
            #'elke dag een ander stembureaunummer hebben. Elk '
            #'stembureau(nummer) moet dus apart ingevoerd worden.'
            '<br>'
            '<br>'
            '<b>Format:</b> cijfers'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 517'
        ),
        validators=[
            DataRequired(),
            NumberRange(min=1, max=2000000000)
        ],
        render_kw={
            'placeholder': 'bv. 517'
        }
    )

    naam_stembureau = StringField(
        'Naam stembureau',
        description=(
            'De naam van het stembureau.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Stadhuis'
        ),
        validators=[
            DataRequired(),
        ],
        render_kw={
            'placeholder': 'bv. Stadhuis'
        }
    )

    type_stembureau = CustomSelectField(
        'Type stembureau',
        description=(
            'Kies \'regulier\' als dit een normaal stembureau betreft. Kies '
            '\'bijzonder\' als het stembureau afwijkende openingstijden heeft. '
            'Kies \'mobiel\' als het stembureau meerdere locaties heeft.'
            '<br>'
            '<br>'
            '<b>Format:</b> keuze uit:'
            '<ul>'
            '  <li>regulier</li>'
            '  <li>bijzonder</li>'
            '  <li>mobiel</li>'
            '</ul>'
            '<b>Voorbeeld:</b> regulier'
        ),
        choices=[
            (
                'regulier',
                'regulier'
            ),
            (
                'bijzonder',
                'bijzonder'
            ),
            (
                'mobiel',
                'mobiel'
            )
        ],
        validators=[
            DataRequired(),
        ],
        render_kw={
            'class': 'form-select',
            'data-none-selected-text': (
                'Selecteer het type stembureau'
            )
        }
    )

    website_locatie = URLStringField(
        'Website locatie',
        description=(
            'Website van de locatie van het stembureau, indien '
            'aanwezig.'
            '<br>'
            '<br>'
            '<b>Format:</b> Volledige URL (dit begint met \'http://\' of '
            '\'https://\')'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> https://www.denhaag.nl/nl'
            '/contact-met-de-gemeente/stadhuis-den-haag/'
        ),
        validators=[
            Optional(),
            URL(
                message='Ongeldige URL. Correct is bv. '
                '\'https://www.voorbeeld.nl\''
            )
        ],
        render_kw={
            'placeholder': 'bv. https://www.denhaag.nl/nl'
            '/contact-met-de-gemeente/stadhuis-den-haag/'
        }
    )

    bag_nummeraanduiding_id = HiddenField(
        'BAG Nummeraanduiding ID',
        description=(
            'BAG Nummeraanduiding ID, vindbaar door het adres van het '
            'stembureau op <a href="https://bagviewer.kadaster.nl/" '
            'target="_blank" rel="noopener">bagviewer.kadaster.nl</a> in te '
            'voeren en rechts onder het kopje \'Nummeraanduiding\' te kijken.'
            '<br>'
            '<br>'
            'Vermeld voor mobiele stembureaus of locaties zonder BAG '
            'Nummeraanduiding ID het dichtstbijzijnde BAG '
            'Nummeraanduiding ID en gebruik eventueel het \'Extra '
            'adresaanduiding\'-veld om de locatie van het stembureau te '
            'beschrijven. NB: de precieze locatie geeft u aan met de '
            '\'Latitude\' en \'Longitude\'-velden of met de \'X\' en '
            '\'Y\'-velden.'
            '<br>'
            '<br>'
            'Bonaire, Sint Eustatius en Saba moeten hier \'0000000000000000\' '
            '(zestien keer het getal \'0\') invullen. Het adres van het '
            'stembureau moet vervolgens in het \'Extra adresaanduiding\'-veld '
            'ingevuld worden.'
            '<br>'
            '<br>'
            '<b>Format:</b> cijfers'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 0518200000747446'
        ),
        validators=[
            DataRequired(),
            Length(
                min=16,
                max=16,
                message="Dit veld moet precies 16 cijfers bevatten."
            ),
            Regexp(
                '^[0-9]+$',
                message='Elk karakter moet een nummer tussen 0 en 9 zijn.'
            ),
            valid_bag
        ],
        render_kw={
            'placeholder': 'bv. 0518200000747446'
        }
    )

    adres_stembureau = StringField(
        'Adres stembureau',
        description=(
            'Voer de <b>straatnaam inclusief huisnummer</b> van het '
            'stembureau in en eventueel een '
            '<b>huisletter / huisnummertoevoeging</b> en, gescheiden met een '
            'komma, de <b>plaatsnaam</b>. U kunt ook zoeken op '
            '<b>postcode</b> en huisnummer. En u kunt ook zoeken op '
            '<b>BAG Nummeraanduiding ID</b>, vindbaar door het adres van het '
            'stembureau op <a href="https://bagviewer.kadaster.nl/" '
            'target="_blank" rel="noopener">bagviewer.kadaster.nl</a> in te '
            'voeren en rechts onder het kopje \'Nummeraanduiding\' te kijken.'
            '<br>'
            '<br>'
            'Het ingevoerde adres wordt '
            'automatisch opgezocht en in een lijst getoond waarin ook de '
            '16-cijferige BAG Nummeraanduiding ID te zien is dat uniek is '
            'voor het adres. Klik op het adres dat hoort bij het stembureau. '
            'De coördinaten van het adres worden automatisch ingevuld in de '
            'Latitude/Longitude- en X/Y-velden . Kijk op de kaart hieronder '
            'of de locatie klopt.'
            '<br>'
            '<br>'
            'Vermeld voor mobiele stembureaus die vlakbij een gebouw staan of '
            'locaties zonder BAG Nummeraanduiding ID het BAG Nummeraanduiding '
            'ID van het dichtstbijzijnde gebouw en gebruik eventueel het '
            '\'Extra adresaanduiding\'-veld om de locatie van stembureau te '
            'beschrijven. Mocht een (mobiel) stembureau niet in de buurt van '
            'een gebouw staan, voer dan \'0000000000000000\' (zestien keer het '
            'getal \'0\') in; \'Extra adresaanduiding\'-attribuut is dan '
            'verplicht. NB: de precieze locatie geeft u aan met de '
            '\'Latitude\' en \'Longitude\'-velden óf met de \'X\' en '
            '\'Y\'-velden.'
            '<br>'
            '<br>'
            'Bonaire, Sint Eustatius en Saba moeten hier \'0000000000000000\' '
            '(zestien keer het getal \'0\') invullen. Het adres van het '
            'stembureau moet vervolgens in het \'Extra adresaanduiding\'-veld '
            'ingevuld worden.'
            '<br>'
            '<br>'
            '<b>Format:</b>'
            '<ul>'
            '<li>&lt;straatnaam&gt; &lt;huisnummer&gt;[huisletter]-[huisnummertoevoeging], &lt;woonplaats&gt;</li>'
            '<li>&lt;postcode&gt; &lt;huisnummer&gt;[huisletter]-[huisnummertoevoeging]</li>'
            '<li>&lt;BAG Nummeraanduiding ID&gt;</li>'
            '</ul>'
            '<br>'
            '<br>'
            '<b>Voorbeelden:</b>'
            '<ul>'
            '<li>Spui 70, \'s-Gravenhage</li>'
            '<li>2511BT 70</li>'
            '<li>0518200000747446</li>'
            '</ul>'
        ),
        validators=[
            Optional(),
        ],
        render_kw={
            'placeholder': 'Straatnaam óf Postcode óf BAG ID'
        }
    )

    extra_adresaanduiding = StringField(
        'Extra adresaanduiding',
        description=(
            'Eventuele extra informatie over de locatie van het '
            'stembureau. Bv. \'Ingang aan achterkant gebouw\' of '
            '\'Mobiel stembureau op het midden van het plein\'.'
            '<br>'
            '<br>'
            'Bonaire, Sint Eustatius en Saba moeten hier het adres van het '
            'stembureau invullen.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst; als er geen extra informatie is, laat dit '
            'veld dan leeg (\'nee\' e.d. worden automatisch verwijderd).'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Ingang aan achterkant gebouw'
        ),
        validators=[
            Optional(),
            no_no
        ],
        render_kw={
            'placeholder': 'bv. Ingang aan achterkant gebouw'
        }
    )

    latitude = CommaDotFloatField(
        'Latitude',
        description=(
            'Breedtegraad met minimaal 4 decimalen.'
            '<br>'
            '<br>'
            'Als u de latitude van het stembureau niet weet dan '
            'kunt u dit vinden via <a href="https://www.openstreetmap.org/" '
            'target="_blank" rel="noopener">openstreetmap.org</a>. Zoom in op '
            'het stembureau, klik op de juiste locatie met de '
            'rechtermuisknop en selecteer \'Show address\'/\'Toon adres\'. De '
            'latitude en longitude (in die volgorde) staan nu linksboven in '
            'de zoekbalk.'
            '<br>'
            '<br>'
            '<b>Format:</b> graden in DD.dddd notatie'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 52.0775912'
        ),
        validators=[
            Optional(),
            latitude_range
        ],
        render_kw={
            'placeholder': 'bv. 52.0775912'
        }
    )

    longitude = CommaDotFloatField(
        'Longitude',
        description=(
            'Lengtegraad met minimaal 4 decimalen.'
            '<br>'
            '<br>'
            'Als u de longitude van het stembureau niet weet dan '
            'kunt u dit vinden via <a href="https://www.openstreetmap.org/" '
            'target="_blank" rel="noopener">openstreetmap.org</a>. Zoom in op '
            'het stembureau, klik op de juiste locatie met de '
            'rechtermuisknop en selecteer \'Show address\'/\'Toon adres\'. De '
            'latitude en longitude (in die volgorde) staan nu linksboven in '
            'de zoekbalk.'
            '<br>'
            '<br>'
            '<b>Format:</b> graden in DD.dddd notatie'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 4.3166395'
        ),
        validators=[
            Optional(),
            longitude_range
        ],
        render_kw={
            'placeholder': 'bv. 4.3166395'
        }
    )

    x = CommaDotFloatField(
        'X',
        description=(
            'Rijksdriehoekscoördinaat x (minimaal in meters, decimalen ook '
            'toegestaan).'
            '<br>'
            '<br>'
            '<b>Format:</b> getal tussen 0 en 300000'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 81611'
        ),
        validators=[
            Optional(),
            x_range
        ],
        render_kw={
            'placeholder': 'bv. 81611'
        }
    )

    y = CommaDotFloatField(
        'Y',
        description=(
            'Rijksdriehoekscoördinaat y (minimaal in meters, decimalen ook '
            'toegestaan).'
            '<br>'
            '<br>'
            '<b>Format:</b> getal tussen 300000 en 620000'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 454909'
        ),
        validators=[
            Optional(),
            y_range
        ],
        render_kw={
            'placeholder': 'bv. 454909'
        }
    )

    openingstijd = StringField(
        'Openingstijd',
        description=(
            'In sommige gevallen heeft een stembureau meerdere openingstijden, '
            'bijvoorbeeld een mobiel stembureau of een stembureau dat '
            '‘s middags even dicht is. In zulke gevallen moeten alle '
            'openingstijden als aparte stembureaus ingevoerd worden.'
            '<br>'
            '<br>'
            '<b>Format:</b> YYYY-MM-DDTHH:MM:SS'
            '<br>'
            '<br>'
            f'<b>Voorbeeld:</b> {current_app.config["ELECTION_DATE"]}T07:30:00'
        ),
        default=f'{current_app.config["ELECTION_DATE"]}T07:30:00',
        validators=[
            DataRequired(),
            Regexp(
                r'^' + current_app.config["ELECTION_DATE"] + r'T\d{2}:\d{2}:\d{2}$',
                message=(
                    'Dit veld is verkeerd ingevuld. Het hoort ingevuld te '
                    f'worden zoals bv. \'{current_app.config["ELECTION_DATE"]}T07:30:00\'.'
                )
            )
        ],
        render_kw={
            'placeholder': f'bv. {current_app.config["ELECTION_DATE"]}T07:30:00'
        }
    )

    sluitingstijd = StringField(
        'Sluitingstijd',
        description=(
            'In sommige gevallen heeft een stembureau meerdere openingstijden, '
            'bijvoorbeeld een mobiel stembureau of een stembureau dat '
            '‘s middags even dicht is. In zulke gevallen moeten alle '
            'openingstijden als aparte stembureaus ingevoerd worden.'
            '<br>'
            '<br>'
            '<b>Format:</b> YYYY-MM-DDTHH:MM:SS'
            '<br>'
            '<br>'
            f'<b>Voorbeeld:</b> {current_app.config["ELECTION_DATE"]}T21:00:00'
        ),
        default=f'{current_app.config["ELECTION_DATE"]}T21:00:00',
        validators=[
            DataRequired(),
            Regexp(
                r'^' + current_app.config["ELECTION_DATE"] + r'T\d{2}:\d{2}:\d{2}$',
                message=(
                    'Dit veld is verkeerd ingevuld. Het hoort ingevuld te '
                    f'worden zoals bv. \'{current_app.config["ELECTION_DATE"]}T21:00:00\'.'
                )
            )
        ],
        render_kw={
            'placeholder': f'bv. {current_app.config["ELECTION_DATE"]}T21:00:00'
        }
    )

    tellocatie = CustomSelectField(
        'Tellocatie',
        description=(
            'Is deze locatie ook een locatie waar de stemmen worden geteld?'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er op deze locatie ook stemmen '
            'worden geteld. Vul \'nee\' in als dat niet zo is. '
            'Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    contactgegevens_gemeente = StringField(
        'Contactgegevens gemeente',
        description=(
            '&lt;afdeling/functie&gt;: De afdeling of specifieke functie '
            'binnen de gemeente die zich bezig houdt met de stembureaus; '
            'i.v.m. verduurzaming bij voorkeur dus niet de '
            'naam/contactgegevens van een persoon.'
            '<br>'
            '<br>'
            '<b>Format:</b> &lt;afdeling/functie&gt;, &lt;e-mailadres en/of '
            'telefoonnummer en/of postadres&gt;'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Unit Verkiezingen, verkiezingen@denhaag.nl '
            '070-3534488 Gemeente Den Haag Publiekszaken/Unit Verkiezingen '
            'Postbus 84008 2508 AA Den Haag'
        ),
        validators=[
            DataRequired()
        ],
        render_kw={
            'placeholder': 'bv. Unit Verkiezingen, verkiezingen@denhaag.nl '
            '070-3534488 Gemeente Den Haag Publiekszaken/Unit Verkiezingen '
            'Postbus 84008 2508 AA Den Haag'
        }
    )

    verkiezingswebsite_gemeente = URLStringField(
        'Verkiezingswebsite gemeente',
        description=(
            'URL van de gemeentewebsite met data of informatie over de '
            'stembureaus (of verkiezing).'
            '<br>'
            '<br>'
            '<b>Format:</b> Volledige URL (dit begint met \'http://\' of '
            '\'https://\')'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <span style="word-break: break-word;">https://www.denhaag.nl/nl/verkiezingen/</span>'
        ),
        validators=[
            DataRequired(),
            URL(
                message='Ongeldige URL. Correct is bv. '
                '\'https://www.denhaag.nl/nl/verkiezingen/\''
            )
        ],
        render_kw={
            'placeholder': 'bv. https://www.denhaag.nl/nl/verkiezingen/'
        }
    )

    # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field to
    # the form
    if [x for x in current_app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
        verkiezingen = CustomSelectMultipleField(
            'Verkiezingen',
            description=(
                'In het geval van waterschapsverkiezingen en verkiezingen van '
                'stadsdeelcommissies / gebiedscommissies / wijkraden kan er in '
                'sommige gemeenten niet in elk stembureau voor alle verkiezingen '
                'gestemd worden. Door Amsterdam lopen er bijvoorbeeld drie '
                'waterschappen en er kan enkel voor een waterschap gestemd worden '
                'bij stembureaus die in het gebied van het waterschap liggen. '
                'Alle gemeenten vragen we daarom in het geval van deze '
                'verkiezingen per stembureau specifiek aan te geven voor welke '
                'waterschappen / stadsdeelcommissies / gebiedscommissies / '
                'wijkraden er gestemd kunnen worden. Ook als er überhaupt maar '
                'één keuze is (bv. als er in de hele gemeente maar voor één '
                'waterschap gekozen kan worden) en ook als er in de gemeente bij '
                'elk stembureau voor alle verkiezingen gestemd kan worden.'
                '<br>'
                '<br>'
                'In het geval dat er in dit stembureau voor meerdere '
                'waterschappen / stadsdeelcommissies / gebiedscommissies / '
                'wijkraden gestemd kan worden dan scheidt u deze met een '
                'puntkomma, bv.: waterschapsverkiezingen voor Delfland; '
                'waterschapsverkiezingen voor Rijnland'
                '<br>'
                '<br>'
                '<b>Format:</b> keuze uit:'
                '<ul>'
                '  <li>waterschapsverkiezingen voor &lt;naam van waterschap '
                'zonder \'Waterschap\' of \'Hoogheemraadschap\' voor de naam&gt;</li>'
                '  <li>verkiezingen &lt;gebiedscommissies / wijkraden&gt; '
                '&lt;naam van gebiedscommissies / wijkraden&gt;</li>'
                '  <li>verkiezingen stadsdeelcommissie &lt;naam van '
                'stadsdeelcommissie&gt;</li>'
                '</ul>'
                '<br>'
                '<b>Voorbeeld:</b> waterschapsverkiezingen voor Delfland'
            ),
            choices=[
                (
                    'waterschapsverkiezingen voor Noorderzijlvest',
                    'Noorderzijlvest'
                ),
                (
                    'waterschapsverkiezingen voor Fryslân',
                    'Fryslân'
                ),
                (
                    'waterschapsverkiezingen voor Hunze en Aa\'s',
                    'Hunze en Aa\'s'
                ),
                (
                    'waterschapsverkiezingen voor Drents Overijsselse Delta',
                    'Drents Overijsselse Delta'
                ),
                (
                    'waterschapsverkiezingen voor Vechtstromen',
                    'Vechtstromen'
                ),
                (
                    'waterschapsverkiezingen voor Vallei en Veluwe',
                    'Vallei en Veluwe'
                ),
                (
                    'waterschapsverkiezingen voor Rijn en IJssel',
                    'Rijn en IJssel'
                ),
                (
                    'waterschapsverkiezingen voor De Stichtse Rijnlanden',
                    'De Stichtse Rijnlanden'
                ),
                (
                    'waterschapsverkiezingen voor Amstel, Gooi en Vecht',
                    'Amstel, Gooi en Vecht'
                ),
                (
                    'waterschapsverkiezingen voor Hollands Noorderkwartier',
                    'Hollands Noorderkwartier'
                ),
                (
                    'waterschapsverkiezingen voor Rijnland',
                    'Rijnland'
                ),
                (
                    'waterschapsverkiezingen voor Delfland',
                    'Delfland'
                ),
                (
                    'waterschapsverkiezingen voor Schieland en de Krimpenerwaard',
                    'Schieland en de Krimpenerwaard'
                ),
                (
                    'waterschapsverkiezingen voor Rivierenland',
                    'Rivierenland'
                ),
                (
                    'waterschapsverkiezingen voor Hollandse Delta',
                    'Hollandse Delta'
                ),
                (
                    'waterschapsverkiezingen voor Scheldestromen',
                    'Scheldestromen'
                ),
                (
                    'waterschapsverkiezingen voor Brabantse Delta',
                    'Brabantse Delta'
                ),
                (
                    'waterschapsverkiezingen voor De Dommel',
                    'De Dommel'
                ),
                (
                    'waterschapsverkiezingen voor Aa en Maas',
                    'Aa en Maas'
                ),
                (
                    'waterschapsverkiezingen voor Limburg',
                    'Limburg'
                ),
                (
                    'waterschapsverkiezingen voor Zuiderzeeland',
                    'Zuiderzeeland'
                )
            ],
            validators=[
                Optional(),
            ],
            render_kw={
                'data-none-selected-text': (
                    'Selecteer één of meerdere waterschappen'
                )
            }
        )

    toegankelijk_voor_mensen_met_een_lichamelijke_beperking = CustomSelectField(
        'Toegankelijk voor mensen met een lichamelijke beperking',
        description=(
            'Is het stembureau toegankelijk voor mensen met een lichamelijke beperking? '
            'Voor meer informatie, <a '
            'href="https://www.rijksoverheid.nl/onderwerpen/verkiezingen/'
            'verkiezingentoolkit/toegankelijkheid-verkiezingen" target="_blank" '
            'rel="noopener">zie deze pagina op rijksoverheid.nl</a>.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als het stembureau toegankelijk is '
            'voor mensen met een lichamelijke beperking. Vul \'nee\' in als dat '
            'niet zo is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            DataRequired()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    toegankelijke_ov_halte = CustomSelectField(
        'Toegankelijke ov-halte',
        description=(
            'Is er een toegankelijke ov-halte in de buurt en is de logische '
            'route vanaf deze ov-halte naar het stembureau toegankelijk?'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er een toegankelijke ov-halte '
            'in de buurt is. Vul \'nee\' in als dat niet zo is. Laat het veld '
            'leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    toilet = CustomSelectField(
        'Toilet',
        description=(
            'Is er een toilet, genderneutraal toilet of toegankelijk toilet '
            'aanwezig? Als er zowel een \'toilet\' en/of een \'genderneutraal '
            'toilet\' aanwezig zijn én er ook een \'toegankelijk toilet\' '
            'aanwezig is vul dan \'toegankelijk toilet\' in. Als er zowel een '
            '\'toilet\' en een \'genderneutraal toilet\' aanwezig zijn vul '
            'dan \'genderneutraal toilet\' in.'
            '<br>'
            '<br>'
            '<b>Format:</b> keuze uit:'
            '<ul>'
            '  <li>ja</li>'
            '  <li>ja, genderneutraal toilet</li>'
            '  <li>ja, toegankelijk toilet</li>'
            '  <li>nee</li>'
            '</ul>'
            '<b>Voorbeeld:</b> ja, toegankelijk toilet'
        ),
        choices=[('', ''), ('ja', 'ja'), ('ja, genderneutraal toilet', 'ja, genderneutraal toilet'), ('ja, toegankelijk toilet', 'ja, toegankelijk toilet'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    host = CustomSelectField(
        'Host',
        description=(
            'Is er iemand aanwezig die kiezers ontvangt en kan helpen?'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er en host aanwezig is. Vul '
            '\'nee\' in als dat niet zo is. Laat het veld leeg als het '
            'onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    geleidelijnen = CustomSelectField(
        'Geleidelijnen',
        description=(
            'Zijn er geleidelijnen aanwezig buiten en/of binnen het stembureau '
            'voor mensen met een visuele beperking?'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'buiten en binnen\' in als er geleidelijnen '
            'buiten en binnen het stembureau aanwezig zijn. Vul \'buiten\' in '
            'als deze enkel buiten aanwezig zijn. Vul \'binnen\' in als deze '
            'enkel binnen aanwezig zijn. Vul \'nee\' in als er geen '
            'geleidelijnen zijn. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> buiten en binnen'
        ),
        choices=[('', ''), ('buiten en binnen', 'buiten en binnen'), ('buiten', 'buiten'), ('binnen', 'binnen'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    stemmal_met_audio_ondersteuning = CustomSelectField(
        'Stemmal met audio-ondersteuning',
        description=(
            'Is er een stemmal met audio-ondersteuning (stembox/soundbox) '
            'aanwezig voor mensen met een visuele beperking of mensen die '
            'moeite hebben met lezen? Voor meer informatie, zie: '
            '<a href="https://www.oogvereniging.nl/leven-met/stemmen-met-een-oogaandoening/#stemmal" target="_blank">oogvereniging.nl</a>, '
            '<a href="https://stemmal.nl/" target="_blank">stemmal.nl</a> '
            'en <a href="https://www.stembox.nl/" target="_blank">stembox.nl</a>.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er een stemmal met '
            'audio-ondersteuning (stembox/soundbox) aanwezig is. Vul \'nee\' '
            'in als dat niet zo is. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    kandidatenlijst_in_braille = CustomSelectField(
        'Kandidatenlijst in braille',
        description=(
            'Is er een kandidatenlijst in braille aanwezig voor mensen met '
            'een visuele beperking?'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er een kandidatenlijst in '
            'braille aanwezig is. Vul \'nee\' in als dat niet zo is. Laat het '
            'veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    kandidatenlijst_met_grote_letters = CustomSelectField(
        'Kandidatenlijst met grote letters',
        description=(
            'Is er een kandidatenlijst met grote letters aanwezig voor mensen '
            'met een visuele beperking? NB: niet te verwarren met de '
            '\'vergrote kandidatenlijst\' die in elk stembureau verplicht '
            'aanwezig is.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er een kandidatenlijst met '
            'grote letters aanwezig is. Vul \'nee\' in als dat niet zo is. '
            'Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    gebarentolk_ngt = CustomSelectField(
        'Gebarentolk (NGT)',
        description=(
            'Is er een gebarentolk op locatie in het stembureau of op afstand '
            '(via videobellen) aanwezig die de Nederlandse Gebarentaal (NGT) '
            'beheerst? Als de gebarentolk niet de hele dag aanwezig is, '
            'vermeldt dan gedurende welke periode(n) deze precies aanwezig is in '
            'het \'Extra toegankelijkheidsinformatie\'-attribuut.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'op locatie\' in als de gebarentolk fysiek '
            'in het stembureau aanwezig is. Vul \'op afstand\' in als de '
            'gebarentolk op afstand (via videobellen) aanwezig is. Vul '
            '\'nee\' in als er geen gebarentolk aanwezig is. Laat het veld '
            'leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> op locatie'
        ),
        choices=[
            ('', ''),
            ('op locatie', 'op locatie'),
            ('op afstand', 'op afstand'),
            ('nee', 'nee')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    gebarentalig_stembureaulid_ngt = CustomSelectField(
        'Gebarentalig stembureaulid (NGT)',
        description=(
            'Is er een stembureaulid aanwezig die de Nederlandse Gebarentaal (NGT) beheerst?'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er een gebarentalig '
            'stembureaulid  aanwezig is. Vul \'nee\' in als dat niet zo is. '
            'Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    akoestiek_geschikt_voor_slechthorenden = CustomSelectField(
        'Akoestiek geschikt voor slechthorenden',
        description=(
            'Is de akoestiek van het stembureau geschikt voor '
            'slechthorenden? Voor meer informatie, zie <a '
            'href="https://bk.nijsnet.nl/d_ontwerpregels/40_Slechthorenden" '
            'target="_blank" rel="noopener">deze website</a>.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als de akoestiek in het stembureau '
            'geschikt is voor slechthorenden. Vul \'nee\' in als dat niet zo is. '
            'Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional(),
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    prikkelarm = CustomSelectField(
        'Prikkelarm',
        description=(
            'Dit stembureau is zo ingericht dat er weinig prikkels zijn.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als dit stembureau prikkelarm is. '
            'Vul \'nee\' in als dat niet zo is. Laat het veld leeg als het '
            'onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    prokkelduo = CustomSelectField(
        'Prokkelduo',
        description=(
            'Is er een prokkelduo aanwezig op dit stembureau? Een prokkelduo '
            'bestaat uit twee vrijwilligers, één met een (licht) '
            'verstandelijke beperking en één zonder, die samen verschillende '
            'taken op het stembureau uitvoeren. Voor meer informatie, zie: '
            '<a href="https://www.prokkel.nl/inclusieve-stembureaus/" '
            'target="_blank">https://www.prokkel.nl/inclusieve-stembureaus/</a>'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul \'ja\' in als er in dit stembureau een '
            'prokkelduo aanwezig is. Vul \'nee\' in als dat niet zo is. Laat '
            'het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> ja'
        ),
        choices=[('', ''), ('ja', 'ja'), ('nee', 'nee')],
        validators=[
            Optional()
        ],
        render_kw={
            'data-none-selected-text': ''
        }
    )

    extra_toegankelijkheidsinformatie = StringField(
        'Extra toegankelijkheidsinformatie',
        description=(
            'Eventuele extra informatie over de toegankelijkheid van dit '
            'stembureau. Zie ook de voorbeelden.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst; als er geen extra informatie is, laat dit '
            'veld dan leeg (\'nee\' e.d. worden automatisch verwijderd). NB: '
            'een leesloep is verplicht op elk stembureau en moet hier dus '
            'niet vermeld worden.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Dit stembureau is ingericht voor kwetsbare '
            'mensen, stembureau is volledig toegankelijk voor mensen met een '
            'lichamelijke beperking er is echter geen '
            'gehandicaptenparkeerplaats, gebarentolk op locatie (NGT) is '
            'aanwezig van 10:00-12:00 en 16:00-18:00, oefenstembureau'
        ),
        validators=[
            Optional(),
            no_no
        ],
        render_kw={
            'placeholder': 'bv. Dit stembureau is ingericht voor kwetsbare '
            'mensen, stembureau is volledig toegankelijk voor mensen met een '
            'lichamelijke beperking er is echter geen '
            'gehandicaptenparkeerplaats, gebarentolk op locatie (NGT) is '
            'aanwezig van 10:00-12:00 en 16:00-18:00, oefenstembureau'
        }
    )

    overige_informatie = StringField(
        'Overige informatie',
        description=(
            'Eventuele overige informatie over dit stembureau.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst; als er geen extra informatie is, laat dit '
            'veld dan leeg (\'nee\' e.d. worden automatisch verwijderd).'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b>'
        ),
        validators=[
            Optional(),
            no_no
        ]
    )
