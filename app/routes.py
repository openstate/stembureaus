import csv
import os
import sys

from flask import render_template, request, redirect, url_for, flash, Markup
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
from app.models import User, ckan, Record, BAG
from app.utils import find_buurt_and_wijk
from math import ceil
from time import sleep
import uuid


# Used to set the order of the fields in the stembureaus overzicht
field_order = [
    'Nummer stembureau',
    'Naam stembureau',
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
    'Contactgegevens',
    'Beschikbaarheid'
]


kieskringen = []
with open('app/data/kieskringen.csv') as IN:
    reader = csv.reader(IN, delimiter=';')
    kieskringen = list(reader)

# A list containing all gemeentenamen, used in the search box on the
#homepage
alle_gemeenten = [{'gemeente_naam': row[2]} for row in kieskringen]


def get_stembureaus(elections, filters=None):
    merge_field = 'UUID'
    results = {}
    for election in elections.keys():
        records = ckan.filter_records(
            ckan.elections[election]['publish_resource'],
            filters)
        for record in records['records']:
            if record[merge_field] not in results:
                results[record[merge_field]] = record
            try:
                results[record[merge_field]]['elections'].append(election)
            except LookupError:
                results[record[merge_field]]['elections'] = [election]

    return results.values()


def _hydrate(r):
    del r['Beschikbaarheid']
    del r['Contactgegevens']
    del r['Gebruikersdoel het gebouw']
    del r['Website locatie']
    del r['X']
    del r['Y']
    del r['ID']
    del r['BAG referentienummer']
    del r['Districtcode']
    del r['Hoofdstembureau']
    del r['Kieskring ID']
    del r['Wijknaam']
    del r['Buurtnaam']
    return r


@app.route("/")
def index():
    records = get_stembureaus(ckan.elections)
    return render_template(
        'index.html',
        records=[_hydrate(r) for r in records],
        alle_gemeenten=alle_gemeenten
    )


@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')


@app.route("/data")
def data():
    return render_template('data.html')


@app.route("/s/<gemeente>/<primary_key>")
def show_stembureau(gemeente, primary_key):
    records = get_stembureaus(
        ckan.elections, {'Gemeente': gemeente, 'UUID': primary_key}
    )
    return render_template(
        'show_stembureau.html',
        records=[_hydrate(r) for r in records],
        gemeente=gemeente,
        primary_key=primary_key
    )


@app.route("/s/<gemeente>")
def show_gemeente(gemeente):
    records = get_stembureaus(ckan.elections, {'Gemeente': gemeente})
    return render_template(
        'show_gemeente.html',
        records=[_hydrate(r) for r in records],
        gemeente=gemeente
    )


@app.route("/e/<gemeente>/<primary_key>")
def embed_stembureau(gemeente, primary_key):
    records = get_stembureaus(
        ckan.elections, {'Gemeente': gemeente, 'UUID': primary_key})
    return render_template(
        'embed_stembureau.html', records=[_hydrate(r) for r in records],
        gemeente=gemeente)


