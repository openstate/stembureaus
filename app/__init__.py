#/usr/bin/env python
# -*- coding: utf-8 -*-
import locale
from config import Config
from flask import Flask
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

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

from app import routes, models
