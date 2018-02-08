from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, StringField, IntegerField, FloatField, PasswordField,
    SubmitField, FormField, FieldList
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    submit = SubmitField('Bevestig')


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
    submit = SubmitField('Bevestig')


class LoginForm(FlaskForm):
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    Wachtwoord = PasswordField('Wachtwoord', validators=[DataRequired()])
    submit = SubmitField('Inloggen')


class PubliceerForm(FlaskForm):
    submit = SubmitField('Publiceer')


class EditForm(FlaskForm):
    submit = SubmitField('Opslaan')
    submit_annuleren = SubmitField('Annuleren')
    submit_verwijderen = SubmitField('Verwijderen')

    nummer_stembureau = IntegerField(
        'Nummer stembureau',
        validators=[
            DataRequired()
        ]
    )
    naam_stembureau = StringField(
        'Naam stembureau',
        validators=[
            DataRequired()
        ]
    )
    gebruikersdoel_het_gebouw = StringField(
        'Gebruikersdoel het gebouw',
        validators=[
            DataRequired()
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
            DataRequired()
        ]
    )
    extra_adresaanduiding = StringField(
        'Extra adresaanduiding',
        validators=[]
    )
    longitude = FloatField(
        'Longitude',
        validators=[
            DataRequired()
        ]
    )
    latitude = FloatField(
        'Latitude',
        validators=[
            DataRequired()
        ]
    )
    districtcode = StringField(
        'Districtcode',
        validators=[]
    )
    openingstijden = StringField(
        'Openingstijden',
        validators=[
            DataRequired()
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