@app.route("/e/<gemeente>")
def embed_gemeente(gemeente):
    records = get_stembureaus(ckan.elections, {'Gemeente': gemeente})
    show_search = (request.args.get('search', 1, type=int) == 1)
    return render_template(
        'embed_gemeente.html',
        records=[_hydrate(r) for r in records],
        gemeente=gemeente,
        show_search=show_search
    )


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
        return redirect(url_for('gemeente_stemlokalen_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.Wachtwoord.data):
            flash('Fout e-mailadres of wachtwoord')
            return(redirect(url_for('gemeente_login')))
        login_user(user)
        return redirect(url_for('gemeente_stemlokalen_dashboard'))
    return render_template('gemeente-login.html', form=form)


@app.route("/gemeente-logout")
@login_required
def gemeente_logout():
    logout_user()
    return redirect(url_for('index'))


@app.route(
    "/gemeente-stemlokalen-dashboard",
    methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokalen_dashboard():
    elections = current_user.elections.all()

    # Pick the first election. In the case of multiple elections we only
    # retrieve the stembureaus of the first election as the records for
    # both elections are the same (at least the GR2018 + referendum
    # elections on March 21st 2018).
    verkiezing = elections[0].verkiezing

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

    _remove_id(gemeente_publish_records)
    _remove_id(gemeente_draft_records)

    toon_stembureaus_pagina = False
    if gemeente_publish_records:
        toon_stembureaus_pagina = True

    show_publish_note = False
    if gemeente_draft_records != gemeente_publish_records:
        show_publish_note = True

    vooringevuld = ''
    vooringevuld_fn = (
        'files/deels_vooringevuld/waarismijnstemlokaal.nl_invulformulier_%s_'
        'deels_vooringevuld.xlsx' % (
            current_user.gemeente_naam
        )
    )
    if os.path.exists(vooringevuld_fn):
        vooringevuld = vooringevuld_fn

    form = FileUploadForm()

    # Save, parse and validate an uploaded spreadsheet and save the
    # stembureaus
    if form.validate_on_submit():
        f = form.data_file.data
        filename = secure_filename(f.filename)
        filename = '%s__%s' % (current_user.gemeente_code, filename)
        file_path = os.path.join(
            os.path.abspath(
                os.path.join(app.instance_path, '../upload')
            ),
            filename
        )
        f.save(file_path)
        parser = UploadFileParser()
        app.logger.info(
            'Processing uploaded file for %s' % (current_user.gemeente_naam)
        )
        try:
            records = parser.parse(file_path)
        except ValueError as e:
            app.logger.warning('Upload failed: %s' % e)
            flash(
                Markup(
                    'Uploaden mislukt. Het lijkt er op dat u geen gebruik '
                    'maakt van de stembureau-spreadsheet. Download de '
                    '<a href="/files/waarismijnstemlokaal.nl_invulformulier'
                    '.xlsx"><b>stembureaus-spreadsheet</b></a> en vul de '
                    'gegevens volgens de instructies in de spreadsheet in om '
                    'deze vervolgens op deze pagina te uploaden.'
                )
            )
            return render_template(
                'gemeente-stemlokalen-dashboard.html',
                verkiezing_string=_format_verkiezingen_string(elections),
                total_publish_records=len(gemeente_publish_records),
                total_draft_records=len(gemeente_draft_records),
                form=form,
                show_publish_note=show_publish_note,
                vooringevuld=vooringevuld,
                toon_stembureaus_pagina=toon_stembureaus_pagina,
                upload_deadline_passed=app.config['UPLOAD_DEADLINE_PASSED']
            )

        validator = Validator()
        results = validator.validate(records)

        # If the spreadsheet did not validate then return the errors as
        # flash messages
        if not results['no_errors']:
            flash(
                Markup(
                    'Uploaden mislukt. Los de hieronder getoonde '
                    'foutmeldingen op en upload de spreadsheet opnieuw.'
                    '<br><br>'
                )
            )
            for column_number, col_result in sorted(
                    results['results'].items()):
                if col_result['errors']:
                    error_flash = (
                        '<b>Foutmelding(en) in <span class="text-red">'
                        'invulveld %s (oftewel kolom "%s")</span></b>:' % (
                            column_number - 5,
                            _colnum2string(column_number)
                        )
                    )
                    error_flash += '<ul>'
                    for column_name, error in col_result['errors'].items():
                        error_flash += '<li>%s: %s</li>' % (
                            column_name, error[0]
                        )
                    error_flash += '</ul><br>'
                    flash(Markup(error_flash))
        # If there not a single value in the results then state that we
        # could not find any stembureaus
        elif not results['found_any_record_with_values']:
            flash(
                'Uploaden mislukt. Er zijn geen stembureaus gevonden in de '
                'spreadsheet.'
            )
        # If the spreadsheet did validate then first delete all current
        # stembureaus from the draft_resource and then save the newly
        # uploaded stembureaus to the draft_resources of each election
        # and finally redirect to the overzicht
        else:
            # Delete all stembureaus of current gemeente
            if gemeente_draft_records:
                for election in [x.verkiezing for x in elections]:
                    ckan.delete_records(
                        ckan.elections[election]['draft_resource'],
                        {
                            'CBS gemeentecode': current_user.gemeente_code
                        }
                    )

            # Create and save records
            for election in [x.verkiezing for x in elections]:
                records = []
                for _, result in results['results'].items():
                    if result['form']:
                        records.append(
                            _create_record(
                                result['form'],
                                result['uuid'],
                                current_user,
                                election
                            )
                        )
                ckan.save_records(
                    ckan.elections[election]['draft_resource'],
                    records=records
                )

            flash(
                'Het uploaden van stembureaus is gelukt! Controleer in het '
                'overzicht hieronder of alles klopt en voer eventuele '
                'wijzigingen door. Klik vervolgens op de "Publiceer"-knop als '
                'alles klopt.'
            )
            return redirect(
                url_for(
                    'gemeente_stemlokalen_overzicht'
                )
            )

    return render_template(
        'gemeente-stemlokalen-dashboard.html',
        verkiezing_string=_format_verkiezingen_string(elections),
        total_publish_records=len(gemeente_publish_records),
        total_draft_records=len(gemeente_draft_records),
        form=form,
        show_publish_note=show_publish_note,
        vooringevuld=vooringevuld,
        toon_stembureaus_pagina=toon_stembureaus_pagina,
        upload_deadline_passed=app.config['UPLOAD_DEADLINE_PASSED']
    )


@app.route("/gemeente-stemlokalen-overzicht", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_overzicht():
    elections = current_user.elections.all()

    # Pick the first election. In the case of multiple elections we only
    # retrieve the stembureaus of the first election as the records for
    # both elections are the same (at least the GR2018 + referendum
    # elections on March 21st 2018).
    verkiezing = elections[0].verkiezing

    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

    _remove_id(gemeente_draft_records)

    publish_form = PubliceerForm()

    # Publiceren
    if publish_form.validate_on_submit():
        if publish_form.submit.data:
            # Publish stembureaus to all elections
            for election in [x.verkiezing for x in elections]:
                temp_all_draft_records = ckan.get_records(
                    ckan.elections[election]['draft_resource']
                )
                temp_gemeente_draft_records = [
                    record for record in temp_all_draft_records['records']
                    if record['CBS gemeentecode'] == current_user.gemeente_code
                ]
                _remove_id(temp_gemeente_draft_records)
                ckan.publish(election, temp_gemeente_draft_records)
            flash('Stembureaus gepubliceerd')
            # Sleep to make sure that the data is saved before it is
            # requested again in the lines right below here
            sleep(1)

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
    disable_publish_form = True
    if gemeente_draft_records != gemeente_publish_records:
        disable_publish_form = False

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
            page=page - 1
        )
    next_url = None
    if len(gemeente_draft_records) > page * posts_per_page:
        next_url = url_for(
            'gemeente_stemlokalen_overzicht',
            page=page + 1
        )

    return render_template(
        'gemeente-stemlokalen-overzicht.html',
        verkiezing_string=_format_verkiezingen_string(elections),
        draft_records=paged_draft_records,
        field_order=field_order,
        publish_form=publish_form,
        disable_publish_form=disable_publish_form,
        page=page,
        start_record=start_record + 1,
        end_record=end_record,
        total_records=len(gemeente_draft_records),
        total_pages=ceil(len(gemeente_draft_records)/posts_per_page),
        previous_url=previous_url,
        next_url=next_url,
        upload_deadline_passed=app.config['UPLOAD_DEADLINE_PASSED']
    )


@app.route(
    "/gemeente-stemlokalen-edit",
    methods=['GET', 'POST']
)
@app.route(
    "/gemeente-stemlokalen-edit/<stemlokaal_id>",
    methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokalen_edit(stemlokaal_id=None):
    elections = current_user.elections.all()

    # Pick the first election. In the case of multiple elections we only
    # retrieve the stembureaus of the first election as the records for
    # both elections are the same (at least the GR2018 + referendum
    # elections on March 21st 2018).
    verkiezing = elections[0].verkiezing

    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == current_user.gemeente_code
    ]

    # Initialize the form with the data already available in the draft
    init_record = {}
    if stemlokaal_id:
        for record in gemeente_draft_records:
            if record['UUID'] == stemlokaal_id:
                init_record = Record(
                    **{k.lower(): v for k, v in record.items()}).record

    form = EditForm(**init_record)

    # When the user clicked the 'Annuleren' button go back to the
    # overzicht page without doing anything
    if form.submit_annuleren.data:
        flash('Bewerking geannuleerd')
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht'
            )
        )

    # When the user clicked the 'Verwijderen' button delete the
    # stembureau from the draft_resources of each election
    if form.submit_verwijderen.data:
        if stemlokaal_id:
            for election in [x.verkiezing for x in elections]:
                ckan.delete_records(
                    ckan.elections[election]['draft_resource'],
                    {'UUID': stemlokaal_id}
                )
        flash('Stembureau verwijderd')
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht'
            )
        )
    # When the user clicked the 'Opslaan' button save the stembureau
    # to the draft_resources of each election
    if form.validate_on_submit():
        if not stemlokaal_id:
            stemlokaal_id = uuid.uuid4().hex
        for election in [x.verkiezing for x in elections]:
            record = _create_record(
                form,
                stemlokaal_id,
                current_user,
                election
            )
            ckan.save_records(
                ckan.elections[election]['draft_resource'],
                records=[record]
            )
        flash('Stembureau opgeslagen')
        return redirect(
            url_for(
                'gemeente_stemlokalen_overzicht'
            )
        )

    return render_template(
        'gemeente-stemlokalen-edit.html',
        form=form,
        upload_deadline_passed=app.config['UPLOAD_DEADLINE_PASSED']
    )


