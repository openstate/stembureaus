from app import app, db
from app.models import Gemeente, User, Gemeente_user, Election, BAG, ckan, add_user
from app.email import send_invite, send_update
from app.parser import UploadFileParser
from app.validator import Validator
from app.routes import create_record, kieskringen
from app.utils import find_buurt_and_wijk, get_gemeente, publish_gemeente_records, remove_id
from app.stembureaumanager import StembureauManager
from app.tsa import TSAManager
from app.procura import ProcuraManager

from datetime import datetime, timedelta
from dateutil import parser
from flask import url_for
from pprint import pprint
import click
import copy
import json
import os
import sys
import uuid
import pytz


@app.cli.group()
def API():
    "API related commands"
    pass


@API.command()
@click.option('--from-date', default=datetime.now(pytz.UTC) - timedelta(hours=1), help="Only load gemeenten after this date/timestamp; default: 2 hours before now")
@click.option('--gm-code', help="Load a specific gemeente (format: <GMxxxx>) irrespective of its last gewijzigd timestamp")
def stembureaumanager(from_date, gm_code):
    """
    Update data from municipalities that use Stembureaumanager
    """
    print("Updating Stembureaumanager from %s ..." % (from_date,))
    if isinstance(from_date, str):
        if 'T' not in from_date:
            from_date = '%sT00:00:00Z' % (from_date,)
        from_date = parser.parse(from_date)
    StembureauManager(from_date=from_date, gm_code=gm_code).run()


@API.command()
@click.option('--from-date', default=datetime.now(pytz.timezone('Europe/Amsterdam')) - timedelta(hours=2), help="Only load gemeenten after this date/timestamp; default: 2 hours before now")
@click.option('--gm-code', help="Load a specific gemeente (format: <GMxxxx>) irrespective of its last gewijzigd timestamp")
def tsa(from_date, gm_code):
    """
    Update data from municipalities that use TSA
    """
    print("Updating TSA from %s ..." % (from_date,))
    if isinstance(from_date, str):
        if 'T' not in from_date:
            from_date = '%sT00:00:00' % (from_date,)
        from_date = parser.parse(from_date)
    TSAManager(from_date=from_date, gm_code=gm_code).run()


@API.command()
@click.option('--from-date', default=datetime.now(pytz.timezone('Europe/Amsterdam')) - timedelta(hours=2), help="Only load gemeenten after this date/timestamp; default: 2 hours before now")
@click.option('--gm-code', help="Load a specific gemeente (format: <GMxxxx>) irrespective of its last gewijzigd timestamp")
def procura(from_date, gm_code):
    """
    Update data from municipalities that use Procura
    """
    print("Updating Procura from %s ..." % (from_date,))
    if isinstance(from_date, str):
        if 'T' not in from_date:
            from_date = '%sT00:00:00' % (from_date,)
        from_date = parser.parse(from_date)
    ProcuraManager(from_date=from_date, gm_code=gm_code).run()


# CKAN (use uppercase to avoid conflict with 'ckan' import from
# app.models)
@app.cli.group()
def CKAN():
    """ckan commands"""
    pass


@CKAN.command()
def show_verkiezingen():
    """
    Show all current elections and the corresponding public and draft resources
    """
    pprint(ckan.elections)


def _get_bag(r):
    print(r['_id'])
    if not r['Straatnaam']:
        print('geen straatnaam')

        bag = BAG.query.filter_by(nummeraanduiding=r['BAG Nummeraanduiding ID'])
        if bag.count() == 1:
            return bag.first()

        bag = BAG.query.filter_by(object_id=r['BAG Nummeraanduiding ID'])
        if bag.count() == 1:
            if bag.first().nummeraanduiding:
                return bag.first()
            else:
                return False

        bag = BAG.query.filter_by(pandid=r['BAG Nummeraanduiding ID'])
        if bag.count() == 1:
            if bag.first().nummeraanduiding:
                return bag.first()
            else:
                return False

        return False


