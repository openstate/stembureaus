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
    RadioField
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


# Require at least four decimals and a point in between the numbers
def min_four_decimals(form, field):
    if not re.match('^-?\d+\.\d{4,}', str(field.data)):
        raise ValidationError(
            'De cijfers in de Latitude en Longitude velden moeten met een '
            'punt (of komma) gescheiden worden en moeten minimaal 4 '
            'decimalen achter de punt hebben.'
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


def x_range(form, field):
    if type(field.data) == float:
        if field.data >= 0 and field.data < 300000:
            return
    else:
        raise ValidationError(
            'De x-waarde moet tussen 0 of 300000 liggen, anders ligt de '
            'coördinaat niet op het vasteland van Europees Nederland.'
        )


def y_range(form, field):
    if type(field.data) == float:
        if field.data >= 300000 and field.data < 620000:
            return
    else:
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
                self.longitude.data, self.latitude.data
            )
        elif self.x.data and self.y.data:
            self.longitude.data, self.latitude.data = convert_xy_to_latlong(
                self.x.data, self.y.data
            )

        if not FlaskForm.validate(self):
            valid = False

        if (self.bag_referentienummer.data == "0000000000000000" and
                not self.extra_adresaanduiding.data):
            self.extra_adresaanduiding.errors.append(
                'Aangezien u "0000000000000000" in het "BAG '
                'referentienummer"-veld heeft ingevuld moet u het adres of '
                'andere verduidelijking van de locatie van stembureau in dit '
                'veld invullen.'
            )
            valid = False

        if (not ((self.latitude.data and self.longitude.data) or
                (self.x.data and self.y.data))):
            self.latitude.errors.append(
                "Minimaal Longitude en Latitude of X en Y moeten "
                "ingevuld zijn."
            )
            self.longitude.errors.append(
                "Minimaal Longitude en Latitude of X en Y moeten "
                "ingevuld zijn."
            )
            self.x.errors.append(
                "Minimaal Longitude en Latitude of X en Y moeten "
                "ingevuld zijn."
            )
            self.y.errors.append(
                "Minimaal Longitude en Latitude of X en Y moeten "
                "ingevuld zijn."
            )
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
            'stembureaus.'
            '<br>'
            '<br>'
            'Elk stembureau moet apart ingevoerd worden ook al is de '
            'locatie (het stemlokaal) hetzelfde aangezien elk stembureau een '
            'ander nummer heeft.'
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
            DataRequired()
        ],
        render_kw={
            'placeholder': 'bv. Stadhuis'
        }
    )

    website_locatie = URLStringField(
        'Website locatie',
        description=(
            'Website van de locatie van het stembureau, indien aanwezig.'
            '<br>'
            '<br>'
            '<b>Format:</b> Volledige URL (dit begint met "http://" or '
            '"https://")'
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
                '"https://www.voorbeeld.nl"'
            )
        ],
        render_kw={
            'placeholder': 'bv. https://www.denhaag.nl/nl'
            '/bestuur-en-organisatie/contact-met-de-gemeente'
            '/stadhuis-den-haag.htm'
        }
    )

    bag_referentienummer = StringField(
        'BAG referentienummer',
        description=(
            'BAG Nummeraanduiding ID, vindbaar door het adres van het '
            'stembureau op <a href="https://bagviewer.kadaster.nl/" '
            'target="_blank" rel="noopener">bagviewer.kadaster.nl</a> in te '
            'voeren en rechts onder het kopje "Nummeraanduiding" te kijken.'
            '<br>'
            '<br>'
            'Vermeld voor mobiele stembureaus het dichtstbijzijnde BAG '
            'Nummeraanduiding ID en gebruik eventueel het '
            '"Extra adresaanduiding"-veld om de locatie van stembureau te '
            'beschrijven. NB: de precieze locatie geeft u aan met de '
            '"Latitude" en "Longitude"-velden of met de "X" en "Y"-velden.'
            '<br>'
            '<br>'
            'Bonaire, Sint Eustatius en Saba moeten hier "0000000000000000" '
            '(zestien keer het getal "0") invullen. Het adres van het '
            'stembureau moet vervolgens in het "Extra adresaanduiding"-veld '
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

    extra_adresaanduiding = StringField(
        'Extra adresaanduiding',
        description=(
            'Eventuele extra informatie over de locatie van het stembureau. '
            'Bv. "Ingang aan achterkant gebouw" of "Mobiel stembureau op het '
            'midden van het plein".'
            '<br>'
            '<br>'
            'Bonaire, Sint Eustatius en Saba moeten hier het adres van het '
            'stembureau invullen.'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Ingang aan achterkant gebouw'
        ),
        validators=[
            Optional(),
        ],
        render_kw={
            'placeholder': 'bv. Ingang aan achterkant gebouw'
        }
    )

    longitude = CommaDotFloatField(
        'Longitude',
        description=(
            'Lengtegraad met minimaal 4 decimalen.'
            '<br>'
            '<br>'
            'Als u de longitude van het stembureau niet weet dan kunt u '
            'dit vinden via <a href="https://www.openstreetmap.org/" '
            'target="_blank" rel="noopener">openstreetmap.org</a>. Zoom in op '
            'het stembureau, klik op de juiste locatie met de rechtermuisknop '
            'en selecteer "Show address"/"Toon adres". De latitude en '
            'longitude (in die volgorde) staan nu linksboven in de zoekbalk.'
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

    latitude = CommaDotFloatField(
        'Latitude',
        description=(
            'Breedtegraad met minimaal 4 decimalen.'
            '<br>'
            '<br>'
            'Als u de latitude van het stembureau niet weet dan kunt '
            'dit vinden via <a href="https://www.openstreetmap.org/" '
            'target="_blank" rel="noopener">openstreetmap.org</a>. Zoom in op '
            'het stembureau, klik op de juiste locatie met de rechtermuisknop '
            'en selecteer "Show address"/"Toon adres". De latitude en '
            'longitude (in die volgorde) staan nu linksboven in de zoekbalk.'
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

    openingstijden = StringField(
        'Openingstijden',
        description=(
            'Sommige gemeenten werken met mobiele stembureaus die gedurende '
            'de dag op verschillende locaties staan.'
            '<br>'
            '<br>'
            'Voor mobiele stembureaus moet voor elke locatie een nieuw '
            '"stembureau" aangemaakt worden (zodat de locatie en '
            'openingstijden apart worden opgeslagen).'
            '<br>'
            '<br>'
            '<b>Format:</b> YYYY-MM-DDTHH:MM:SS tot YYYY-MM-DDTHH:MM:SS'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 2019-03-20T07:30:00 tot 2019-03-20T21:00:00'
        ),
        default='2019-03-20T07:30:00 tot 2019-03-20T21:00:00',
        validators=[
            DataRequired(),
            Regexp(
                (
                    '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} tot '
                    '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
                ),
                message=(
                    'Dit veld hoort ingevuld te worden zoals '
                    '"2019-03-20T07:30:00 tot 2019-03-20T21:00:00".'
                )
            )
        ]
    )

    contactgegevens = StringField(
        'Contactgegevens',
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

    beschikbaarheid = URLStringField(
        'Beschikbaarheid',
        description=(
            'URL van de gemeentewebsite met data of informatie over de '
            'stembureaus (of verkiezing).'
            '<br>'
            '<br>'
            '<b>Format:</b> Volledige URL (dit begint met "http://" of '
            '"https://")'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> https://www.stembureaus<br>indenhaag.nl/'
        ),
        validators=[
            DataRequired(),
            URL(
                message='Ongeldige URL. Correct is bv. '
                '"https://www.stembureausindenhaag.nl"'
            )
        ],
        render_kw={
            'placeholder': 'bv. https://www.stembureausindenhaag.nl/'
        }
    )

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
            'zonder "Waterschap" of "Hoogheemraadschap" voor de naam&gt;</li>'
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
                'waterschapsverkiezingen voor Noorderzijlvest'
            ),
            (
                'waterschapsverkiezingen voor Fryslân',
                'waterschapsverkiezingen voor Fryslân'
            ),
            (
                "waterschapsverkiezingen voor Hunze en Aa's",
                "waterschapsverkiezingen voor Hunze en Aa's"
            ),
            (
                'waterschapsverkiezingen voor Drents Overijsselse Delta',
                'waterschapsverkiezingen voor Drents Overijsselse Delta'
            ),
            (
                'waterschapsverkiezingen voor Vechtstromen',
                'waterschapsverkiezingen voor Vechtstromen'
            ),
            (
                'waterschapsverkiezingen voor Vallei en Veluwe',
                'waterschapsverkiezingen voor Vallei en Veluwe'
            ),
            (
                'waterschapsverkiezingen voor Rijn en IJssel',
                'waterschapsverkiezingen voor Rijn en IJssel'
            ),
            (
                'waterschapsverkiezingen voor De Stichtse Rijnlanden',
                'waterschapsverkiezingen voor De Stichtse Rijnlanden'
            ),
            (
                'waterschapsverkiezingen voor Amstel, Gooi en Vecht',
                'waterschapsverkiezingen voor Amstel, Gooi en Vecht'
            ),
            (
                'waterschapsverkiezingen voor Hollands Noorderkwartier',
                'waterschapsverkiezingen voor Hollands Noorderkwartier'
            ),
            (
                'waterschapsverkiezingen voor Rijnland',
                'waterschapsverkiezingen voor Rijnland'
            ),
            (
                'waterschapsverkiezingen voor Delfland',
                'waterschapsverkiezingen voor Delfland'
            ),
            (
                'waterschapsverkiezingen voor Schieland en de Krimpenerwaard',
                'waterschapsverkiezingen voor Schieland en de Krimpenerwaard'
            ),
            (
                'waterschapsverkiezingen voor Rivierenland',
                'waterschapsverkiezingen voor Rivierenland'
            ),
            (
                'waterschapsverkiezingen voor Hollandse Delta',
                'waterschapsverkiezingen voor Hollandse Delta'
            ),
            (
                'waterschapsverkiezingen voor Scheldestromen',
                'waterschapsverkiezingen voor Scheldestromen'
            ),
            (
                'waterschapsverkiezingen voor Brabantse Delta',
                'waterschapsverkiezingen voor Brabantse Delta'
            ),
            (
                'waterschapsverkiezingen voor De Dommel',
                'waterschapsverkiezingen voor De Dommel'
            ),
            (
                'waterschapsverkiezingen voor Aa en Maas',
                'waterschapsverkiezingen voor Aa en Maas'
            ),
            (
                'waterschapsverkiezingen voor Limburg',
                'waterschapsverkiezingen voor Limburg'
            ),
            (
                'waterschapsverkiezingen voor Zuiderzeeland',
                'waterschapsverkiezingen voor Zuiderzeeland'
            )
        ],
        validators=[
            Optional(),
        ],
        render_kw={
            'class': 'selectpicker',
            'data-icon-base': 'fa',
            'data-tick-icon': 'fa-check',
            'data-none-selected-text': (
                'Selecteer één of meerdere waterschappen'
            )
        }
    )

    mindervaliden_toegankelijk = CustomSelectField(
        'Mindervaliden toegankelijk',
        description=(
            'Is het stembureau toegankelijk voor mindervaliden?'
            '<br>'
            'Voor meer informatie, <a '
            'href="https://vng.nl/onderwerpenindex/bestuur/'
            'verkiezingen-referenda/nieuws/'
            'toegankelijke-verkiezingen-waar-moeten-gemeenten-op-letten" '
            'target="_blank" rel="noopener">zie deze pagina op vng.nl</a>.'
            '<br>'
            'Mocht uw gemeente de toegankelijkheid van de stembureaus op '
            'basis van de ‘Checklist toegankelijkheidscriteria stemlokalen’ '
            'toetsen, dan kunt u de antwoorden onderaan dit formulier '
            'invullen.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul "Y" in als het stembureau mindervaliden '
            'toegankelijk is. Vul "N" in als dat niet zo is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
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
            'Is de akoestiek van het stembureau geschikt voor slechthorenden? '
            'Voor meer informatie, zie <a '
            'href="https://bk.nijsnet.com/04040_Slechthorenden.aspx" '
            'target="_blank" rel="noopener">deze website</a>.'
            '<br>'
            '<br>'
            '<b>Format:</b> Vul "Y" in als de akoestiek in het stembureau '
            'geschikt is voor slechthorenden. Vul "N" in als dat niet zo is. '
            'Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'selectpicker',
            'data-none-selected-text': ''
        }
    )

    mindervalide_toilet_aanwezig = CustomSelectField(
        'Mindervalide toilet aanwezig',
        description=(
            '<b>Format:</b> Vul "Y" in als de er een mindervalide toilet '
            'aanwezig is in het stembureau. Vul "N" in als dat niet zo is. '
            'Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'selectpicker',
            'data-none-selected-text': ''
        }
    )

    show_checklist = RadioField(
        'Toon "Checklist toegankelijkheidscriteria stembureaus"',
        choices=[('Nee', 'Nee'), ('Ja', 'Ja')],
        default='Nee'
    )

    v1_1_a_aanduiding_aanwezig = CustomSelectField(
        '1.1.a Aanduiding aanwezig',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_1_b_aanduiding_duidelijk_zichtbaar = CustomSelectField(
        '1.1.b Aanduiding duidelijk zichtbaar',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_1_c_aanduiding_goed_leesbaar = CustomSelectField(
        '1.1.c Aanduiding goed leesbaar',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_2_a_gpa_aanwezig = CustomSelectField(
        '1.2.a GPA aanwezig',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_2_b_aantal_vrij_parkeerplaatsen_binnen_50m_van_de_entree = IntegerField(
        '1.2.b Aantal vrij parkeerplaatsen binnen 50m van de entree',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Aantal'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 6'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 6'
        }
    )

    v1_2_c_hoogteverschil_tussen_parkeren_en_trottoir = CustomSelectField(
        '1.2.c Hoogteverschil tussen parkeren en trottoir',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_2_d_hoogteverschil = IntegerField(
        '1.2.d Hoogteverschil',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 20'
        ),
        validators=[
            NumberRange(min=0, max=10000),
            Optional()
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 20'
        }
    )

    v1_2_e_type_overbrugging = CustomSelectField(
        '1.2.e Type overbrugging',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Helling/Trap/Lift/Geen'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Lift'
        ),
        choices=[
            ('', ''),
            ('Helling', 'Helling'),
            ('Trap', 'Trap'),
            ('Lift', 'Lift'),
            ('Geen', 'Geen')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_2_f_overbrugging_conform_itstandaard = CustomSelectField(
        '1.2.f Overbrugging conform ITstandaard',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_3_a_vlak_verhard_en_vrij_van_obstakels = CustomSelectField(
        '1.3.a Vlak, verhard en vrij van obstakels',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_3_b_hoogteverschil = IntegerField(
        '1.3.b Hoogteverschil',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 30'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 30'
        }
    )

    v1_3_c_type_overbrugging = CustomSelectField(
        '1.3.c Type overbrugging',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Helling/Trap/Lift/Geen'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Lift'
        ),
        choices=[
            ('', ''),
            ('Helling', 'Helling'),
            ('Trap', 'Trap'),
            ('Lift', 'Lift'),
            ('Geen', 'Geen')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_3_d_overbrugging_conform_itstandaard = CustomSelectField(
        '1.3.d Overbrugging conform ITstandaard',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_3_e_obstakelvrije_breedte_van_de_route = IntegerField(
        '1.3.e Obstakelvrije breedte van de route',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 120'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 120'
        }
    )

    v1_3_f_obstakelvrije_hoogte_van_de_route = IntegerField(
        '1.3.f Obstakelvrije hoogte van de route',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 200'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 200'
        }
    )

    v1_4_a_is_er_een_route_tussen_gebouwentree_en_stemruimte = CustomSelectField(
        '1.4.a Is er een route tussen gebouwentree en stemruimte',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_4_b_route_duidelijk_aangegeven = CustomSelectField(
        '1.4.b Route duidelijk aangegeven',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_4_c_vlak_en_vrij_van_obstakels = CustomSelectField(
        '1.4.c Vlak en vrij van obstakels',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_4_d_hoogteverschil = IntegerField(
        '1.4.d Hoogteverschil',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 10'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 10'
        }
    )

    v1_4_e_type_overbrugging = CustomSelectField(
        '1.4.e Type overbrugging',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Helling/Trap/Lift/Geen'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Lift'
        ),
        choices=[
            ('', ''),
            ('Helling', 'Helling'),
            ('Trap', 'Trap'),
            ('Lift', 'Lift'),
            ('Geen', 'Geen')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_4_f_overbrugging_conform_itstandaard = CustomSelectField(
        '1.4.f Overbrugging conform ITstandaard',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v1_4_g_obstakelvrije_breedte_van_de_route = IntegerField(
        '1.4.g Obstakelvrije breedte van de route',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 110'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 110'
        }
    )

    v1_4_h_obstakelvrije_hoogte_van_de_route = IntegerField(
        '1.4.h Obstakelvrije hoogte van de route',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 220'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 220'
        }
    )

    v1_4_i_deuren_in_route_bedien_en_bruikbaar = CustomSelectField(
        '1.4.i Deuren in route bedien- en bruikbaar',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_1_a_deurtype = CustomSelectField(
        '2.1.a Deurtype',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Handbediend of Automatisch'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Handbediend'
        ),
        choices=[
            ('', ''),
            ('Handbediend', 'Handbediend'),
            ('Automatisch', 'Automatisch')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_1_b_opstelruimte_aan_beide_zijden_van_de_deur = CustomSelectField(
        '2.1.b Opstelruimte aan beide zijden van de deur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_1_c_bedieningskracht_buitendeur = CustomSelectField(
        '2.1.c Bedieningskracht buitendeur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <40N of >40N'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <40N'
        ),
        choices=[('', ''), ('<40N', '<40N'), ('>40N', '>40N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_1_d_drempelhoogte_t_o_v_straat_vloer_niveau = CustomSelectField(
        '2.1.d Drempelhoogte (t.o.v. straat/vloer niveau)',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <2cm of >2cm'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <2cm'
        ),
        choices=[('', ''), ('<2cm', '<2cm'), ('>2cm', '>2cm')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_1_e_vrije_doorgangsbreedte_buitendeur = CustomSelectField(
        '2.1.e Vrije doorgangsbreedte buitendeur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <85cm of >85cm'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> >85cm'
        ),
        choices=[('', ''), ('<85cm', '<85cm'), ('>85cm', '>85cm')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_2_a_tussendeuren_aanwezig_in_eventuele_route = CustomSelectField(
        '2.2.a Tussendeuren aanwezig in eventuele route',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_2_b_deurtype = CustomSelectField(
        '2.2.b Deurtype',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Handbediend of Automatisch'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Handbediend'
        ),
        choices=[
            ('', ''),
            ('Handbediend', 'Handbediend'),
            ('Automatisch', 'Automatisch')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_2_c_opstelruimte_aan_beide_zijden_van_de_deur = CustomSelectField(
        '2.2.c Opstelruimte aan beide zijden van de deur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_2_d_bedieningskracht_deuren = CustomSelectField(
        '2.2.d Bedieningskracht deuren',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <40N of >40N'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <40N'
        ),
        choices=[('', ''), ('<40N', '<40N'), ('>40N', '>40N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_2_e_drempelhoogte_t_o_v_vloer_niveau = CustomSelectField(
        '2.2.e Drempelhoogte (t.o.v. vloer niveau)',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <2cm of >2cm'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <2cm'
        ),
        choices=[('', ''), ('<2cm', '<2cm'), ('>2cm', '>2cm')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_2_f_vrije_doorgangsbreedte_deur = CustomSelectField(
        '2.2.f Vrije doorgangsbreedte deur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <85cm of >85cm'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> >85cm'
        ),
        choices=[('', ''), ('<85cm', '<85cm'), ('>85cm', '>85cm')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_3_a_deur_aanwezig_naar_van_stemruimte = CustomSelectField(
        '2.3.a Deur aanwezig naar/van stemruimte',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_3_b_deurtype = CustomSelectField(
        '2.3.b Deurtype',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Handbediend of Automatisch'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Handbediend'
        ),
        choices=[
            ('', ''),
            ('Handbediend', 'Handbediend'),
            ('Automatisch', 'Automatisch')
        ],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_3_c_opstelruimte_aan_beide_zijden_van_de_deur = CustomSelectField(
        '2.3.c Opstelruimte aan beide zijden van de deur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_3_d_bedieningskracht_deur = CustomSelectField(
        '2.3.d Bedieningskracht deur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <40N of >40N'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <40N'
        ),
        choices=[('', ''), ('<40N', '<40N'), ('>40N', '>40N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_3_e_drempelhoogte_t_o_v_vloer_niveau = CustomSelectField(
        '2.3.e Drempelhoogte (t.o.v. vloer niveau)',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <2cm of >2cm'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> <2cm'
        ),
        choices=[('', ''), ('<2cm', '<2cm'), ('>2cm', '>2cm')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_3_f_vrije_doorgangsbreedte_deur = CustomSelectField(
        '2.3.f Vrije doorgangsbreedte deur',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> <85cm of >85cm'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> >85cm'
        ),
        choices=[('', ''), ('<85cm', '<85cm'), ('>85cm', '>85cm')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_a_zijn_er_tijdelijke_voorzieningen_aangebracht = CustomSelectField(
        '2.4.a Zijn er tijdelijke voorzieningen aangebracht',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_b_vloerbedekking_randen_over_de_volle_lengte_deugdelijk_afgeplakt = CustomSelectField(
        (
            '2.4.b VLOERBEDEKKING: Randen over de volle lengte deugdelijk '
            'afgeplakt'
        ),
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_c_hellingbaan_weerbestendig_alleen_van_toepassing_bij_buitentoepassing = CustomSelectField(
        (
            '2.4.c HELLINGBAAN: Weerbestendig (alleen van toepassing bij '
            'buitentoepassing)'
        ),
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_d_hellingbaan_deugdelijk_verankerd_aan_ondergrond = CustomSelectField(
        '2.4.d HELLINGBAAN: Deugdelijk verankerd aan ondergrond',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_e_leuning_bij_hellingbaan_trap_leuning_aanwezig_en_conform_criteria = CustomSelectField(
        (
            '2.4.e LEUNING BIJ HELLINGBAAN/TRAP: Leuning aanwezig en conform '
            'criteria'
        ),
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_f_dorpeloverbrugging_weerbestendig_alleen_van_toepassing_bij_buitentoepassing = CustomSelectField(
        (
            '2.4.f DORPELOVERBRUGGING: Weerbestendig (alleen van toepassing '
            'bij buitentoepassing)'
        ),
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v2_4_g_dorpeloverbrugging_deugdelijk_verankerd_aan_ondergrond = CustomSelectField(
        '2.4.g DORPELOVERBRUGGING: Deugdelijk verankerd aan ondergrond',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_1_a_obstakelvrije_doorgangen = CustomSelectField(
        '3.1.a Obstakelvrije doorgangen',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_1_b_vrije_draaicirkel_manoeuvreerruimte = CustomSelectField(
        '3.1.b Vrije draaicirkel / manoeuvreerruimte',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_1_c_idem_voor_stemtafel_en_stemhokje = CustomSelectField(
        '3.1.c Idem voor stemtafel en stemhokje',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_1_d_opstelruimte_voor_naast_stembus = CustomSelectField(
        '3.1.d Opstelruimte voor/naast stembus',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_2_a_stoelen_in_stemruimte_aanwezig = CustomSelectField(
        '3.2.a Stoelen in stemruimte aanwezig',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_2_b_1_op_5_stoelen_uitgevoerd_met_armleuningen = CustomSelectField(
        '3.2.b 1 op 5 Stoelen uitgevoerd met armleuningen',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_3_a_hoogte_van_het_laagste_schrijfblad = IntegerField(
        '3.3.a Hoogte van het laagste schrijfblad',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> hoogte in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 60'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 60'
        }
    )

    v3_3_b_schrijfblad_onderrijdbaar = CustomSelectField(
        '3.3.b Schrijfblad onderrijdbaar',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_4_a_hoogte_inworpgleuf_stembiljet = IntegerField(
        '3.4.a Hoogte inworpgleuf stembiljet',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> hoogte in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 70'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 70'
        }
    )

    v3_4_b_afstand_inwerpgleuf_t_o_v_de_opstelruimte = IntegerField(
        '3.4.b Afstand inwerpgleuf t.o.v. de opstelruimte',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> afstand in centimeters'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 160'
        ),
        validators=[
            Optional(),
            NumberRange(min=0, max=10000)
        ],
        render_kw={
            'class': 'checklist',
            'placeholder': 'bv. 160'
        }
    )

    v3_5_a_leesloep_zichtbaar_aanwezig = CustomSelectField(
        '3.5.a Leesloep (zichtbaar) aanwezig',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_6_a_kandidatenlijst_in_stemlokaal_aanwezig = CustomSelectField(
        '3.6.a Kandidatenlijst in stemlokaal aanwezig',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )

    v3_6_b_opstelruimte_voor_de_kandidatenlijst_aanwezig = CustomSelectField(
        '3.6.b Opstelruimte voor de kandidatenlijst aanwezig',
        description=(
            'Zie deze <a href="https://vng.nl/files/vng/bijlage_1_checklist_'
            'toegankelijkheidscriteria_stemlokalen.pdf" target="_blank" '
            'rel="noopener">PDF</a> voor meer informatie'
            '<br>'
            '<br>'
            '<b>Format:</b> Y of N. Laat het veld leeg als het onbekend is.'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Y'
        ),
        choices=[('', ''), ('Y', 'Y'), ('N', 'N')],
        validators=[
            Optional()
        ],
        render_kw={
            'class': 'checklist selectpicker',
            'data-none-selected-text': ''
        }
    )
