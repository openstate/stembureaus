from app import app, db
from app.models import User, ckan, Election
from app.email import send_invite, send_mailcorrectie
from app.parser import UploadFileParser
from app.validator import Validator
from app.routes import _remove_id, _create_record
from datetime import datetime
from flask import url_for
from pprint import pprint
import click
import json
import os
import uuid


# CKAN (use uppercase to avoid conflict with 'ckan' import from
# app.models)
@app.cli.group()
def CKAN():
    """ckan commands"""
    pass


@CKAN.command()
def toon_verkiezingen():
    """
    Toon alle huidige verkiezingen en de bijbehornde public en draft
    resources
    """
    pprint(ckan.elections)


@CKAN.command()
@click.argument('resource_id')
def maak_nieuwe_datastore(resource_id):
    """
    Maak een nieuwe datastore tabel in een resource
    """
    fields = [
        {
            "id": "Gemeente",
            "type": "text"
        },
        {
            "id": "CBS gemeentecode",
            "type": "text"
        },
        {
            "id": "Nummer stembureau",
            "type": "int"
        },
        {
            "id": "Naam stembureau",
            "type": "text"
        },
        {
            "id": "Gebruikersdoel het gebouw",
            "type": "text"
        },
        {
            "id": "Website locatie",
            "type": "text"
        },
        {
            "id": "Wijknaam",
            "type": "text"
        },
        {
            "id": "CBS wijknummer",
            "type": "text"
        },
        {
            "id": "Buurtnaam",
            "type": "text"
        },
        {
            "id": "CBS buurtnummer",
            "type": "text"
        },
        {
            "id": "BAG referentienummer",
            "type": "text"
        },
        {
            "id": "Straatnaam",
            "type": "text"
        },
        {
            "id": "Huisnummer",
            "type": "text"
        },
        {
            "id": "Huisnummertoevoeging",
            "type": "text"
        },
        {
            "id": "Postcode",
            "type": "text"
        },
        {
            "id": "Plaats",
            "type": "text"
        },
        {
            "id": "Extra adresaanduiding",
            "type": "text"
        },
        {
            "id": "X",
            "type": "int"
        },
        {
            "id": "Y",
            "type": "int"
        },
        {
            "id": "Longitude",
            "type": "float"
        },
        {
            "id": "Latitude",
            "type": "float"
        },
        {
            "id": "Districtcode",
            "type": "text"
        },
        {
            "id": "Openingstijden",
            "type": "text"
        },
        {
            "id": "Mindervaliden toegankelijk",
            "type": "text"
        },
        {
            "id": "Invalidenparkeerplaatsen",
            "type": "text"
        },
        {
            "id": "Akoestiek",
            "type": "text"
        },
        {
            "id": "Mindervalide toilet aanwezig",
            "type": "text"
        },
        {
            "id": "Kieskring ID",
            "type": "text"
        },
        {
            "id": "Hoofdstembureau",
            "type": "text"
        },
        {
            "id": "Contactgegevens",
            "type": "text"
        },
        {
            "id": "Beschikbaarheid",
            "type": "text"
        },
        {
            "id": "ID",
            "type": "text"
        },
        {
            "id": "UUID",
            "type": "text"
        }
    ]

    ckan.create_datastore(resource_id, fields)


