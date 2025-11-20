#!/usr/bin/env python3

# Sicco: based on the following guide:
# https://developers.google.com/sheets/api/quickstart/python

from flask import current_app
from __future__ import print_function
import copy
import csv
import httplib2
import os
import json
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
from app.email import send_email


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

    # ID of the Google spreadsheet where the answers of the form are
    # stored
    spreadsheetId = '1AhN-cfJ3JYKFzsstKJ6njpVhbHTfWREEB8UUWozCNjc'
    # Relevant columns in the spreadsheet
    rangeName = 'Form Responses 1!A2:D'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    # This file contains the most recent processed line/row. During a
    # new run of this script only lines newer than the one in the file
    # are processed.
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
        # Some debug lines
        #fields = ['date', 'email', 'gemeente', 'naam']
        #records = [dict(zip(fields, v)) for v in new_values]
        #pprint(records)

        # Load gemeenten data of this election
        gemeente_json = []
        with open('app/data/gemeenten.json.example') as IN:
            gemeente_json = json.load(IN)
        # Process each new value
        output = []
        for row in new_values:
            new_gemeente_naam = row[2].strip()

            # Google Forms/Sheets treat values starting with a "'"
            # different and remove it when we read the value, so we
            # account for that here
            if new_gemeente_naam == "s-Hertogenbosch":
                new_gemeente_naam = "'s-Hertogenbosch"
            if new_gemeente_naam == "s-Gravenhage":
                new_gemeente_naam = "'s-Gravenhage"

            # Retrieve info for the gemeente
            json_gemeente = [
                copy.deepcopy(g) for g in gemeente_json
                if g['gemeente_naam'] == new_gemeente_naam]

            # Send an email if the gemeente could not be found
            if len(json_gemeente) <= 0:
                send_email(
                    '[waarismijnstemlokaal.nl] Gemeente niet in '
                    'gemeenten.json.example',
                    sender=current_app.config['FROM'],
                    recipients=current_app.config['ADMINS'],
                    text_body=(
                        'Kon %s niet vinden in gemeenten.json.example'
                    ) % (new_gemeente_naam),
                    html_body=(
                        '<p>Kon %s niet vinden in '
                        'gemeenten.json.example</p>'
                    ) % (new_gemeente_naam),
                )
                continue
            # Add the email adress to the gemeente info
            json_gemeente[0]['email'].append(row[1])
            output.append(json_gemeente[0])
        # Print the JSON containing gemeente info with the newly added
        # email addresses
        print(json.dumps(output))

        # Save the new last processed line
        with open('last_processed_line.csv', 'w') as OUT:
            writer = csv.writer(OUT)
            writer.writerow(new_values[-1])


if __name__ == '__main__':
    main()
