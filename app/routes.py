import csv
import os
import re
import sys
from decimal import Decimal

from flask import (
    render_template, request, redirect, url_for, flash, Markup, session,
    jsonify
)
from flask_login import (
    UserMixin, login_required, login_user, logout_user, current_user
)
from werkzeug.utils import secure_filename
import sqlalchemy
from sqlalchemy import or_
from sqlalchemy.sql.expression import cast

from app import app, db
from app.forms import (
    ResetPasswordRequestForm, ResetPasswordForm, LoginForm, EditForm,
    FileUploadForm, PubliceerForm, GemeenteSelectionForm
)
from app.parser import UploadFileParser
from app.validator import Validator
from app.email import send_password_reset_email
from app.models import Gemeente, User, ckan, Record, BAG
from app.utils import find_buurt_and_wijk
from math import ceil
from time import sleep
import uuid


# Used to set the order of the fields in the stembureaus overzicht
field_order = [
    'Nummer stembureau',
    'Naam stembureau',
    'Website locatie',
    'BAG Nummeraanduiding ID',
    'Extra adresaanduiding',
    'Latitude',
    'Longitude',
    'X',
    'Y',
    'Openingstijden 14-03-2022',
    'Openingstijden 15-03-2022',
    'Openingstijden 16-03-2022',
    'Toegankelijk voor mensen met een lichamelijke beperking',
    'Akoestiek',
    'Auditieve hulpmiddelen',
    'Visuele hulpmiddelen',
    'Gehandicaptentoilet',
    'Tellocatie',
    'Contactgegevens gemeente',
    'Verkiezingswebsite gemeente',
    #'Verkiezingen'
]

# Used
default_minimal_fields = [
    'UUID',
    'Gemeente',
    'Nummer stembureau',
    'Naam stembureau',
    'Straatnaam',
    'Huisnummer',
    'Huisletter',
    'Huisnummertoevoeging',
    'Postcode',
    'Plaats',
    'Extra adresaanduiding',
    'Latitude',
    'Longitude',
    'Openingstijden 14-03-2022',
    'Openingstijden 15-03-2022',
    'Openingstijden 16-03-2022',
    'Toegankelijk voor mensen met een lichamelijke beperking',
    'Auditieve hulpmiddelen',
    'Visuele hulpmiddelen',
    'Akoestiek',
    'Gehandicaptentoilet'
]

extended_minimal_fields = default_minimal_fields + [
    #'Verkiezingen',
    'Tellocatie',
    'Website locatie',
    'Contactgegevens gemeente',
    'Verkiezingswebsite gemeente'
]

disclaimer_text = (
    "NB: Deze gemeente heeft haar stemlokaalgegevens niet zelf aangeleverd. "
    "De gegevens van de stembureaus van deze gemeente zijn door Open State "
    "Foundation zo goed mogelijk verzameld maar de correctheid en/of "
    "compleetheid ervan kan niet gegarandeerd worden."
)

disclaimer_gemeenten = []
with open('files/niet-deelnemende-gemeenten-2022-gr.csv') as IN:
    disclaimer_gemeenten = [x.strip() for x in IN.readlines()]

kieskringen = []
with open('app/data/kieskringen.csv') as IN:
    reader = csv.reader(IN, delimiter=';')
    # Skip header
    next(reader)
    kieskringen = list(reader)

# A list containing all gemeentenamen, used in the search box on the
# homepage. Also allow for some alternative municipality names.
alternative_names = [
    {'gemeente_naam': 'Den Haag'},
    {'gemeente_naam': 'Den Bosch'},
    {'gemeente_naam': 'De Friese Meren'},
    {'gemeente_naam': 'Noordoost-Friesland'},
    {'gemeente_naam': 'Zuidwest-Friesland'}
]
alle_gemeenten = [
    {'gemeente_naam': row[2]} for row in kieskringen
] + alternative_names


# Always allow admins to edit the data even if the deadline is passed
def check_deadline_passed():
    if current_user.admin:
        return False
    elif app.config['UPLOAD_DEADLINE_PASSED']:
        return True
    else:
        return False


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


