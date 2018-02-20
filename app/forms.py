from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import (
    ValidationError, DataRequired, Email, EqualTo, Length, URL, NumberRange,
    AnyOf, Regexp
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
                ['json', 'csv', 'xls', 'xlsx', 'ods'],
                (
                    'Alleen Excel (.xls, .xslx) of OpenDocument (.ods) '
                    'spreadsheets zijn toegestaan.'
                )
            )
        ],
        render_kw={
            'class': 'filestyle',
            'data-classButton': 'btn btn-primary',
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


def title(form, field):
    # Make sure the first character is upper case (this conversion will
    # be saved)
    field.data = field.data.title()


# Require at least four decimals
def min_four_decimals(form, field):
    if not re.match('^\d+\.\d{4,}', str(field.data)):
        raise ValidationError(
            'Latitude en Longitude moeten minimaal 4 decimalen hebben.'
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
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )
    naam_stembureau = StringField(
        'Naam stembureau',
        validators=[
            DataRequired()
        ]
    )
    # The order of validators is important, 'title' needs to be listed
    # before 'AnyOf'
    gebruikersdoel_het_gebouw = StringField(
        'Gebruikersdoel het gebouw',
        validators=[
            DataRequired(),
            title,
            AnyOf(
                [
                    'Wonen', 'Bijeenkomst', 'Winkel', 'Gezondheidszorg',
                    'Kantoor', 'Logies', 'Industrie', 'Onderwijs', 'Sport',
                    'Cel', 'Overig'
                ]
            )
        ]
    )
    website_locatie = StringField(
        'Website locatie',
        validators=[
            URL()
        ]
    )
    bag_referentienummer = StringField(
        'BAG referentienummer',
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
        validators=[]
    )
    longitude = FloatField(
        'Longitude',
        validators=[
            DataRequired(),
            min_four_decimals
        ]
    )
    latitude = FloatField(
        'Latitude',
        validators=[
            DataRequired(),
            min_four_decimals
        ]
    )
    districtcode = StringField(
        'Districtcode',
        validators=[]
    )
    openingstijden = StringField(
        'Openingstijden',
        validators=[
            DataRequired(),
            Regexp(
                (
                    '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} tot '
                    '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
                ),
                message=(
                    'Dit veld hoort ingevuld te worden zoals '
                    '"2017-03-21T07:30:00 tot 2017-03-21T21:00:00".'
                )
            )
        ]
    )
    mindervaliden_toegankelijk = BooleanField(
        'Mindervaliden toegankelijk',
        validators=[]
    )
    invalidenparkeerplaatsen = BooleanField(
        'Invalidenparkeerplaatsen',
        validators=[]
    )
    akoestiek = BooleanField(
        'Akoestiek',
        validators=[]
    )
    mindervalide_toilet_aanwezig = BooleanField(
        'Mindervalide toilet aanwezig',
        validators=[]
    )
    kieskring_id = StringField(
        'Kieskring ID',
        validators=[]
    )
    hoofdstembureau = StringField(
        'Hoofdstembureau',
        validators=[]
    )
    contactgegevens = StringField(
        'Contactgegevens',
        validators=[
            DataRequired()
        ]
    )
    beschikbaarheid = StringField(
        'Beschikbaarheid',
        validators=[
            DataRequired(),
            URL()
        ]
    )