@app.route("/gemeente-instructies")
@login_required
def gemeente_instructies():
    return render_template('gemeente-instructies.html')


# Format string containing the verkiezingen
def _format_verkiezingen_string(elections):
    verkiezing_string = ''
    verkiezingen = ['<b>' + x.verkiezing + '</b>' for x in elections]
    if len(verkiezingen) > 1:
        verkiezing_string = ', '.join(verkiezingen[:-1])
        verkiezing_string += ' en %s' % (verkiezingen[-1])
    else:
        verkiezing_string = verkiezingen[0]

    return verkiezing_string


def _create_record(form, stemlokaal_id, current_user, election):
    ID = 'NLODS%sstembureaus%s%s' % (
        current_user.gemeente_code,
        app.config['CKAN_CURRENT_ELECTIONS'][election]['election_date'],
        app.config['CKAN_CURRENT_ELECTIONS'][election]['election_number']
    )

    kieskring_id = ''
    hoofdstembureau = ''
    if election.startswith('Gemeenteraadsverkiezingen'):
        kieskring_id = current_user.gemeente_naam
        hoofdstembureau = current_user.gemeente_naam
    if election.startswith('Referendum'):
        for row in kieskringen:
            if row[2] == current_user.gemeente_naam:
                kieskring_id = row[0]
                hoofdstembureau = row[1]

    record = {
        'UUID': stemlokaal_id,
        'Gemeente': current_user.gemeente_naam,
        'CBS gemeentecode': current_user.gemeente_code,
        'Kieskring ID': kieskring_id,
        'Hoofdstembureau': hoofdstembureau,
        'ID': ID
    }

    for f in form:
        if f.type != 'SubmitField' and f.type != 'CSRFTokenField':
            record[f.label.text] = f.data

    bag_nummer = record['BAG referentienummer']
    bag_record = BAG.query.get(bag_nummer)

    if bag_record is not None:
        bag_conversions = {
            'verblijfsobjectgebruiksdoel': 'Gebruikersdoel het gebouw',
            'openbareruimte': 'Straatnaam',
            'huisnummer': 'Huisnummer',
            'huisnummertoevoeging': 'Huisnummertoevoeging',
            'postcode': 'Postcode',
            'woonplaats': 'Plaats',
        }

        for bag_field, record_field in bag_conversions.items():
            bag_field_value = getattr(bag_record, bag_field, None)
            if bag_field_value is not None:
                record[record_field] = bag_field_value.encode(
                    'latin1'
                ).decode()
            else:
                record[record_field] = None
        wk_code, wk_naam, bu_code, bu_naam = find_buurt_and_wijk(
            bag_nummer,
            current_user.gemeente_code,
            bag_record.lon,
            bag_record.lat
        )
        if wk_naam:
            record['Wijknaam'] = wk_naam
        if wk_code:
            record['CBS wijknummer'] = wk_code
        if bu_naam:
            record['Buurtnaam'] = bu_naam
        if bu_code:
            record['CBS buurtnummer'] = bu_code

    return record


# Remove '_id' as CKAN doesn't accept this field in upsert when we
# want to publish and '_id' is almost never the same in
# publish_records and draft_records so we need to remove it in order
# to compare them
def _remove_id(records):
    for record in records:
        del record['_id']


# Converts a column number to a spreadsheet column string, e.g. 6 to F
# and 124 to DT
def _colnum2string(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


if __name__ == "__main__":
    app.run(threaded=True)
