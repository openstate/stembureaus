import os

from flask import render_template, request, redirect, url_for, flash
from flask_login import (
    UserMixin, login_required, login_user, logout_user, current_user)
from werkzeug.utils import secure_filename

from app import app, db
from app.forms import (
    ResetPasswordRequestForm, ResetPasswordForm, LoginForm, EditForm)
from app.parser import UploadFileParser
from app.validator import Validator
from app.email import send_password_reset_email
from app.models import User, ckan, Record


field_order = [
    'Nummer stembureau',
    'Naam stembureau',
    'Gebruikersdoel het gebouw',
    'Website locatie',
    'BAG referentienummer',
    'Extra adresaanduiding',
    'Longitude',
    'Latitude',
    'Districtcode',
    'Openingstijden',
    'Mindervaliden toegankelijk',
    'Invalidenparkeerplaatsen',
    'Akoestiek',
    'Mindervalide toilet aanwezig',
    'Kieskring ID',
    'Hoofdstembureau',
    'Contactgegevens',
    'Beschikbaarheid'
]


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')


@app.route("/dataset")
def dataset():
    return render_template('dataset.html')


@app.route("/gemeente-reset-wachtwoord-verzoek", methods=['GET', 'POST'])
def gemeente_reset_wachtwoord_verzoek():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            'Er is een e-mail verzonden met instructies om het wachtwoord te '
            'veranderen'
        )
        return redirect(url_for('gemeente_login'))
    return render_template('gemeente-reset-wachtwoord-verzoek.html', form=form)


@app.route("/gemeente-reset-wachtwoord/<token>", methods=['GET', 'POST'])
def gemeente_reset_wachtwoord(token):
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.Wachtwoord.data)
        db.session.commit()
        flash('Uw wachtwoord is aangepast')
        return redirect(url_for('gemeente_login'))
    return render_template('gemeente-reset-wachtwoord.html', form=form)


@app.route("/gemeente-login", methods=['GET', 'POST'])
def gemeente_login():
    if current_user.is_authenticated:
        return redirect(url_for('gemeente_verkiezing_overzicht'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.Wachtwoord.data):
            flash('Fout e-mailadres of wachtwoord')
            return(redirect(url_for('gemeente_login')))
        login_user(user)
        return redirect(url_for('gemeente_verkiezing_overzicht'))
    return render_template('gemeente-login.html', form=form)


@app.route("/gemeente-logout")
@login_required
def gemeente_logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/gemeente-verkiezing-overzicht")
@login_required
def gemeente_verkiezing_overzicht():
    resource_data = ckan.get_resources()
    return render_template(
        'gemeente-verkiezing-overzicht.html', resource_data=resource_data)


@app.route("/gemeente-stemlokalen-overzicht/<verkiezing>", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_overzicht(verkiezing):
    result = None
    form = FileUploadForm()

    if form.validate_on_submit():
            f = form.data_file.data
            filename = secure_filename(f.filename)
            file_path = os.path.join(
                os.path.abspath(
                    os.path.join(app.instance_path, '../data-files')),
                filename)
            f.save(file_path)
            parser = UploadFileParser()
            headers, records = parser.parse(file_path)
            validator = Validator()
            result = validator.validate(headers, records)

    publish_records = ckan.get_records(
        ckan.elections[verkiezing]['publish_resource']
    )
    draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    largest_primary_key = 0
    for record in draft_records['records']:
        if record['primary_key'] > largest_primary_key:
            largest_primary_key = record['primary_key']

    publish_records = [
        record for record in publish_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]
    draft_records = [
        record for record in draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

    return render_template(
        'gemeente-stemlokalen-overzicht.html',
        verkiezing=verkiezing,
        draft_records=draft_records,
        field_order=field_order,
        new_primary_key=largest_primary_key + 1,
        form=form,
        result=result)


@app.route("/gemeente-stemlokalen-edit/<verkiezing>/<stemlokaal_id>", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_edit(verkiezing, stemlokaal_id):
    publish_records = ckan.get_records(
        ckan.elections[verkiezing]['publish_resource']
    )
    draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    publish_records = [
        record for record in publish_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]
    draft_records = [
        record for record in draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

    # Initialize the form with the data already available in the draft
    init_record = {}
    for record in draft_records:
        if record['primary_key'] == int(stemlokaal_id):
            init_record = Record(
                **{k.lower(): v for k, v in record.iteritems()}).record

    form = EditForm(**init_record)

    if form.validate_on_submit():
        record = create_record(form, stemlokaal_id, current_user)
        ckan.save_record(
            ckan.elections[verkiezing]['draft_resource'],
            record=record
        )
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht',
                verkiezing=verkiezing,
                draft_records=draft_records,
                field_order=field_order
            )
        )

    return render_template(
        'gemeente-stemlokalen-edit.html',
        verkiezing=verkiezing,
        form=form
    )

def create_record(form, stemlokaal_id, current_user):
    record = {
        'primary_key': stemlokaal_id,
        'Gemeente': current_user.gemeente_naam,
        'CBS gemeentecode': current_user.gemeente_code
    }

    for f in form:
        if f.type != 'SubmitField' and f.type != 'CSRFTokenField':
            record[f.label.text] = f.data

    return record


if __name__ == "__main__":
    app.run(threaded=True)
