#/usr/bin/env python
# -*- coding: utf-8 -*-
import locale
import os
import re
from collections import defaultdict
from config import Config
from decimal import *
from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# Used for translating error messages for Flask-WTF forms
babel = Babel(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = u"Log in om verder te gaan"
login_manager.login_view = "gemeente_login"

locale.setlocale(locale.LC_NUMERIC, 'nl_NL.UTF-8')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.email)


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


# Create the 'User' table above if it doesn't exist
db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')

@app.route("/dataset")
def dataset():
    return render_template('dataset.html')

@app.route("/gemeente-aanmelden", methods=['GET', 'POST'])
def gemeente_aanmelden():
    if current_user.is_authenticated:
        return redirect(url_for('gemeente_stemlokalen_overzicht'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.Wachtwoord.data)
        db.session.add(user)
        db.session.commit()
        flash('Aanmelden gelukt')
        return redirect(url_for('gemeente_login'))
    return render_template('gemeente-aanmelden.html', form=form)

@app.route("/gemeente-login", methods=['GET', 'POST'])
def gemeente_login():
    if current_user.is_authenticated:
        return redirect(url_for('gemeente_stemlokalen_overzicht'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.Wachtwoord.data):
            flash('Fout e-mailadres of wachtwoord')
            return(redirect(url_for('gemeente_login')))
        login_user(user)
        return redirect(url_for('gemeente_stemlokalen_overzicht'))
    return render_template('gemeente-login.html', form=form)

@app.route("/gemeente-logout")
@login_required
def gemeente_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/gemeente-stemlokalen-overzicht", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_overzicht():
    return render_template('gemeente-stemlokalen-overzicht.html')

@app.route("/gemeente-stemlokalen-upload", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_upload():
    return render_template('gemeente-stemlokalen-upload.html')

if __name__ == "__main__":
    app.run(threaded=True)
