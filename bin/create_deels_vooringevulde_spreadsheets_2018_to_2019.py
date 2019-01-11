#!/usr/bin/env python3

import csv
import os
import re
import sys

from openpyxl import load_workbook
from openpyxl.styles import Font
from pyexcel_ods3 import get_data, save_data

sys.path.insert(0, '.')


def as_text(value):
    if value is None:
        return ""
    return str(value)

field_names = [
    'Nummer stembureau',
    'Naam stembureau',
    'Website locatie',
    'BAG referentienummer',
    'Extra adresaanduiding',
    'X',
    'Y',
    'Longitude',
    'Latitude',
    'Openingstijden',
    'Mindervaliden toegankelijk',
    'Akoestiek',
    'Mindervalide toilet aanwezig',
    'Contactgegevens',
    'Beschikbaarheid'
]

gemeente_herindelingen = {
    'Haren': 'Groningen',
    'Ten Boer': 'Groningen',
    'Binnenmaas': 'Hoeksche Waard',
    'Cromstrijen': 'Hoeksche Waard',
    'Korendijk': 'Hoeksche Waard',
    'Oud-Beijerland': 'Hoeksche Waard',
    'Strijen': 'Hoeksche Waard',
    'Leerdam': 'Vijfheerenlanden',
    'Vianen': 'Vijfheerenlanden',
    'Zederik': 'Vijfheerenlanden',
    'Aalburg': 'Altena',
    'Werkendam': 'Altena',
    'Woudrichem': 'Altena',
    'Nuth': 'Beekdaelen',
    'Onderbanken': 'Beekdaelen',
    'Schinnen': 'Beekdaelen',
    'Haarlemmerliede en Spaarnwoude': 'Haarlemmermeer',
    'Bedum': 'Het Hogeland',
    'De Marne': 'Het Hogeland',
    'Eemsmond': 'Het Hogeland',
    'Winsum': 'Het Hogeland',
    'Grootegast': 'Westerkwartier',
    'Leek': 'Westerkwartier',
    'Marum': 'Westerkwartier',
    'Zuidhorn': 'Westerkwartier',
    'Giessenlanden': 'Molenlanden',
    'Molenwaard': 'Molenlanden',
    'Dongeradeel': 'Noardeast-Fryslân',
    'Ferwerderadiel': 'Noardeast-Fryslân',
    'Kollumerland en Nieuwkruisland': 'Noardeast-Fryslân',
    'Noordwijkerhout': 'Noordwijk',
    'Geldermalsen': 'West Betuwe',
    'Lingewaal': 'West Betuwe',
    'Neerijnen': 'West Betuwe'
}


def main():
    with open('files/67f5d14c-b625-485f-9f47-8faccc5e27bc.csv') as IN:
        reader = csv.reader(IN)
        header = reader.__next__()
        records_per_gemeente = {}
        # Load the records
        for row in reader:
            data = dict(zip(header, row))
            record = {}
            for key, value in data.items():
                if key in field_names:
                    if key == 'Openingstijden':
                        record[key] = re.sub('2018-03-21', '2019-03-20', value)
                    else:
                        record[key] = value

            gemeente = data['Gemeente']
            if gemeente in gemeente_herindelingen:
                gemeente = gemeente_herindelingen[gemeente]

            try:
                records_per_gemeente[gemeente].append(record)
            except KeyError:
                records_per_gemeente[gemeente] = [record]

        if not os.path.exists('files/deels_vooringevuld'):
            os.mkdir('files/deels_vooringevuld')

        for gemeente, records in records_per_gemeente.items():
            # Save the records to the .xslx file
            print(gemeente)
            path = "files/deels_vooringevuld/waarismijnstemlokaal.nl_invulformulier_%s_deels_vooringevuld.xlsx" % (gemeente,)
            os.system("cp files/waarismijnstemlokaal.nl_invulformulier.xlsx \"%s\"" % (
                path,))
            workbook = load_workbook(path)
            worksheet = workbook['Attributen']
            font = Font(name="Arial", size=10)
            column = 6

            # Sort the records based on 'Nummer stembureau' while placing
            # records without a 'Nummer stembureau' at the end
            sorted_records = sorted(records, key=lambda k: int(k['Nummer stembureau']) if k['Nummer stembureau'] else 100000)

            for record in sorted_records:
                row = 2
                for field_name in field_names:
                    worksheet.cell(row=row, column=column, value=record[field_name]).font = font
                    row += 1
                column += 1

            # Set width of each column
            for column_cells in tuple(worksheet.columns)[5:]:
                length = max(len(as_text(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column].width = int(length * 0.75)

            workbook.save(path)
            workbook.close()

            # Save the records to the .ods file
            #path = "files/deels_vooringevuld/waarismijnstemlokaal.nl_invulformulier_%s_deels_vooringevuld.ods" % (gemeente,)
            #os.system("cp files/waarismijnstemlokaal.nl_invulformulier.ods \"%s\"" % (
            #    path,))
            #data = get_data(path)
            #for record in records:
            ## TODO this needs to be rewritten
            ##    data['Attributen'][2].append(record['Naam stembureau'])
            ##    if 'BAG referentienummer' in record:
            ##        data['Attributen'][5].append(record['BAG referentienummer'])
            ##    if 'Longitude' in record:
            ##        data['Attributen'][7].append(record['Longitude'])
            ##    if 'Latitude' in record:
            ##        data['Attributen'][8].append(record['Latitude'])
            ##    data['Attributen'][10].append(record['Openingstijden'])
            #    save_data(path, data)
    return 0

if __name__ == '__main__':
    sys.exit(main())