@CKAN.command()
@click.option('--resource_type', default='draft')
def fix_bag_addresses(resource_type):
    """
    Checks all records of all election resources (default draft) for
    missing address information. If this is the case, try to retrieve
    it based on the available BAG number, otherwise check if the BAG
    number is another type of BAG number (other than nummeraanduiding)
    and see if it corresponds with 1 BAG nummeraanduiding ID in order
    to retrieve the address. Finally, the whole resource is exported.
    """
    for name, election in ckan.elections.items():
        total = 0
        bag_found = 0
        resource_id = election['%s_resource' % (resource_type)]
        sys.stderr.write('%s: %s\n' % (name, resource_id))
        records = ckan.get_records(resource_id)
        for r in records['records']:
            bag = _get_bag(r)

            if bag:
                bag_found += 1
                r['BAG Nummeraanduiding ID'] = bag.nummeraanduiding

                bag_conversions = {
                    'verblijfsobjectgebruiksdoel': 'Gebruiksdoel van het gebouw',
                    'openbareruimte': 'Straatnaam',
                    'huisnummer': 'Huisnummer',
                    'huisletter': 'Huisletter',
                    'huisnummertoevoeging': 'Huisnummertoevoeging',
                    'postcode': 'Postcode',
                    'woonplaats': 'Plaats'
                }

                for bag_field, record_field in bag_conversions.items():
                    bag_field_value = getattr(bag, bag_field, None)
                    if bag_field_value is not None:
                        r[record_field] = bag_field_value.encode(
                            'latin1'
                        ).decode()
                    else:
                        r[record_field] = None

            total += 1
        sys.stderr.write(
            "%s records, %s with BAG found\n" % (
                total, bag_found
            )
        )

        with open('exports/%s_bag_add_fix.json' % (resource_id), 'w') as OUT:
            json.dump(records['records'], OUT, indent=4, sort_keys=True)


