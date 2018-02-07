from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


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


class FileUploadForm(FlaskForm):
    data_file = FileField('Bestand', validators=[
        FileRequired(), FileAllowed(
            ['json', 'csv', 'xls', 'xlsx', 'ods'],
            'Alleen Excel of Open Office bestanden zijn toegestaan.')])
    submit = SubmitField('Uploaden')


class VotingStationForm(FlaskForm):
        # TODO: validate correctly
        gemeente = StringField(
            'Gemeente', validators=[DataRequired()])
        gemeente_code = StringField(
            'CBS gemeentecode', validators=[DataRequired()])
        stembureau_nummer = IntegerField(
            'Nummer Stembureau', validators=[DataRequired()])
        stembureau_naam = StringField(
            'Naam Stembureau', validators=[DataRequired()])
