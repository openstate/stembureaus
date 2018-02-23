from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import (
    ValidationError, DataRequired, Optional, Email, EqualTo, Length, URL,
    NumberRange, AnyOf, Regexp
)
from wtforms import (
    BooleanField, StringField, IntegerField, FloatField, PasswordField,
    SubmitField, FormField, FieldList
)
import re


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
            'class': 'filestyle',
            'data-classButton': 'btn btn-info',
            'data-buttonText': 'Your label here'
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


# Require at least four decimals and a point in between the numbers
def min_four_decimals(form, field):
    if not re.match('^\d+\.\d{4,}', str(field.data)):
        raise ValidationError(
            'De cijfer in de Latitude en Longitude velden moeten met een punt '
            'gescheiden worden (geen komma) en moeten minimaal 4 decimalen '
            'achter de punt hebben.'
        )


class EditForm(FlaskForm):
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
            'class': 'btn btn-info'
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
        ]
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
        ]
    )

    website_locatie = StringField(
        'Website locatie',
        description=(
            'Website van de locatie van het stembureau, indien aanwezig.'
            '<br>'
            '<br>'
            '<b>Format:</b> URL'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> https://www.denhaag.nl/nl'
            '/bestuur-en-organisatie/contact-met-de-gemeente'
            '/stadhuis-den-haag.htm'
        ),
        validators=[
            Optional(),
            URL()
        ]
    )

    bag_referentienummer = StringField(
        'BAG referentienummer',
        description=(
            'BAG Nummeraanduiding ID, vindbaar door het adres van het '
            'stembureau op <a href="https://bagviewer.kadaster.nl/" '
            'target="_blank">bagviewer.kadaster.nl</a> in te voeren en rechts '
            'onder het kopje "Nummeraanduiding" te kijken.'
            '<br>'
            '<br>'
            'Vermeld voor mobiele stembureaus het dichtstbijzijnde BAG '
            'Nummeraanduiding ID en gebruik eventueel het '
            '"Extra adresaanduiding"-veld om de locatie van stembureau te '
            'beschrijven. NB: de precieze locatie geeft u aan met de '
            '"Latitude" en "Longitude"-velden.'
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
            )
        ]
    )

    extra_adresaanduiding = StringField(
        'Extra adresaanduiding',
        description=(
            'Eventuele extra informatie over de locatie van het stembureau. '
            'Bv. "Ingang aan achterkant gebouw" of "Mobiel stembureau op het '
            'midden van het plein".'
            '<br>'
            '<br>'
            '<b>Format:</b> tekst'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> Ingang aan achterkant gebouw'
        ),
        validators=[
            Optional(),
        ]
    )

    longitude = FloatField(
        'Longitude',
        description=(
            'Lengtegraad met minimaal 4 decimalen.'
            '<br>'
            '<br>'
            '<b>Format:</b> graden in DD.dddd notatie'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 4.3166395'
        ),
        validators=[
            DataRequired(),
            min_four_decimals
        ]
    )

    latitude = FloatField(
        'Latitude',
        description=(
            'Breedtegraad met minimaal 4 decimalen.'
            '<br>'
            '<br>'
            '<b>Format:</b> graden in DD.dddd notatie'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> 52.0775912'
        ),
        validators=[
            DataRequired(),
            min_four_decimals
        ]
    )

    districtcode = StringField(
        'Districtcode',
        description='Districtcode',
        validators=[
            Optional(),
        ]
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
            '<b>Voorbeeld:</b> 2018-03-21T07:30:00 tot 2018-03-21T21:00:00'
        ),
        validators=[
            DataRequired(),
            Regexp(
                (
                    '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} tot '
                    '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
                ),
                message=(
                    'Dit veld hoort ingevuld te worden zoals '
                    '"2018-03-21T07:30:00 tot 2018-03-21T21:00:00".'
                )
            )
        ]
    )

    mindervaliden_toegankelijk = BooleanField(
        'Mindervaliden toegankelijk',
        description=(
            'Bij de bepaling van de toegankelijkheid is het niet voldoende '
            'als het gebouw toegankelijk is. Er moet ook minstens 1 stemhokje '
            'goed toegankelijk zijn (en bereikbaar).'
            '<br>'
            '<br>'
            '<b>Format:</b> vinkje'
        ),
        validators=[
            Optional(),
        ]
    )

    invalidenparkeerplaatsen = BooleanField(
        'Invalidenparkeerplaatsen',
        description=(
            '<b>Format:</b> vinkje'
        ),
        validators=[
            Optional(),
        ]
    )

    akoestiek = BooleanField(
        'Akoestiek',
        description=(
            'Aanvinken als de akoestiek geschikt is voor slechthorenden.'
            '<br>'
            '<br>'
            '<b>Format:</b> vinkje'
        ),
        validators=[
            Optional(),
        ]
    )

    mindervalide_toilet_aanwezig = BooleanField(
        'Mindervalide toilet aanwezig',
        description=(
            '<b>Format:</b> vinkje'
        ),
        validators=[
            Optional(),
        ]
    )

    contactgegevens = StringField(
        'Contactgegevens',
        description=(
            '&lt;afdeling/functie&gt;: De afdeling of specifieke functie '
            'binnen de gemeente die zich bezig houdt met de stembureaus; ivm '
            'verduurzaming bij voorkeur dus niet de naam/contactgegevens van '
            'een persoon.'
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
        ]
    )

    beschikbaarheid = StringField(
        'Beschikbaarheid',
        description=(
            'URL van de gemeentewebsite met data of informatie over de '
            'stembureaus (of verkiezing).'
            '<br>'
            '<br>'
            '<b>Format:</b> URL'
            '<br>'
            '<br>'
            '<b>Voorbeeld:</b> https://www.stembureaus<br>indenhaag.nl/'
        ),
        validators=[
            DataRequired(),
            URL()
        ]
    )