@CKAN.command()
@click.argument('resource_id')
def add_new_datastore(resource_id):
    """
    Add a new datastore table to a resource. This needs to be run once after
    you've created a new CKAN resource, see the 'Create new CKAN datasets and
    resources for new elections' section in README.md.
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
            "id": "Type stembureau",
            "type": "text"
        },
        {
            "id": "Gebruiksdoel van het gebouw",
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
            "id": "BAG Nummeraanduiding ID",
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
            "id": "Huisletter",
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
            "type": "float"
        },
        {
            "id": "Y",
            "type": "float"
        },
        {
            "id": "Latitude",
            "type": "float"
        },
        {
            "id": "Longitude",
            "type": "float"
        },
        {
            "id": "Openingstijd",
            "type": "timestamp"
        },
        {
            "id": "Sluitingstijd",
            "type": "timestamp"
        },
        {
            "id": "Toegankelijk voor mensen met een lichamelijke beperking",
            "type": "text"
        },
        {
            "id": "Toegankelijke ov-halte",
            "type": "text"
        },
        {
            "id": "Gehandicaptentoilet",
            "type": "text"
        },
        {
            "id": "Host",
            "type": "text"
        },
        {
            "id": "Geleidelijnen",
            "type": "text"
        },
        {
            "id": "Stemmal met audio-ondersteuning",
            "type": "text"
        },
        {
            "id": "Kandidatenlijst in braille",
            "type": "text"
        },
        {
            "id": "Kandidatenlijst met grote letters",
            "type": "text"
        },
        {
            "id": "Gebarentolk (NGT)",
            "type": "text"
        },
        {
            "id": "Gebarentalig stembureaulid (NGT)",
            "type": "text"
        },
        {
            "id": "Akoestiek geschikt voor slechthorenden",
            "type": "text"
        },
        {
            "id": "Prikkelarm",
            "type": "text"
        },
        {
            "id": "Extra toegankelijkheidsinformatie",
            "type": "text"
        },
        {
            "id": "Overige informatie",
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
            "id": "Tellocatie",
            "type": "text"
        },
        {
            "id": "Contactgegevens gemeente",
            "type": "text"
        },
        {
            "id": "Verkiezingswebsite gemeente",
            "type": "text"
        }
    ]

    # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field at
    # this place in the list
    if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
        fields += [
            {
                "id": "Verkiezingen",
                "type": "text"
            }
        ]

    fields += [
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
    current_gemeente = get_gemeente(gemeente_code)

    elections = current_gemeente.elections.all()
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
        if record['CBS gemeentecode'] == current_gemeente.gemeente_code
    ]
    remove_id(gemeente_draft_records)

    parser = UploadFileParser()
    app.logger.info(
        'Manually (CLI) uploading file for '
        '%s' % (current_gemeente.gemeente_naam)
    )
    try:
        records = parser.parse(file_path)
    except ValueError as e:
        app.logger.warning('Manual upload failed: %s' % e)
        return

    validator = Validator()
    results = validator.validate(records)

    # If the spreadsheet did not validate then return the errors
    if not results['no_errors']:
        print(
            'Upload failed. Fix the errors shown below and try again.\n\n'
        )
        for column_number, col_result in sorted(
                results['results'].items()):
            if col_result['errors']:
                print(
                    'Error(s) in '
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
    # If there is not a single value in the results then state that we
    # could not find any stembureaus
    elif not results['found_any_record_with_values']:
        print(
            'Upload failed. No stembureaus have been found in this '
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
                        'CBS gemeentecode': current_gemeente.gemeente_code
                    }
                )

        # Create and save records
        for election in [x.verkiezing for x in elections]:
            records = []
            for _, result in results['results'].items():
                if result['form']:
                    records.append(
                        create_record(
                            result['form'],
                            result['uuid'],
                            current_gemeente,
                            election
                        )
                    )
            ckan.save_records(
                ckan.elections[election]['draft_resource'],
                records=records
            )
        print('Upload successful!')
    print('\n\n')


@CKAN.command()
@click.argument('gemeente_code')
def publish_gemeente(gemeente_code):
    """
    Publishes the saved (draft) stembureaus of a gemeente
    """
    publish_gemeente_records(gemeente_code)


@CKAN.command()
@click.argument('gemeente_code')
@click.argument('source_resource')
@click.argument('dest_resource')
@click.option('--dest_id', '-di')
@click.option('--dest_hoofdstembureau', '-dh')
@click.option('--dest_kieskring_id', '-dk')
def copy_gemeente_resource(gemeente_code, source_resource, dest_resource,
                           dest_id=None, dest_hoofdstembureau=None,
                           dest_kieskring_id=None):
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
    remove_id(gemeente_resource_records)

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
            dest_kieskring_id = gemeente_dest_resource_records[0][
                'Kieskring ID'
            ]

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
        ckan.save_records(
            resource_id,
            sorted(
                records, key=lambda x: (x['Gemeente'], x['Nummer stembureau'])
            )
        )


@CKAN.command()
@click.argument('gemeenten_info_file_path')
@click.argument('excluded_gemeenten_file_path')
@click.argument('rug_file_path')
def import_rug(rug_file_path,
               excluded_gemeenten_file_path, gemeenten_info_file_path):
    """
    Import records coming from Geodienst from the Rijksuniversiteit Groningen.
    These records don't contain all fields and these need to be filled. Based
    on the gemeente in the record it will be saved to correct election(s)
    resources (draft + publish).
    """
    # Retrieve information about gemeenten
    with open(gemeenten_info_file_path) as IN:
        gemeenten_info = json.load(IN)

    # Retrieve file containing a list of names of gemeenten which
    # uploaded stembureaus themselves and thus don't need to be
    # retrieved from the RUG data
    with open(excluded_gemeenten_file_path) as IN:
        excluded_gemeenten = [line.strip() for line in IN]

    with open(rug_file_path) as IN:
        # Load RUG file
        rug_records = json.load(IN)

        resource_records = {}
        # Prepopulate a dict with all CKAN resources
        for election, values in app.config['CKAN_CURRENT_ELECTIONS'].items():
            resource_records[values['draft_resource']] = []
            resource_records[values['publish_resource']] = []

        # Process each record
        for rug_record in rug_records:
            # Skip record if its gemeente is in the excluded list
            if rug_record['Gemeente'] in excluded_gemeenten:
                continue

            # Retrieve the gemeente info for the gemeente of the
            # current record
            record_gemeente_info = {}
            for gemeente_info in gemeenten_info:
                if gemeente_info['gemeente_naam'] == rug_record['Gemeente']:
                    record_gemeente_info = gemeente_info

            rug_record['UUID'] = uuid.uuid4().hex
            gemeente_code = record_gemeente_info['gemeente_code']
            rug_record['CBS gemeentecode'] = gemeente_code

            # Try to retrieve the record in the BAG
            bag_result = BAG.query.filter_by(
                openbareruimte=rug_record['Straatnaam'],
                huisnummer=rug_record['Huisnummer'],
                huisnummertoevoeging=rug_record['Huisnummertoevoeging'],
                woonplaats=rug_record['Plaats']
            )

            # If the query above didn't work, try it again without
            # huisnummertoevoeging
            if bag_result.count() == 0:
                bag_result = BAG.query.filter_by(
                    openbareruimte=rug_record['Straatnaam'],
                    huisnummer=rug_record['Huisnummer'],
                    woonplaats=rug_record['Plaats']
                )

            # If there are multiple BAG matches, simply take the first
            bag_object = bag_result.first()

            # Retrieve gebruiksdoel, postcode and nummeraanduiding
            # from BAG
            if bag_object:
                bag_conversions = {
                    'verblijfsobjectgebruiksdoel': 'Gebruiksdoel van het gebouw',
                    'postcode': 'Postcode',
                    'nummeraanduiding': 'BAG Nummeraanduiding ID'
                }

                for bag_field, record_field in bag_conversions.items():
                    bag_field_value = getattr(bag_object, bag_field, None)
                    if bag_field_value is not None:
                        rug_record[record_field] = bag_field_value.encode(
                            'latin1'
                        ).decode()
                    else:
                        rug_record[record_field] = None

            ## We stopped adding the wijk and buurt data as the data
            ## supplied by CBS is not up to date enough as it is only
            ## released once a year and many months after changes
            ## have been made by the municipalities.
            # Retrieve wijk and buurt info
            #wk_code, wk_naam, bu_code, bu_naam = find_buurt_and_wijk(
            #    '000',
            #    rug_record['CBS gemeentecode'],
            #    rug_record['Latitude']
            #    rug_record['Longitude'],
            #)
            #if wk_naam:
            #    rug_record['Wijknaam'] = wk_naam
            #if wk_code:
            #    rug_record['CBS wijknummer'] = wk_code
            #if bu_naam:
            #    rug_record['Buurtnaam'] = bu_naam
            #if bu_code:
            #    rug_record['CBS buurtnummer'] = bu_code

            # Loop over each election in which the current gemeente
            # participates and create election specific fields
            for verkiezing in record_gemeente_info['verkiezingen']:
                record = copy.deepcopy(rug_record)

                verkiezing_info = app.config['CKAN_CURRENT_ELECTIONS'][
                    verkiezing
                ]
                record['ID'] = 'NLODS%sstembureaus%s%s' % (
                    gemeente_code,
                    verkiezing_info['election_date'],
                    verkiezing_info['election_number']
                )

                kieskring_id = ''
                hoofdstembureau = ''
                if verkiezing.startswith('gemeenteraadsverkiezingen'):
                    kieskring_id = record['Gemeente']
                    hoofdstembureau = record['Gemeente']
                if verkiezing.startswith('referendum'):
                    for row in kieskringen:
                        if row[2] == record['Gemeente']:
                            kieskring_id = row[0]
                            hoofdstembureau = row[1]

                record['Kieskring ID'] = kieskring_id
                record['Hoofdstembureau'] = hoofdstembureau

                # Append the record for the draft and publish resource
                # of this election
                resources = [
                    verkiezing_info['draft_resource'],
                    verkiezing_info['publish_resource']
                ]
                for resource in resources:
                    resource_records[resource].append(record)
        for resource, res_records in resource_records.items():
            print('%s: %s' % (resource, len(res_records)))
            ckan.save_records(resource, res_records)


@CKAN.command()
@click.argument('resource_id')
def resource_show(resource_id):
    """
    Show datastore resource metadata
    """
    pprint(ckan.resource_show(resource_id))


@CKAN.command()
@click.argument('resource_id')
def test_datastore_upsert(resource_id):
    """
    Insert or update data in the datastore table in a resource with
    an example record; used for testing
    """
    record = {
        "Gemeente": "'s-Gravenhage",
        "CBS gemeentecode": "GM0518",
        "Nummer stembureau": "517",
        "Naam stembureau": "Stadhuis",
        "Type stembureau": "regulier",
        "Gebruiksdoel van het gebouw": "kantoor",
        "Website locatie": "https://www.denhaag.nl/nl/contact-met-de-gemeente/stadhuis-den-haag/",
        "Wijknaam": "Centrum",
        "CBS wijknummer": "WK051828",
        "Buurtnaam": "Kortenbos",
        "CBS buurtnummer": "BU05182811",
        "BAG Nummeraanduiding ID": "0518100000275247",
        "Straatnaam": "Spui",
        "Huisnummer": 70,
        "Huisletter": "",
        "Huisnummertoevoeging": "",
        "Postcode": "2511 BT",
        "Plaats": "Den Haag",
        "Extra adresaanduiding": "Ingang aan achterkant gebouw",
        "X": 81611,
        "Y": 454909,
        "Latitude": 52.0775912,
        "Longitude": 4.3166395,
        "Openingstijd": "2024-06-06T07:30:00",
        "Sluitingstijd": "2024-06-06T21:00:00",
        "Toegankelijk voor mensen met een lichamelijke beperking": "ja",
        "Toegankelijke ov-halte": "ja",
        "Gehandicaptentoilet": "nee",
        "Host": "ja",
        "Geleidelijnen": "buiten en binnen",
        "Stemmal met audio-ondersteuning": "ja",
        "Kandidatenlijst in braille": "ja",
        "Kandidatenlijst met grote letters": "ja",
        "Gebarentolk (NGT)": "op locatie",
        "Gebarentalig stembureaulid (NGT)": "ja",
        "Akoestiek geschikt voor slechthorenden": "ja",
        "Prikkelarm": "ja",
        "Extra toegankelijkheidsinformatie": "Dit stembureau is ingericht voor kwetsbare mensen, stembureau is volledig toegankelijk voor mensen met een lichamelijke beperking er is echter geen gehandicaptenparkeerplaats, gebarentolk op locatie (NGT) is aanwezig van 10:00-12:00 en 16:00-18:00, oefenstembureau",
        "Overige informatie": "",
        "Kieskring ID": "'s-Gravenhage",
        "Hoofdstembureau": "Nederland",
        "Tellocatie": "ja",
        "Contactgegevens gemeente": "Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag",
        "Verkiezingswebsite gemeente": "https://www.stembureausindenhaag.nl/",
        "ID": "NLODSGM0518stembureaus20240606015",
        "UUID": uuid.uuid4().hex
    }

    # If there are 'waterschapsverkiezingen', add the 'Verkiezingen' field to
    # the example record
    if [x for x in app.config['CKAN_CURRENT_ELECTIONS'] if 'waterschapsverkiezingen' in x]:
        record["Verkiezingen"] = "waterschapsverkiezingen voor Delfland"

    ckan.save_records(
        resource_id=resource_id,
        records=[record]
    )


@CKAN.command()
@click.argument('resource_id')
@click.argument('record_id')
def remove_record_via_id(resource_id, record_id):
    """
    Remove a record from a datastore/resource based on its '_id'
    """
    ckan.delete_records(
        resource_id,
        {
            '_id': record_id
        }
    )


@CKAN.command()
@click.argument('resource_id')
def remove_datastore(resource_id):
    """
    Remove the datastore table from a resource
    """
    ckan.delete_datastore(resource_id)


# MySQL commands
@app.cli.group()
def mysql():
    """MySQL related commands"""
    pass


@mysql.command()
def show_all_users():
    """
    Show all users and their corresponding gemeenten
    """
    for user in User.query.all():
        print(
            '"%s","%s"' % (
                user.email,
                user.gemeenten
            )
        )


@mysql.command()
@click.option('--crm', is_flag=True, show_default=True, default=False, help="Output only non-admin users and don't show the verkiezingen; this format can be copied to our CRM")
def show_all_gemeenten(crm):
    """
    Show all gemeenten and their corresponding users and verkiezingen
    """
    for gemeente in Gemeente.query.all():
        if crm:
            print(
                '"%s","%s","%s"' % (
                    gemeente.gemeente_code,
                    gemeente.gemeente_naam,
                    ','.join([x.email for x in gemeente.users])
                )
            )
        else:
            print(
                '"%s","%s","%s",["%s"]' % (
                    gemeente.gemeente_code,
                    gemeente.gemeente_naam,
                    gemeente.users,
                    ", ".join([x.verkiezing for x in gemeente.elections.all()])
                )
            )


@mysql.command()
def remove_all_gemeenten_verkiezingen_users():
    """
    Only use this in development. This command removes all gemeenten,
    verkiezingen and users from the MySQL database.
    """
    if not app.debug:
        result = input(
            'You are running this command in PRODUCTION. Are you sure that '
            'you want to remove all gemeenten, verkiezingen and users '
            'from the MySQL database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print("No gemeenten, verkiezingen and users removed")
            return

    Election.query.delete()
    Gemeente_user.query.delete()
    total_users_removed = User.query.delete()
    total_gemeenten_removed = Gemeente.query.delete()

    db.session.commit()

    print("All verkiezingen removed")
    print("%d users removed" % total_users_removed)
    print("%d gemeenten removed" % total_gemeenten_removed)


@mysql.command()
@click.argument('gemeente')
@click.argument('email')
def add_new_user(gemeente, email):
    gemeente = Gemeente.query.filter_by(
        gemeente_naam=gemeente
    ).first()
    add_user(gemeente.id, email, send_logging_mail=False)


@mysql.command()
@click.argument('email')
def remove_user(email):
    """
    Remove a user by specifying the user's email address
    """
    if not app.debug:
        result = input(
            'You are running this command in PRODUCTION. Are you sure that '
            'you want to remove this user from the MySQL database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print("No user removed")
            return

    user = User.query.filter_by(email=email).first()

    if not user:
        print('No user with email address %s' % (email))
        return

    Gemeente_user.query.filter_by(user_id=user.id).delete()
    User.query.filter_by(id=user.id).delete()
    print("User %s removed" % email)

    db.session.commit()


@mysql.command()
@click.argument('email')
def add_admin_user(email):
    """
    Adds an admin user. This command will prompt for an email address.
    If it does not exist yet a user will be created and given admin
    rights, which allows the user to see and edit all gemeenten.
    """

    # Check if a user already exists with this email address
    user = User.query.filter_by(email=email).first()

    if user:
        user.admin = True
    if not user:
        user = User(
            email=email,
            admin=True
        )
        user.set_password(os.urandom(24))
        db.session.add(user)
        db.session.commit()

        # Send the new user an invitation email
        send_invite(user)

    # Add access to all gemeenten for this user, by adding
    # records to the Gemeente_user association table
    gemeente_count = 0
    for gemeente in Gemeente.query.all():
        gemeente_user = Gemeente_user.query.filter_by(
            gemeente_id=gemeente.id,
            user_id=user.id
        ).first()

        # Make sure the record doesn't exist already
        if not gemeente_user:
            gemeente_user = Gemeente_user(
                gemeente_id=gemeente.id,
                user_id=user.id
            )
            db.session.add(gemeente_user)
            gemeente_count += 1

    db.session.commit()

    print(
        "Added admin user with access to all %s gemeenten" % (gemeente_count)
    )


@mysql.command()
@click.option('--json_file', default='app/data/gemeenten.json')
def add_gemeenten_verkiezingen_users(json_file):
    """
    Add all gemeenten, verkiezingen and users specified in
    'app/data/gemeenten.json' to the MySQL database and send new users
    an invitation email
    """
    print("Opening %s" % (json_file,))
    with open(json_file, newline='') as IN:
        data = json.load(IN)
        total_gemeenten_created = 0
        total_users_created = 0
        for item in data:
            # Add gemeenten
            gemeente = Gemeente.query.filter_by(
                gemeente_code=item['gemeente_code']
            ).first()

            # Make sure the gemeente doesn't exist already
            if not gemeente:
                gemeente = Gemeente(
                    gemeente_naam=item['gemeente_naam'],
                    gemeente_code=item['gemeente_code']
                )
                db.session.add(gemeente)
                db.session.commit()

                total_gemeenten_created += 1
            else:
                print(
                    "Gemeente already exists: %s (%s)" % (
                        item['gemeente_naam'], item['gemeente_code'],
                    )
                )

            # Remove existing elections and add new elections (this
            # allows us to easily change the elections that are
            # currently held)
            elections = gemeente.elections.all()
            for election in elections:
                Election.query.filter_by(id=election.id).delete()
            for verkiezing in item['verkiezingen']:
                election = Election(
                    verkiezing=verkiezing, gemeente=gemeente
                )
                db.session.add(election)
            db.session.commit()

            # Add users
            for email in item['email']:
                total_users_created += add_user(
                    gemeente.id, email, send_logging_mail=False
                )

            # Add admin users (they have access to all gemeenten)
            for admin in User.query.filter_by(admin=1):
                # Add records to the Gemeente_user association table
                gemeente_user = Gemeente_user.query.filter_by(
                    gemeente_id=gemeente.id,
                    user_id=admin.id
                ).first()

                # Make sure the record doesn't exist already
                if not gemeente_user:
                    gemeente_user = Gemeente_user(
                        gemeente_id=gemeente.id,
                        user_id=admin.id
                    )
                    db.session.add(gemeente_user)
            db.session.commit()

        print(
            '%d gemeenten added' % (
                total_gemeenten_created
            )
        )
        print('%d users added' % (total_users_created))


@mysql.command()
@click.argument('email')
def create_user_invite_link(email):
    """
    Create a 'reset password' URL for a user. Useful to avoid emails
    in the process of resetting a users password. Provide the users
    email address as parameter.
    """
    user = User.query.filter_by(email=email).first()
    if not user:
        print('No user with email address %s' % (email))
        return
    token = user.get_reset_password_token()
    print(
        'Password reset URL for %s: %s' % (
            email,
            url_for('user_reset_wachtwoord', token=token, _external=True)
        )
    )


@mysql.command()
def eenmalig_gemeenten_update_mail():
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten een update e-mail voor waarismijnstemlokaal.nl '
            'wilt sturen? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten ge-e-maild')
            return

    total_mailed = 0
    for user in User.query.all():
        send_update(user)
        total_mailed += 1
    print('%d gemeenten ge-e-maild' % (total_mailed))
