from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo


class RegisterForm(FlaskForm):
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    # Use 'Wachtwoord' instead of 'password' as the variable
    # is used in a user-facing error message when the passwords
    # don't match and we want it to show a Dutch word instead of
    # English
    Wachtwoord = PasswordField('Wachtwoord', validators=[DataRequired()])
    Wachtwoord2 = PasswordField(
        'Herhaal wachtwoord', validators=[DataRequired(), EqualTo('Wachtwoord')])
    submit = SubmitField('Aanmelden')


class LoginForm(FlaskForm):
    email = StringField('E-mailadres', validators=[DataRequired(), Email()])
    Wachtwoord = PasswordField('Wachtwoord', validators=[DataRequired()])
    submit = SubmitField('Inloggen')