@CKAN.command()
@click.argument('gemeente_code')
@click.argument('file_path')
def upload_stembureau_spreadsheet(gemeente_code, file_path):
    """
    Uploads a stembureau spreadheet, specify full absolute file_path
    """
    current_user = _get_user(gemeente_code)

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

    parser = UploadFileParser()
    app.logger.info(
        'Manually (CLI) uploading file for %s' % (current_user.gemeente_naam)
    )
    try:
        headers, records = parser.parse(file_path)
    except ValueError as e:
        app.logger.warning('Manual upload failed: %s' % e)
        return

    validator = Validator()
    results = validator.validate(headers, records)

    # If the spreadsheet did not validate then return the errors
    if not results['no_errors']:
        print(
            'Uploaden mislukt. Los de hieronder getoonde '
            'foutmeldingen op en upload de spreadsheet opnieuw.\n\n'
        )
        for column_number, col_result in sorted(
                results['results'].items()):
            if col_result['errors']:
                print(
                    'Foutmelding(en) in '
                    'invulveld %s:' % (
                        column_number - 5
                    )
                )
                for column_name, error in col_result['errors'].items():
                    print(
                        '%s: %s\n' % (
                            column_name, error[0]
                        )
                    )
    # If there not a single value in the results then state that we
    # could not find any stembureaus
    elif not results['found_any_record_with_values']:
        print(
            'Uploaden mislukt. Er zijn geen stembureaus gevonden in de '
            'spreadsheet.'
        )
    # If the spreadsheet did validate then first delete all current
    # stembureaus from the draft_resource and then save the newly
    # uploaded stembureaus to the draft_resources of each election
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
        print('Uploaden gelukt!')
    print('\n\n')


@CKAN.command()
@click.argument('gemeente_code')
def publish_gemeente(gemeente_code):
    """
    Publishes the saved (draft) stembureaus of a gemeente
    """
    current_user = _get_user(gemeente_code)

    elections = current_user.elections.all()

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


@CKAN.command()
@click.argument('gemeente_code')
@click.argument('source_resource')
@click.argument('dest_resource')
@click.option('--dest_id', '-di')
@click.option('--dest_hoofdstembureau', '-dh')
@click.option('--dest_kieskring_id', '-dk')
def copy_gemeente_resource(gemeente_code, source_resource, dest_resource, dest_id=None,
        dest_hoofdstembureau=None, dest_kieskring_id=None):
    """
    Copies the records of a gemeente from one resource (source) to another
    (dest). Note: this removes all records for the gemeente in dest first.
    If dest contains no records then you need to specify the ID,
    Hoofdstembureau and Kieskring ID value for the gemeente in the dest
    resource.
    """
    all_resource_records = ckan.get_records(source_resource)
    gemeente_resource_records = [
        record for record in all_resource_records['records']
        if record['CBS gemeentecode'] == gemeente_code
    ]
    _remove_id(gemeente_resource_records)

    # If either one of these parameters is not set then try to get the
    # values from the dest_resource
    if not dest_id or not dest_hoofdstembureau or not dest_kieskring_id:
        all_dest_resource_records = ckan.get_records(dest_resource)
        gemeente_dest_resource_records = [
            record for record in all_dest_resource_records['records']
            if record['CBS gemeentecode'] == gemeente_code
        ]
        if gemeente_dest_resource_records:
            dest_id = gemeente_dest_resource_records[0]['ID']
            dest_hoofdstembureau = gemeente_dest_resource_records[0][
                'Hoofdstembureau'
            ]
            dest_kieskring_id = gemeente_dest_resource_records[0]['Kieskring ID']

    # If either of these is still not set, abort!
    if not dest_id or not dest_hoofdstembureau or not dest_kieskring_id:
        print(
            'Could not retrieve dest_id or dest_hoofdstembureau or '
            'dest_kieskring_id'
        )

    for record in gemeente_resource_records:
        record['ID'] = dest_id
        record['Hoofdstembureau'] = dest_hoofdstembureau
        record['Kieskring ID'] = dest_kieskring_id

    ckan.delete_records(
        dest_resource,
        {'CBS gemeentecode': gemeente_code}
    )
    ckan.save_records(dest_resource, gemeente_resource_records)


@CKAN.command()
@click.argument('resource_id')
def export_resource(resource_id):
    """
    Exports all records of a resource to a json file in the exports directory
    """
    all_resource_records = ckan.get_records(resource_id)['records']
    filename = 'exports/%s_%s.json' % (
        datetime.now().isoformat()[:19],
        resource_id
    )
    with open(filename, 'w') as OUT:
        json.dump(all_resource_records, OUT, indent=4, sort_keys=True)