# Used to only retrieve the records that are needed on a page
def _hydrate(record, minimal_type='default'):
    minimal_record = {}
    if minimal_type == 'default':
        for key, value in record.items():
            if key in default_minimal_fields:
                minimal_record[key] = value
    elif minimal_type == 'extended':
        for key, value in record.items():
            if key in extended_minimal_fields:
                minimal_record[key] = value
    return minimal_record


# Add 'Cache-Control': 'private' header if users are logged in
@app.after_request
def after_request_callback(response):
    if current_user.is_authenticated:
        response.headers['Cache-Control'] = 'private'

    return response


@app.route("/")
def index():
    records = get_stembureaus(ckan.elections)
    return render_template(
        'index.html',
        records=[_hydrate(record, 'default') for record in records],
        alle_gemeenten=alle_gemeenten,
        show_search=True
    )


@app.route("/over-deze-website")
def over_deze_website():
    return render_template('over-deze-website.html')


@app.route("/data")
def data():
    return render_template('data.html')


@app.route("/" + app.config['SIGNUP_FORM_PATH'])
def signup_form():
    return render_template(
        'signup_form.html',
        signup_form_url=app.config['SIGNUP_FORM_URL'],
        signup_form_title=app.config['SIGNUP_FORM_TITLE']
    )


@app.route("/s/<gemeente>/<primary_key>")
def show_stembureau(gemeente, primary_key):
    disclaimer = ''
    if gemeente in disclaimer_gemeenten:
        disclaimer = disclaimer_text

    records = get_stembureaus(
        ckan.elections, {'Gemeente': gemeente, 'UUID': primary_key}
    )
    return render_template(
        'show_stembureau.html',
        records=[_hydrate(record, 'extended') for record in records],
        gemeente=gemeente,
        primary_key=primary_key,
        disclaimer=disclaimer
    )


@app.route("/s/<gemeente>")
def show_gemeente(gemeente):
    disclaimer = ''
    if gemeente in disclaimer_gemeenten:
        disclaimer = disclaimer_text

    records = get_stembureaus(ckan.elections, {'Gemeente': gemeente})
    return render_template(
        'show_gemeente.html',
        records=[_hydrate(record, 'default') for record in records],
        gemeente=gemeente,
        disclaimer=disclaimer
    )


@app.route("/e/<gemeente>/<primary_key>")
def embed_stembureau(gemeente, primary_key):
    records = get_stembureaus(
        ckan.elections, {'Gemeente': gemeente, 'UUID': primary_key}
    )
    show_infobar = (request.args.get('infobar', 1, type=int) == 1)
    return render_template(
        'embed_stembureau.html',
        records=[_hydrate(record, 'extended') for record in records],
        gemeente=gemeente,
        primary_key=primary_key,
        show_infobar=show_infobar
    )


@app.route("/e/<gemeente>")
def embed_gemeente(gemeente):
    records = get_stembureaus(ckan.elections, {'Gemeente': gemeente})
    show_search = (request.args.get('search', 1, type=int) == 1)
    return render_template(
        'embed_gemeente.html',
        records=[_hydrate(record, 'default') for record in records],
        gemeente=gemeente,
        show_search=show_search
    )


@app.route("/e/alles")
def embed_alles():
    records = get_stembureaus(ckan.elections)
    show_search = (request.args.get('search', 1, type=int) == 1)
    return render_template(
        'embed_alles.html',
        records=[_hydrate(record, 'default') for record in records],
        alle_gemeenten=alle_gemeenten,
        show_search=show_search
    )


