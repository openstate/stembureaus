#!/usr/bin/env python3

# Sicco: based on the following guide:
# https://developers.google.com/sheets/api/quickstart/python

from __future__ import print_function
import csv
import httplib2
import os
import re
import json
from pprint import pprint
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

sys.path.insert(0, '.')
from app.models import ckan
from app.email import send_email
from app import app, mail


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('.')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(
        credential_dir, 'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com
    /spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1AhN-cfJ3JYKFzsstKJ6njpVhbHTfWREEB8UUWozCNjc'
    rangeName = 'Form Responses 1!A2:D'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    with open('last_processed_line.csv') as IN:
        reader = csv.reader(IN)
        last_processed_line = reader.__next__()

    new_values = []
    # Loop over all values. If the last procesed line is found
    # add all values after that to new_values
    for idx, row in enumerate(values):
        if row != last_processed_line:
            continue
        else:
            new_values = values[idx + 1:]
            break

    if not new_values:
        print('No (new) data found.')
    else:
        fields = ['date', 'email', 'gemeente', 'naam']
        records = [dict(zip(fields, v)) for v in new_values]
        # pprint(records)

        # Load all valid gemeente namen
        #gemeente_namen = []
        #with open('gemeente_namen.txt') as IN:
        #    for row in IN.readlines():
        #        gemeente_namen.append(row.strip())

        gemeente_json = []
        with open('app/data/gemeenten.json.example') as IN:
            gemeente_json = json.load(IN)
        #pprint(gemeente_json)
        # Process each new value
        output = []
        for row in new_values:
            new_gemeente_naam = row[2].strip()
            #new_gemeente_naam = re.sub(
            #    '^gemeente ', '', row[2].strip(), flags=re.IGNORECASE)
            #if new_gemeente_naam not in gemeente_namen:
            #    with app.app_context():
            #        send_email(
            #            '[waarismijnstemlokaal.nl] Gemeente niet in '
            #            'gemeente_namen.txt',
            #            sender=app.config['FROM'],
            #            recipients=[app.config['FROM']],
            #            text_body=(
            #                'Kon %s niet vinden in gemeente_namen.txt'
            #            ) % (new_gemeente_naam),
            #            html_body=(
            #                '<p>Kon %s niet vinden in gemeente_namen.txt</p>'
            #            ) % (new_gemeente_naam),
            #        )
            #    continue
            # print('Found gemeente: %s' % (new_gemeente_naam))
            json_gemeente = [
                g for g in gemeente_json
                if g['gemeente_naam'] == new_gemeente_naam]
            if len(json_gemeente) <= 0:
                with app.app_context():
                    send_email(
                        '[waarismijnstemlokaal.nl] Gemeente niet in '
                        'gemeenten.json.example',
                        sender=app.config['FROM'],
                        recipients=[app.config['FROM']],
                        text_body=(
                            'Kon %s niet vinden in gemeenten.json.example'
                        ) % (new_gemeente_naam),
                        html_body=(
                            '<p>Kon %s niet vinden in '
                            'gemeenten.json.example</p>'
                        ) % (new_gemeente_naam),
                    )
                continue
            json_gemeente[0]['email'] = row[1]
            #if json_gemeente[0]['verkiezingen'] == []:
            #    json_gemeente[0]['verkiezingen'] = [
            #        e for e in ckan.elections.keys()]
            output.append(json_gemeente[0])
        print(json.dumps(output))


if __name__ == '__main__':
    main()
