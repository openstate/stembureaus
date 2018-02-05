from app import app, db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
from ckanapi import RemoteCKAN
import jwt


class CKAN():
    ua = 'waarismijnstemlokaal/1.0 (+https://waarismijnstemlokaal.nl/)'
    ckan = RemoteCKAN(
        'https://acc-ckan.dataplatform.nl',
        apikey=app.config['CKAN_API_KEY'],
        user_agent=ua
    )

    def get_resources(self):
        resources = app.config['CKAN_PUBLISH_RESOURCE_IDS']
        resource_data = {}
        for resource in resources:
            resource_metadata = self.ckan.action.resource_show(id=resource)
            resource_data[resource] = resource_metadata['name']
        return resource_data


ckanapi = CKAN()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gemeente = db.Column(db.String(120), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        if len(password) < 12:
            raise RuntimeError(
                'Attempted to set password with length less than 12 characters'
            )
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=86400):
        return jwt.encode(
            {
                'reset_password': self.id,
                'exp': time() + expires_in
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms='HS256'
            )['reset_password']
        except:
            return
        return User.query.get(user_id)

    def __repr__(self):
        return '<User {}>'.format(self.email)


# Create the 'User' table above if it doesn't exist
db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