@app.route("/t/", defaults={"query": None})
@app.route("/t/<query>")
def perform_typeahead(query):
    try:
        limit = int(request.args.get('limit', '8'))
    except ValueError as e:
        limit = 8

    # Select a gemeente if none is currently selected
    if not 'selected_gemeente_code' in session:
        return redirect(url_for('gemeente_selectie'))

    gemeente = Gemeente.query.filter_by(
        gemeente_code=session['selected_gemeente_code']
    ).first()

    # Uses re.sub to remove provinces from some gemeenten which is how we write
    # gemeenten in WIMS, but which are not used in the BAG, e.g. 'Beek (L.)'
    gemeente_naam = re.sub(' \(.*\)$', '', gemeente.gemeente_naam)

    if not query:
        return jsonify([])

    results = None
    # first try postcode
    m = re.match('^(\d{4})\s*([a-zA-z]{2})\s*(\d+)?\-?([a-zA-Z0-9]+)?\s*$', query)
    if m is not None:
        postcode = m.group(1) + m.group(2).upper()
        huisnr = None
        huisnr_toev = None

        if m.group(3) is not None:
            huisnr = m.group(3)
        if m.group(4) is not None:
            huisnr_toev = m.group(4)

        results = BAG.query.filter(
            BAG.postcode == postcode,
            BAG.gemeente == gemeente_naam)

        if huisnr is not None:
            results = results.filter(BAG.huisnummer.like(huisnr + '%'))
            if huisnr_toev is not None:
                results = results.filter(or_(
                    BAG.huisnummertoevoeging.like(huisnr_toev + '%'),
                    BAG.huisletter == huisnr_toev))

    # then try if it is a nummeraanduiding
    m = re.match('^(\d{16})\s*$', query)
    if m is not None:
        results = BAG.query.filter(
            BAG.nummeraanduiding == m.group(1),
            BAG.gemeente == gemeente_naam)

    # finally, treat it as a street name
    if results is None:
        m = re.match('^(.+)\s+(\d+)\-?([a-zA-Z0-9]+)?\s*(\,\s*.*)?$', query)
        street = query
        huisnr = None
        huisnr_toev = None
        woonplaats = None
        if m is not None:
            street = m.group(1)
            huisnr = m.group(2)
            if m.group(3) is not None:
                huisnr_toev = m.group(3)
            if m.group(4) is not None:
                woonplaats = m.group(4)
        results = BAG.query.filter(
            BAG.openbareruimte.match('+' + re.sub('\s+', '* +', street.strip()) + '*'),
            BAG.gemeente == gemeente_naam)
        if huisnr is not None:
            results = results.filter(BAG.huisnummer.like(huisnr + '%'))
        if huisnr_toev is not None:
            results = results.filter(or_(
                BAG.huisnummertoevoeging.like(huisnr_toev + '%'),
                BAG.huisletter == huisnr_toev))
        if woonplaats is not None:
            results = results.filter(BAG.woonplaats.like(woonplaats[1:].strip() + '%'))

    if results is not None:
        results = results.order_by(
            BAG.woonplaats, cast(BAG.huisnummer, sqlalchemy.Integer), BAG.huisletter, BAG.huisnummertoevoeging
        ).limit(limit).all()
        return jsonify([x.to_json() for x in results])
    else:
        return jsonify([])


@app.route("/user-reset-wachtwoord-verzoek", methods=['GET', 'POST'])
def user_reset_wachtwoord_verzoek():
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


