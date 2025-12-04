#/usr/bin/env python
# -*- coding: utf-8 -*-
import locale
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from app.assets_blueprint import assets_blueprint
from config import Config
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_babel import Babel
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from app.ckan import CKAN

login_manager = LoginManager()
db = SQLAlchemy()
mail = Mail()
ckan = CKAN()
babel = Babel()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(assets_blueprint)
    db.init_app(app)
    mail.init_app(app)
    ckan.init_app(app)

    # Used for translating error messages for Flask-WTF forms
    babel.init_app(app)

    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    login_manager.login_message = u"Log in om verder te gaan"
    login_manager.login_view = "gemeente_login"

    locale.setlocale(locale.LC_NUMERIC, 'nl_NL.UTF-8')
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')

    if not app.debug:
        # Send email on errors
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['FROM'],
                toaddrs=app.config['ADMINS'],
                subject='[Stemlokalen] website error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

    def jinja_dateformat_filter(timestamp):
        return datetime.fromisoformat(timestamp).strftime('%A %-d %B')
    app.jinja_env.filters['format_date'] = jinja_dateformat_filter

    # Log info messages and up to file
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler(
        'logs/stemlokalen.log',
        maxBytes=1000000,
        backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info(f'Stemlokalen startup, debug={app.debug}')

    from app.models import (
        Gemeente, User, Gemeente_user, Election, BAG
    )
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'Gemeente': Gemeente,
            'User': User,
            'Gemeente_user': Gemeente_user,
            'Election': Election,
            'BAG': BAG
        }

    with app.app_context():
        # Create the MySQL tables if they don't exist
        db.create_all()

        from .routes import create_routes
        create_routes(app)
        from app.errors import create_error_handlers
        create_error_handlers(app)
        from app.cli import create_cli_commands
        create_cli_commands(app)

    return app