@CKAN.command()
@click.argument('resource_id')
@click.argument('file_path')
def import_resource(resource_id, file_path):
    """
    Import records to a resource from a json file
    """
    with open(file_path) as IN:
        records = json.load(IN)
        for record in records:
            if '_id' in record:
                del record['_id']
        ckan.save_records(resource_id, records)


@CKAN.command()
@click.argument('resource_id')
def resource_show(resource_id):
    """
    Show datastore resource metadata
    """
    pprint(ckan.resource_show(resource_id))


@CKAN.command()
@click.argument('resource_id')
def test_upsert_datastore(resource_id):
    """
    Insert of update data in de datastore tabel in een resource met 1
    voorbeeld record als test
    """
    record = {
        "Gemeente": "'s-Gravenhage",
        "CBS gemeentecode": "GM0518",
        "Nummer stembureau": "517",
        "Naam stembureau": "Stadhuis",
        "Gebruikersdoel het gebouw": "kantoor",
        "Website locatie": (
            "https://www.denhaag.nl/nl/bestuur-en-organisatie/contact-met-"
            "de-gemeente/stadhuis-den-haag.htm"
        ),
        "Wijknaam": "Centrum",
        "CBS wijknummer": "WK051828",
        "Buurtnaam": "Kortenbos",
        "CBS buurtnummer": "BU05182811",
        "BAG referentienummer": "0518100000275247",
        "Straatnaam": "Spui",
        "Huisnummer": 70,
        "Huisnummertoevoeging": "",
        "Postcode": "2511 BT",
        "Plaats": "Den Haag",
        "Extra adresaanduiding": "",
        "X": 81611,
        "Y": 454909,
        "Longitude": 4.3166395,
        "Latitude": 52.0775912,
        "Openingstijden": "2017-03-21T07:30:00 tot 2017-03-21T21:00:00",
        "Mindervaliden toegankelijk": 'Y',
        "Invalidenparkeerplaatsen": 'N',
        "Akoestiek": 'Y',
        "Mindervalide toilet aanwezig": 'N',
        "Kieskring ID": "'s-Gravenhage",
        "Contactgegevens": "persoonx@denhaag.nl",
        "Beschikbaarheid": "https://www.stembureausindenhaag.nl/",
        "ID": "NLODSGM0518stembureaus20180321001",
        "UUID": uuid.uuid4().hex
    }
    ckan.save_records(
        resource_id=resource_id,
        records=[record]
    )


@CKAN.command()
@click.argument('resource_id')
def verwijder_datastore(resource_id):
    """
    Verwijder een datastore tabel in een resource
    """
    ckan.delete_datastore(resource_id)

def _get_user(gemeente_code):
    current_user = User.query.filter_by(gemeente_code=gemeente_code).first()
    if not current_user:
        print('Gemeentecode "%s" staat niet in de database' % (gemeente_code))
    return current_user


# Gemeenten
@app.cli.group()
def gemeenten():
    """Gemeenten gerelateerde commands"""
    pass


@gemeenten.command()
def toon_alle_gemeenten():
    """
    Toon alle gemeenten en bijbehorende verkiezingen in de database
    """
    for user in User.query.all():
        print(
            '"%s","%s","%s",["%s"]' % (
                user.gemeente_naam,
                user.gemeente_code,
                user.email,
                ", ".join([x.verkiezing for x in user.elections.all()])
            )
        )


