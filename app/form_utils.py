import csv
from decimal import Decimal

from app.db_utils import db_exec_first
from app.models import BAG
from flask import current_app

kieskringen = []
with open('app/data/kieskringen.csv') as IN:
    reader = csv.reader(IN, delimiter=';')
    # Skip header
    next(reader)
    kieskringen = list(reader)


def create_record(form, stemlokaal_id, gemeente, election):
    ID = 'NLODS%sstembureaus%s%s' % (
        gemeente.gemeente_code,
        current_app.config['CKAN_CURRENT_ELECTIONS'][election]['election_date'],
        current_app.config['CKAN_CURRENT_ELECTIONS'][election]['election_number']
    )

    kieskring_id = ''
    hoofdstembureau = ''
    if (election.startswith('gemeenteraadsverkiezingen') or
            election.startswith('kiescollegeverkiezingen') or
            election.startswith('eilandsraadsverkiezingen')):
        kieskring_id = gemeente.gemeente_naam
        hoofdstembureau = gemeente.gemeente_naam
    elif (election.startswith('referendum') or
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
    bag_record = db_exec_first(BAG, nummeraanduiding=bag_nummer)


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
