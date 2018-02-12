import os

from flask import render_template, request, redirect, url_for, flash
from flask_login import (
    UserMixin, login_required, login_user, logout_user, current_user)
from werkzeug.utils import secure_filename

from app import app, db
from app.forms import (
    ResetPasswordRequestForm, ResetPasswordForm, LoginForm, EditForm,
    FileUploadForm, PubliceerForm)
from app.parser import UploadFileParser
from app.validator import Validator
from app.email import send_password_reset_email
from app.models import User, ckan, Record
from math import ceil


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
    return render_template(
        'gemeente-verkiezing-overzicht.html',
        elections=ckan.elections
    )


@app.route(
    "/gemeente-stemlokalen-dashboard/<verkiezing>",
    methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokalen_dashboard(verkiezing):
    all_publish_records = ckan.get_records(
        ckan.elections[verkiezing]['publish_resource']
    )
    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    gemeente_publish_records = [
        record for record in all_publish_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]
    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

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


    return render_template(
        'gemeente-stemlokalen-dashboard.html',
        verkiezing=verkiezing,
        total_publish_records=len(gemeente_publish_records),
        total_draft_records=len(gemeente_draft_records),
        form=form,
        result=result
    )


@app.route(
    "/gemeente-stemlokalen-overzicht/<verkiezing>", methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokalen_overzicht(verkiezing):
    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    # Find the current largest primary_key value in order to create a
    # new primary_key value when the user wants to add a new stembureau
    largest_primary_key = 0
    for record in all_draft_records['records']:
        if record['primary_key'] > largest_primary_key:
            largest_primary_key = record['primary_key']

    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

    _remove_id(gemeente_draft_records)

    form = PubliceerForm()

    if form.validate_on_submit():
        if form.submit.data:
            ckan.publish(
                verkiezing, gemeente_draft_records
            )
            flash('Stembureaus gepubliceerd')

    all_publish_records = ckan.get_records(
        ckan.elections[verkiezing]['publish_resource']
    )
    gemeente_publish_records = [
        record for record in all_publish_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]
    _remove_id(gemeente_publish_records)

    # Check whether gemeente_draft_records differs from
    # gemeente_publish_records in order to disable or enable the 'Publiceer'
    # button
    show_form = False
    if gemeente_draft_records != gemeente_publish_records:
        show_form = True

    # Pagination
    posts_per_page = app.config['POSTS_PER_PAGE']
    page = request.args.get('page', 1, type=int)

    # Use page 1 if a page lower than 1 is requested
    if page < 1:
        page = 1

    # If the user requests a page larger than the largest page for which
    # we have records to show, use that page instead of the requested
    # one
    if page > ceil(len(gemeente_draft_records) / posts_per_page):
        page = ceil(len(gemeente_draft_records) / posts_per_page)

    start_record = (page - 1) * posts_per_page
    end_record = page * posts_per_page
    if end_record > len(gemeente_draft_records):
        end_record = len(gemeente_draft_records)
    paged_draft_records = gemeente_draft_records[start_record:end_record]

    previous_url = None
    if page > 1:
        previous_url = url_for(
            'gemeente_stemlokalen_overzicht',
            verkiezing=verkiezing,
            page=page - 1
        )
    next_url = None
    if len(gemeente_draft_records) > page * posts_per_page:
        next_url = url_for(
            'gemeente_stemlokalen_overzicht',
            verkiezing=verkiezing,
            page=page + 1
        )

    return render_template(
        'gemeente-stemlokalen-overzicht.html',
        verkiezing=verkiezing,
        draft_records=paged_draft_records,
        field_order=field_order,
        show_form=show_form,
        new_primary_key=largest_primary_key + 1,
        page=page,
        start_record=start_record + 1,
        end_record=end_record,
        total_records=len(gemeente_draft_records),
        previous_url=previous_url,
        next_url=next_url,
        form=form
    )


@app.route(
    "/gemeente-stemlokalen-edit/<verkiezing>/<stemlokaal_id>",
    methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokalen_edit(verkiezing, stemlokaal_id):
    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

    # Initialize the form with the data already available in the draft
    init_record = {}
    for record in gemeente_draft_records:
        if record['primary_key'] == int(stemlokaal_id):
            init_record = Record(
                **{k.lower(): v for k, v in record.items()}).record

    form = EditForm(**init_record)

    # When the user clicked the 'Annuleren' button go back to the
    # overzicht page without doing anything
    if form.submit_annuleren.data:
        flash('Bewerking geannuleerd')
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht',
                verkiezing=verkiezing
            )
        )

    # When the user clicked the 'Verwijderen' button delete the
    # stembureau from the draft_resource
    if form.submit_verwijderen.data:
        ckan.delete_records(
            ckan.elections[verkiezing]['draft_resource'],
            {'primary_key': stemlokaal_id}
        )
        flash('Stembureau verwijderd')
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht',
                verkiezing=verkiezing
            )
        )

    if form.validate_on_submit():
        record = _create_record(form, stemlokaal_id, current_user)
        ckan.save_records(
            ckan.elections[verkiezing]['draft_resource'],
            records=[record]
        )
        flash('Stembureau opgeslagen')
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht',
                verkiezing=verkiezing
            )
        )

    return render_template(
        'gemeente-stemlokalen-edit.html',
        verkiezing=verkiezing,
        form=form
    )


def _create_record(form, stemlokaal_id, current_user):
    record = {
        'primary_key': stemlokaal_id,
        'Gemeente': current_user.gemeente_naam,
        'CBS gemeentecode': current_user.gemeente_code
    }

    for f in form:
        if f.type != 'SubmitField' and f.type != 'CSRFTokenField':
            record[f.label.text] = f.data

    return record


# Remove '_id' as CKAN doesn't accept this field in upsert when we
# want to publish and '_id' is almost never the same in
# publish_records and draft_records so we need to remove it in order
# to compare them
def _remove_id(records):
    for record in records:
        del record['_id']


if __name__ == "__main__":
    app.run(threaded=True)
