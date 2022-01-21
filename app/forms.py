from app import app
from app.models import BAG
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import (
    ValidationError, DataRequired, Optional, Email, EqualTo, Length, URL,
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
                raise ValueError(self.gettext('Not a valid float value'))


# The default pre_validate of SelectField only warned that a value is not
# valid without specifying why it was not valid. This message shows exactly
# which values can be used.
class CustomSelectField(SelectField):
    def pre_validate(self, form):
        if not self.data in [v for v, _ in self.choices]:
            raise ValueError(
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
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    Wachtwoord = PasswordField('Wachtwoord', validators=[DataRequired()])
    submit = SubmitField(
        'Inloggen',
        render_kw={
            'class': 'btn btn-info'
        }
    )


class GemeenteSelectionForm(FlaskForm):
    gemeente = SelectField('Gemeente', validators=[DataRequired()], choices=[])
    submit = SubmitField(
        'Selecteer gemeente',
        render_kw={
            'class': 'btn btn-info selectpicker',
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
    bag_record = BAG.query.filter_by(nummeraanduiding=field.data).first()
    if not bag_record:
        if BAG.query.filter_by(object_id=field.data).first():
            raise ValidationError(
                'Het ingevulde nummer blijkt een BAG Verblijfsobject ID te '
                'zijn. In dit veld moet het BAG Nummeraanduiding ID ingevuld '
                'worden.'
            )
        elif BAG.query.filter_by(pandid=field.data).first():
            raise ValidationError(
                'Het ingevulde nummer blijkt een BAG Pand ID te zijn. In dit '
                'veld moet het BAG Nummeraanduiding ID ingevuld worden.'
            )
        elif field.data == "0000000000000000":
            return
        else:
            raise ValidationError(
                'Het ingevulde nummer kan niet gevonden worden in onze BAG '
                'database. Dit kan gebeuren als de BAG nummeraanduiding ID '
                'zeer recent is toegevoegd aan de BAG. Onze BAG database '
                'wordt eens per maand bijgewerkt. Het kan ook zijn dat het '
                'nummer onjuist is of verouderd. Gebruik '
                'https://bagviewer.kadaster.nl/ om het juiste BAG '
                'Nummeraanduiding ID te vinden. Als dit niet beschikbaar is '
                'vul dan \'0000000000000000\' (zestien keer het getal \'0\') in '
                'en voer het adres of andere verduidelijking van de locatie '
                'in het \'Extra adresaanduiding\'-veld in.'
            )


# Require at least four decimals and a point in between the numbers
def min_four_decimals(form, field):
    if not re.match('^-?\d+\.\d{4,}', str(field.data)):
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
                "U heeft niet op een adres uit de lijst geklikt"
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

        # Require that at least one relevant openingstijden field is
        # filled in for a stembureau
        if not (self.openingstijden_14_03_2022.data
                or self.openingstijden_15_03_2022.data
                or self.openingstijden_16_03_2022.data):
            error_text_one = (
                "Een stembureau moet op minimaal één van deze dagen open "
                "zijn"
            )
            self.openingstijden_14_03_2022.errors.append(error_text_one)
            self.openingstijden_15_03_2022.errors.append(error_text_one)
            self.openingstijden_16_03_2022.errors.append(error_text_one)
            valid = False

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
            '/bestuur-en-organisatie/contact-met-de-gemeente'
            '/stadhuis-den-haag.htm'
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
            '/bestuur-en-organisatie/contact-met-de-gemeente'
            '/stadhuis-den-haag.htm'
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
            '<b>huisletter/huisnummertoevoeging</b> en, gescheiden met een '
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
            'Vermeld voor mobiele stembureaus of locaties zonder adres het '
            'dichtstbijzijnde adres en gebruik eventueel het \'Extra '
            'adresaanduiding\'-veld om de locatie van het stembureau te '
            'beschrijven. NB: de precieze locatie geeft u dan aan met de '
            '\'Latitude\' en \'Longitude\'-velden óf met de \'X\' en '
            '\'Y\'-velden.'
            '<br>'
            '<br>'
            #'Bonaire, Sint Eustatius en Saba moeten hier \'0000000000000000\' '
            #'(zestien keer het getal \'0\') invullen. Het adres van het '
            #'stembureau moet vervolgens in het \'Extra adresaanduiding\'-veld '
            #'ingevuld worden.'
            #'<br>'
            #'<br>'
            '<b>Format:</b>'
            '<ul>'
            '<li>&lt;straatnaam&gt; &lt;huisnummer&gt;[huisletter]-[huisnummertoevoeging], &lt;woonplaats&gt;</li>'
            '<li>&lt;postcode&gt;</li>'
            '<li>&lt;BAG Nummeraanduiding ID&gt;</li>'
            '</ul>'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b>'
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
            'placeholder': 'bv. Spui 70, \'s-Gravenhage'
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
            'Sommige stembureaus zijn niet open voor algemeen publiek '
            'vanwege coronamaatregelen. Bijvoorbeeld een '
            'stembureau in een verzorgingshuis. Geef dat in dit veld '
            'aan door exact de tekst \'Niet open voor algemeen '
            'publiek\' in te voeren.'
            '<br>'
            '<br>'
            'Bonaire, Sint Eustatius en Saba moeten hier het adres van het '
            'stembureau invullen.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> \'Niet open voor algemeen publiek\' of \'Ingang aan achterkant gebouw\''
        ),
        validators=[
            Optional(),
        ],
        render_kw={
            'placeholder': 'bv. \'Niet open voor algemeen publiek\''
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

    openingstijden_14_03_2022 = StringField(
        'Openingstijden 14-03-2022',
        description=(
            'Sommige gemeenten werken met mobiele stembureaus die gedurende '
            'de dag op verschillende locaties staan. Voor mobiele stembureaus '
            'moet voor elke locatie een nieuw \'stembureau\' aangemaakt worden '
            '(zodat de locatie en openingstijden apart worden opgeslagen).'
            '<br>'
            '<br>'
            '<b>Format:</b> YYYY-MM-DDTHH:MM:SS tot YYYY-MM-DDTHH:MM:SS'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 2022-03-14T07:30:00 tot 2022-03-14T21:00:00'
        ),
        validators=[
            Optional(),
            Regexp(
                (
                    '^2022-03-14T\d{2}:\d{2}:\d{2} tot '
                    '2022-03-14T\d{2}:\d{2}:\d{2}$'
                ),
                message=(
                    'Dit veld hoort ingevuld te worden zoals '
                    '\'2022-03-14T07:30:00 tot 2022-03-14T21:00:00\'.'
                )
            )
        ]
    )

    openingstijden_15_03_2022 = StringField(
        'Openingstijden 15-03-2022',
        description=(
            'Sommige gemeenten werken met mobiele stembureaus die gedurende '
            'de dag op verschillende locaties staan. Voor mobiele stembureaus '
            'moet voor elke locatie een nieuw \'stembureau\' aangemaakt worden '
            '(zodat de locatie en openingstijden apart worden opgeslagen).'
            '<br>'
            '<br>'
            '<b>Format:</b> YYYY-MM-DDTHH:MM:SS tot YYYY-MM-DDTHH:MM:SS'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 2022-03-15T07:30:00 tot 2022-03-15T21:00:00'
        ),
        validators=[
            Optional(),
            Regexp(
                (
                    '^2022-03-15T\d{2}:\d{2}:\d{2} tot '
                    '2022-03-15T\d{2}:\d{2}:\d{2}$'
                ),
                message=(
                    'Dit veld hoort ingevuld te worden zoals '
                    '\'2022-03-15T07:30:00 tot 2022-03-15T21:00:00\'.'
                )
            )
        ]
    )

    openingstijden_16_03_2022 = StringField(
        'Openingstijden 16-03-2022',
        description=(
            'Sommige gemeenten werken met mobiele stembureaus die gedurende '
            'de dag op verschillende locaties staan. Voor mobiele stembureaus '
            'moet voor elke locatie een nieuw \'stembureau\' aangemaakt worden '
            '(zodat de locatie en openingstijden apart worden opgeslagen).'
            '<br>'
            '<br>'
            '<b>Format:</b> YYYY-MM-DDTHH:MM:SS tot YYYY-MM-DDTHH:MM:SS'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 2022-03-16T07:30:00 tot 2022-03-16T21:00:00'
        ),
        default='2022-03-16T07:30:00 tot 2022-03-16T21:00:00',
        validators=[
            Optional(),
            Regexp(
                (
                    '^2022-03-16T\d{2}:\d{2}:\d{2} tot '
                    '2022-03-16T\d{2}:\d{2}:\d{2}$'
                ),
                message=(
                    'Dit veld hoort ingevuld te worden zoals '
                    '\'2022-03-16T07:30:00 tot 2022-03-16T21:00:00\'.'
                )
            )
        ]
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
            'class': 'selectpicker',
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
            '<b>Voorbeeld:</b> https://www.stembureaus<br>indenhaag.nl/'
        ),
        validators=[
            DataRequired(),
            URL(
                message='Ongeldige URL. Correct is bv. '
                '\'https://www.stembureausindenhaag.nl\''
            )
        ],
        render_kw={
            'placeholder': 'bv. https://www.stembureausindenhaag.nl/'
        }
    )

    #verkiezingen = CustomSelectMultipleField(
    #    'Verkiezingen',
    #    description=(
    #        'In het geval van waterschapsverkiezingen en verkiezingen van '
    #        'stadsdeelcommissies / gebiedscommissies / wijkraden kan er in '
    #        'sommige gemeenten niet in elk stembureau voor alle verkiezingen '
    #        'gestemd worden. Door Amsterdam lopen er bijvoorbeeld drie '
    #        'waterschappen en er kan enkel voor een waterschap gestemd worden '
    #        'bij stembureaus die in het gebied van het waterschap liggen. '
    #        'Alle gemeenten vragen we daarom in het geval van deze '
    #        'verkiezingen per stembureau specifiek aan te geven voor welke '
    #        'waterschappen / stadsdeelcommissies / gebiedscommissies / '
    #        'wijkraden er gestemd kunnen worden. Ook als er überhaupt maar '
    #        'één keuze is (bv. als er in de hele gemeente maar voor één '
    #        'waterschap gekozen kan worden) en ook als er in de gemeente bij '
    #        'elk stembureau voor alle verkiezingen gestemd kan worden.'
    #        '<br>'
    #        '<br>'
    #        'In het geval dat er in dit stembureau voor meerdere '
    #        'waterschappen / stadsdeelcommissies / gebiedscommissies / '
    #        'wijkraden gestemd kan worden dan scheidt u deze met een '
    #        'puntkomma, bv.: waterschapsverkiezingen voor Delfland; '
    #        'waterschapsverkiezingen voor Rijnland'
    #        '<br>'
    #        '<br>'
    #        '<b>Format:</b> keuze uit:'
    #        '<ul>'
    #        '  <li>waterschapsverkiezingen voor &lt;naam van waterschap '
    #        'zonder \'Waterschap\' of \'Hoogheemraadschap\' voor de naam&gt;</li>'
    #        '  <li>verkiezingen &lt;gebiedscommissies / wijkraden&gt; '
    #        '&lt;naam van gebiedscommissies / wijkraden&gt;</li>'
    #        '  <li>verkiezingen stadsdeelcommissie &lt;naam van '
    #        'stadsdeelcommissie&gt;</li>'
    #        '</ul>'
    #        '<br>'
    #        '<b>Voorbeeld:</b> waterschapsverkiezingen voor Delfland'
    #    ),
    #    choices=[
    #        (
    #            'waterschapsverkiezingen voor Noorderzijlvest',
    #            'waterschapsverkiezingen voor Noorderzijlvest'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Fryslân',
    #            'waterschapsverkiezingen voor Fryslân'
    #        ),
    #        (
    #            \'waterschapsverkiezingen voor Hunze en Aa's\',
    #            \'waterschapsverkiezingen voor Hunze en Aa's\'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Drents Overijsselse Delta',
    #            'waterschapsverkiezingen voor Drents Overijsselse Delta'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Vechtstromen',
    #            'waterschapsverkiezingen voor Vechtstromen'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Vallei en Veluwe',
    #            'waterschapsverkiezingen voor Vallei en Veluwe'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Rijn en IJssel',
    #            'waterschapsverkiezingen voor Rijn en IJssel'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor De Stichtse Rijnlanden',
    #            'waterschapsverkiezingen voor De Stichtse Rijnlanden'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Amstel, Gooi en Vecht',
    #            'waterschapsverkiezingen voor Amstel, Gooi en Vecht'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Hollands Noorderkwartier',
    #            'waterschapsverkiezingen voor Hollands Noorderkwartier'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Rijnland',
    #            'waterschapsverkiezingen voor Rijnland'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Delfland',
    #            'waterschapsverkiezingen voor Delfland'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Schieland en de Krimpenerwaard',
    #            'waterschapsverkiezingen voor Schieland en de Krimpenerwaard'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Rivierenland',
    #            'waterschapsverkiezingen voor Rivierenland'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Hollandse Delta',
    #            'waterschapsverkiezingen voor Hollandse Delta'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Scheldestromen',
    #            'waterschapsverkiezingen voor Scheldestromen'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Brabantse Delta',
    #            'waterschapsverkiezingen voor Brabantse Delta'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor De Dommel',
    #            'waterschapsverkiezingen voor De Dommel'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Aa en Maas',
    #            'waterschapsverkiezingen voor Aa en Maas'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Limburg',
    #            'waterschapsverkiezingen voor Limburg'
    #        ),
    #        (
    #            'waterschapsverkiezingen voor Zuiderzeeland',
    #            'waterschapsverkiezingen voor Zuiderzeeland'
    #        )
    #    ],
    #    validators=[
    #        Optional(),
    #    ],
    #    render_kw={
    #        'class': 'selectpicker',
    #        'data-icon-base': 'fa',
    #        'data-tick-icon': 'fa-check',
    #        'data-none-selected-text': (
    #            'Selecteer één of meerdere waterschappen'
    #        )
    #    }
    #)

    toegankelijk_voor_mensen_met_een_lichamelijke_beperking = CustomSelectField(
        'Toegankelijk voor mensen met een lichamelijke beperking',
        description=(
            'Is het stembureau toegankelijk voor mensen met een lichamelijke beperking?'
            '<br>'
            'Voor meer informatie, <a '
            'href="https://www.rijksoverheid.nl/documenten/publicaties/2021/'
            '10/14/toegankelijkheid-verkiezingen" target="_blank" '
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
            'class': 'selectpicker',
            'data-none-selected-text': ''
        }
    )

    akoestiek = CustomSelectField(
        'Akoestiek',
        description=(
            'Is de akoestiek van het stembureau geschikt voor '
            'slechthorenden? Voor meer informatie, zie <a '
            'href="https://bk.nijsnet.com/04040_Slechthorenden.aspx" '
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
            Optional()
        ],
        render_kw={
            'class': 'selectpicker',
            'data-none-selected-text': ''
        }
    )

    auditieve_hulpmiddelen = StringField(
        'Auditieve hulpmiddelen',
        description=(
            'Welke auditieve hulpmiddelen zijn aanwezig? Dit is een vrij '
            'tekstveld.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> gebarentolk'
        ),
        validators=[
            Optional()
        ],
        render_kw={
            'placeholder': 'bv. gebarentolk'
        }
    )

    visuele_hulpmiddelen = StringField(
        'Visuele hulpmiddelen',
        description=(
            'Welke visuele hulpmiddelen zijn aanwezig? Dit is een vrij '
            'tekstveld.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> leesloep, stemmal, vrijwilliger/host aanwezig'
        ),
        validators=[
            Optional()
        ],
        render_kw={
            'placeholder': 'bv. leesloep, stemmal, vrijwilliger/host aanwezig'
        }
    )

    gehandicaptentoilet = CustomSelectField(
        'Gehandicaptentoilet',
        description=(
            '<b>Format:</b> Vul \'ja\' in als er een gehandicaptentoilet '
            'aanwezig is in het stembureau. Vul \'nee\' in als dat niet zo is. '
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
            'class': 'selectpicker',
            'data-none-selected-text': ''
        }
    )