@gemeenten.command()
def verwijder_alle_gemeenten_en_verkiezingen():
    """
    Gebruik dit enkel in development. Deze command verwijdert alle
    gemeenten en verkiezingen uit de MySQL database.
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten en verkiezingen wilt verwijderen uit de MySQL '
            'database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print("Geen gemeenten verwijderd")
            return

    total_removed = User.query.delete()
    print("%d gemeenten verwijderd" % total_removed)
    db.session.commit()


@gemeenten.command()
@click.option('--json_file', default='app/data/gemeenten.json')
def eenmalig_gemeenten_en_verkiezingen_aanmaken(json_file):
    """
    Gebruik deze command slechts eenmaal(!) om alle gemeenten en
    verkiezingen in de database aan te maken op basis van
    'app/data/gemeenten.json'
    """
    # if not app.debug:
    #     result = input(
    #         'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
    #         'alle gemeenten en verkiezingen wilt aanmaken in de MySQL '
    #         'database? (y/N): '
    #     )
    #     # Print empty line for better readability
    #     print()
    #     if not result.lower() == 'y':
    #         print('Geen gemeenten en verkiezingen aangemaakt')
    #         return

    print("Opening %s" % (json_file,))
    with open(json_file, newline='') as IN:
        data = json.load(IN)
        total_created = 0
        for item in data:
            user_email = item['email']
            existing = User.query.filter_by(gemeente_code=item['gemeente_code']).first()
            if existing:
                print("Already have: %s" % (item['gemeente_code'],))
                user = existing
            else:
                user = User(
                    gemeente_naam=item['gemeente_naam'],
                    gemeente_code=item['gemeente_code'],
                    email=user_email
                )
                user.set_password(os.urandom(24))
                db.session.add(user)

                # Only commit if all users are successfully added
                db.session.commit()

                send_invite(user, 349725)

            elections = user.elections.all()
            if (len(elections)) <= 0:
                for verkiezing in item['verkiezingen']:
                    election = Election(verkiezing=verkiezing, gemeente=user)
                    db.session.add(election)

                # Only commit if all users are successfully added
                db.session.commit()

            total_created += 1

        print(
            '%d gemeenten (en bijbehorende verkiezingen) aangemaakt' % (
                total_created
            )
        )


@gemeenten.command()
def eenmalig_gemeenten_uitnodigen():
    """
    Gebruik deze command slechts eenmaal(!) om alle gemeenten, die je
    eerst hebt aangemaakt met 'gemeenten eenmalig_gemeenten_aanmaken',
    een e-mail te sturen met instructies en de vraag om een wachtwoord
    aan te maken
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten wilt uitnodigen voor waarismijnstemlokaal.nl en '
            'vragen om een wachtwoord aan te maken? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten ge-e-maild')
            return

    total_mailed = 0
    for user in User.query.all():
        send_invite(user, 349725)
        total_mailed += 1
    print('%d gemeenten ge-e-maild' % (total_mailed))


@gemeenten.command()
@click.argument('gemeente_code')
def gemeente_invite_link_maken(gemeente_code):
    """
    Maak een reset wachtwoord link aan voor een gemeente. Handig om via een
    ander kanaal een gemeente haar wachtwoord te laten resetten. Geef de CBS
    gemeentecode mee als parameter (bv. GM1680).
    """
    user = User.query.filter_by(gemeente_code=gemeente_code).first()
    if not user:
        print('Gemeentecode "%s" staat niet in de database' % (gemeente_code))
        return
    token = user.get_reset_password_token()
    print(
        'Password reset link voor %s van gemeente %s (%s): %s' % (
            user.email,
            user.gemeente_code,
            user.gemeente_naam,
            url_for('gemeente_reset_wachtwoord', token=token, _external=True)
        )
    )


@gemeenten.command()
def eenmalig_gemeenten_mailcorrectie():
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten wilt uitnodigen voor waarismijnstemlokaal.nl en '
            'vragen om een wachtwoord aan te maken? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten ge-e-maild')
            return

    total_mailed = 0
    for user in User.query.all():
        send_mailcorrectie(user)
        total_mailed += 1
    print('%d gemeenten ge-e-maild' % (total_mailed))