@app.route("/user-reset-wachtwoord/<token>", methods=['GET', 'POST'])
def user_reset_wachtwoord(token):
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
        return redirect(url_for('gemeente_selectie'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.Wachtwoord.data):
            flash('Fout e-mailadres of wachtwoord')
            return(redirect(url_for('gemeente_login')))
        login_user(user)
        return redirect(url_for('gemeente_selectie'))
    return render_template('gemeente-login.html', form=form)


@app.route("/gemeente-logout")
@login_required
def gemeente_logout():
    session.pop('selected_gemeente_code', None)
    logout_user()
    return redirect(url_for('index'))


@app.route(
    "/gemeente-selectie",
    methods=['GET', 'POST']
)
@login_required
def gemeente_selectie():
    if len(current_user.gemeenten) == 1:
        session[
            'selected_gemeente_code'
        ] = current_user.gemeenten[0].gemeente_code
        return redirect(url_for('gemeente_stemlokalen_dashboard'))

    gemeente_selection_form = GemeenteSelectionForm()
    gemeente_selection_form.gemeente.choices = [
        (
            gemeente.gemeente_code, gemeente.gemeente_naam
        ) for gemeente in current_user.gemeenten
    ]

    # Process selected gemeente
    if gemeente_selection_form.validate_on_submit():
        if gemeente_selection_form.submit.data:
            session[
                'selected_gemeente_code'
            ] = gemeente_selection_form.gemeente.data
            return redirect(url_for('gemeente_stemlokalen_dashboard'))

    return render_template(
        'gemeente-selectie.html',
        gemeente_selection_form=gemeente_selection_form
    )


@app.route(
    "/gemeente-stemlokalen-dashboard",
    methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokalen_dashboard():
    # Select a gemeente if none is currently selected
    if not 'selected_gemeente_code' in session:
        return redirect(url_for('gemeente_selectie'))

    gemeente = Gemeente.query.filter_by(
        gemeente_code=session['selected_gemeente_code']
    ).first()
    elections = gemeente.elections.all()

    # Pick the first election. In the case of multiple elections we only
    # retrieve the stembureaus of the first election as the records for
    # both elections are the same (at least for the GR2018 + referendum
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
        if record['CBS gemeentecode'] == gemeente.gemeente_code
    ]
    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == gemeente.gemeente_code
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
            gemeente.gemeente_naam
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
        filename = '%s__%s' % (gemeente.gemeente_code, filename)
        file_path = os.path.join(
            os.path.abspath(
                os.path.join(app.instance_path, '../upload')
            ),
            filename
        )
        f.save(file_path)
        parser = UploadFileParser()
        app.logger.info(
            'Processing uploaded file for %s' % (gemeente.gemeente_naam)
        )
        try:
            records = parser.parse(file_path)
        except ValueError as e:
            app.logger.warning('Upload failed: %s' % e)
            flash(
                Markup(
                    '<span class="text-red">Uploaden mislukt</span>. Het '
                    'lijkt er op dat u geen gebruik maakt van (de meest '
                    'recente versie van) de stembureau-spreadsheet. Download '
                    'een <a href="/files/waarismijnstemlokaal.nl_'
                    'invulformulier.xlsx"><b>leeg</b></a> of <a href="%s"><b>'
                    'deels vooringevuld</b></a> stembureau-spreadsheet en vul '
                    'de gegevens volgens de instructies in de spreadsheet in '
                    'om deze vervolgens op deze pagina te '
                    'uploaden.' % (vooringevuld)
                )
            )
            return render_template(
                'gemeente-stemlokalen-dashboard.html',
                verkiezing_string=_format_verkiezingen_string(elections),
                gemeente=gemeente,
                total_publish_records=len(gemeente_publish_records),
                total_draft_records=len(gemeente_draft_records),
                form=form,
                show_publish_note=show_publish_note,
                vooringevuld=vooringevuld,
                toon_stembureaus_pagina=toon_stembureaus_pagina,
                upload_deadline_passed=check_deadline_passed()
            )

        validator = Validator()
        results = validator.validate(records)

        # If the spreadsheet did not validate then return the errors as
        # flash messages
        if not results['no_errors']:
            flash(
                Markup(
                    '<span class="text-red">Uploaden mislukt</span>. Los de '
                    'hieronder getoonde foutmeldingen op en upload de '
                    'spreadsheet opnieuw.'
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
                        # adres_stembureau is only relevant in the webform
                        # so skip any errors it might produce for the
                        # spreadsheet
                        if column_name == 'adres_stembureau':
                            continue
                        error_flash += '<li>%s: %s</li>' % (
                            column_name, error[0]
                        )
                    error_flash += '</ul><br>'
                    flash(Markup(error_flash))
        # If there not a single value in the results then state that we
        # could not find any stembureaus
        elif not results['found_any_record_with_values']:
            flash(
                Markup(
                    '<span class="text-red">Uploaden mislukt</span>. Er zijn geen '
                    'stembureaus gevonden in de spreadsheet.'
                )
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
                            'CBS gemeentecode': gemeente.gemeente_code
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
                                gemeente,
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
        gemeente=gemeente,
        total_publish_records=len(gemeente_publish_records),
        total_draft_records=len(gemeente_draft_records),
        form=form,
        show_publish_note=show_publish_note,
        vooringevuld=vooringevuld,
        toon_stembureaus_pagina=toon_stembureaus_pagina,
        upload_deadline_passed=check_deadline_passed()
    )


@app.route("/gemeente-stemlokalen-overzicht", methods=['GET', 'POST'])
@login_required
def gemeente_stemlokalen_overzicht():
    # Select a gemeente if none is currently selected
    if not 'selected_gemeente_code' in session:
        return redirect(url_for('gemeente_selectie'))

    gemeente = Gemeente.query.filter_by(
        gemeente_code=session['selected_gemeente_code']
    ).first()
    elections = gemeente.elections.all()

    # Pick the first election. In the case of multiple elections we only
    # retrieve the stembureaus of the first election as the records for
    # both elections are the same (at least for the GR2018 + referendum
    # elections on March 21st 2018).
    verkiezing = elections[0].verkiezing

    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == gemeente.gemeente_code
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
                    if record['CBS gemeentecode'] == gemeente.gemeente_code
                ]
                _remove_id(temp_gemeente_draft_records)
                ckan.publish(election, gemeente.gemeente_code, temp_gemeente_draft_records)
            flash('Stembureaus gepubliceerd')
            # Sleep to make sure that the data is saved before it is
            # requested again in the lines right below here
            sleep(1)

    all_publish_records = ckan.get_records(
        ckan.elections[verkiezing]['publish_resource']
    )
    gemeente_publish_records = [
        record for record in all_publish_records['records']
        if record['CBS gemeentecode'] == gemeente.gemeente_code
    ]
    _remove_id(gemeente_publish_records)

    # Check whether gemeente_draft_records differs from
    # gemeente_publish_records in order to disable or enable the 'Publiceer'
    # button
    disable_publish_form = True
    if gemeente_draft_records != gemeente_publish_records:
        disable_publish_form = False

    return render_template(
        'gemeente-stemlokalen-overzicht.html',
        verkiezing_string=_format_verkiezingen_string(elections),
        gemeente=gemeente,
        draft_records=gemeente_draft_records,
        field_order=field_order,
        publish_form=publish_form,
        disable_publish_form=disable_publish_form,
        upload_deadline_passed=check_deadline_passed()
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
    # Select a gemeente if none is currently selected
    if not 'selected_gemeente_code' in session:
        return redirect(url_for('gemeente_selectie'))

    gemeente = Gemeente.query.filter_by(
        gemeente_code=session['selected_gemeente_code']
    ).first()
    elections = gemeente.elections.all()

    # Need this to get a starting point for the clickmap;
    # Uses re.sub to remove provinces from some gemeenten which is how we write
    # gemeenten in WIMS, but which are not used in the BAG, e.g. 'Beek (L.)'
    # TODO this won't work for BES-eilanden as they don't exist in the BAG, so
    # exclude them from the filter below and initialize a custom bag_record
    # with coordinates for the BES-eilanden.
    bag_record = BAG.query.filter_by(
        gemeente=re.sub(' \(.*\)$', '', gemeente.gemeente_naam)
    ).order_by('openbareruimte').first()

    # Pick the first election. In the case of multiple elections we only
    # retrieve the stembureaus of the first election as the records for
    # both elections are the same (at least for the GR2018 + referendum
    # elections on March 21st 2018).
    verkiezing = elections[0].verkiezing

    all_draft_records = ckan.get_records(
        ckan.elections[verkiezing]['draft_resource']
    )

    gemeente_draft_records = [
        record for record in all_draft_records['records']
        if record['CBS gemeentecode'] == gemeente.gemeente_code
    ]

    # Initialize the form with the data already available in the draft
    init_record = {}
    if stemlokaal_id:
        for record in gemeente_draft_records:
            if record['UUID'] == stemlokaal_id:
                # Split the Verkiezingen attribute into a list
                if record['Verkiezingen']:
                    record['Verkiezingen'] = [
                        x.strip() for x in record['Verkiezingen'].split(';')
                    ]
                init_record = Record(
                    **{k.lower(): v for k, v in record.items()}
                ).record

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
                gemeente,
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
        gemeente=gemeente,
        bag_record=bag_record,
        upload_deadline_passed=check_deadline_passed()
    )


@app.route(
    "/gemeente-stemlokaal-delete/<stemlokaal_id>",
    methods=['GET', 'POST']
)
@login_required
def gemeente_stemlokaal_delete(stemlokaal_id=None):
    # Select a gemeente if none is currently selected
    if not 'selected_gemeente_code' in session:
        return redirect(url_for('gemeente_selectie'))

    gemeente = Gemeente.query.filter_by(
        gemeente_code=session['selected_gemeente_code']
    ).first()
    elections = gemeente.elections.all()

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

@app.route("/gemeente-instructies")
@login_required
def gemeente_instructies():
    # Select a gemeente if none is currently selected
    if not 'selected_gemeente_code' in session:
        return redirect(url_for('gemeente_selectie'))

    gemeente = Gemeente.query.filter_by(
        gemeente_code=session['selected_gemeente_code']
    ).first()
    return render_template(
        'gemeente-instructies.html',
        gemeente=gemeente,
        signup_form_url=app.config['SIGNUP_FORM_URL']
    )


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


def _create_record(form, stemlokaal_id, gemeente, election):
    ID = 'NLODS%sstembureaus%s%s' % (
        gemeente.gemeente_code,
        app.config['CKAN_CURRENT_ELECTIONS'][election]['election_date'],
        app.config['CKAN_CURRENT_ELECTIONS'][election]['election_number']
    )

    kieskring_id = ''
    hoofdstembureau = ''
    if (election.startswith('Gemeenteraadsverkiezingen') or
            election.startswith('Kiescollegeverkiezingen') or
            election.startswith('Eilandsraadsverkiezingen')):
        kieskring_id = gemeente.gemeente_naam
        hoofdstembureau = gemeente.gemeente_naam
    elif (election.startswith('Referendum') or
            election.startswith('Tweede Kamerverkiezingen') or
            election.startswith('Provinciale Statenverkiezingen')):
        for row in kieskringen:
            if row[2] == gemeente.gemeente_naam:
                kieskring_id = row[0]
                hoofdstembureau = row[1]
    elif election.startswith('Europese Parlementsverkiezingen'):
        kieskring_id = 'Nederland'
        hoofdstembureau = 'Nederland'

    record = {
        'UUID': stemlokaal_id,
        'Gemeente': gemeente.gemeente_naam,
        'CBS gemeentecode': gemeente.gemeente_code,
        'Kieskring ID': kieskring_id,
        'Hoofdstembureau': hoofdstembureau,
        'ID': ID
    }

    # Process the fields from the form
    for f in form:
        # Save the Verkiezingen by joining the list into a string
        if f.label.text == 'Verkiezingen':
            record[f.label.text] = ';'.join(f.data)
        elif (f.type != 'SubmitField' and
                f.type != 'CSRFTokenField' and f.type != 'RadioField'):
            record[f.label.text[:62]] = f.data

    # prevent this field from being saved as it is not a real form field.
    del record['Adres stembureau']

    bag_nummer = record['BAG Nummeraanduiding ID']
    bag_record = BAG.query.filter_by(nummeraanduiding=bag_nummer).first()

    if bag_record is not None:
        bag_conversions = {
            'verblijfsobjectgebruiksdoel': 'Gebruiksdoel van het gebouw',
            'openbareruimte': 'Straatnaam',
            'huisnummer': 'Huisnummer',
            'huisletter': 'Huisletter',
            'huisnummertoevoeging': 'Huisnummertoevoeging',
            'postcode': 'Postcode',
            'woonplaats': 'Plaats',
            'lat': 'Latitude',
            'lon': 'Longitude',
            'x': 'X',
            'y': 'Y'
        }

        for bag_field, record_field in bag_conversions.items():
            bag_field_value = getattr(bag_record, bag_field, None)
            if bag_field_value is not None:
                if isinstance(bag_field_value, Decimal):
                    # do not overwrite geocoordinates if they were otherwise specified
                    if not record.get(record_field):
                        record[record_field] = float(bag_field_value)
                else:
                    record[record_field] = bag_field_value.encode(
                        'utf-8'
                    ).decode()
            else:
                record[record_field] = None

        ## We stopped adding the wijk and buurt data as the data
        ## supplied by CBS is not up to date enough as it is only
        ## released once a year and many months after changes
        ## have been made by the municipalities.
        #wk_code, wk_naam, bu_code, bu_naam = find_buurt_and_wijk(
        #    bag_nummer,
        #    gemeente.gemeente_code,
        #    bag_record.lat,
        #    bag_record.lon
        #)
        #if wk_naam:
        #    record['Wijknaam'] = wk_naam
        #if wk_code:
        #    record['CBS wijknummer'] = wk_code
        #if bu_naam:
        #    record['Buurtnaam'] = bu_naam
        #if bu_code:
        #    record['CBS buurtnummer'] = bu_code

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
