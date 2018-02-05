from app import app, db
from app.models import User, ckan
from app.email import send_invite
from pprint import pprint
import click
import csv
import os


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
            "type": "bool"
        },
        {
            "id": "Invalidenparkeerplaatsen",
            "type": "bool"
        },
        {
            "id": "Akoestiek",
            "type": "bool"
        },
        {
            "id": "Mindervalide toilet aanwezig",
            "type": "bool"
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
        }
    ]

    ckan.ckanapi.datastore_create(
        resource_id=resource_id,
        force=True,
        fields=fields
    )


@CKAN.command()
@click.argument('resource_id')
def upsert_datastore(resource_id):
    """
    Insert or update data in de datastore tabel in een resource
    """
    records = [
        {
            "Gemeente": "'s-Gravenhage",
            "CBS gemeentecode": "GM0518",
            "Nummer stembureau": "517",
            "Naam stembureau": "Stadhuis",
            "Gebruikersdoel het gebouw": "kantoor",
            "Website locatie": "https://www.denhaag.nl/nl/bestuur-en-organisatie/contact-met-de-gemeente/stadhuis-den-haag.htm",
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
            "Mindervaliden toegankelijk": True,
            "Invalidenparkeerplaatsen": False,
            "Akoestiek": True,
            "Mindervalide toilet aanwezig": True,
            "Kieskring ID": "'s-Gravenhage",
            "Contactgegevens": "persoonx@denhaag.nl",
            "Beschikbaarheid": "https://www.stembureausindenhaag.nl/"
        }
    ]
    ckan.ckanapi.datastore_upsert(
        resource_id=resource_id,
        force=True,
        records=records,
        method='insert'
    )


@CKAN.command()
@click.argument('resource_id')
def verwijder_datastore(resource_id):
    """
    Verwijder een datastore tabel in een resource
    """
    ckan.ckanapi.datastore_delete(
        resource_id=resource_id,
        force=True
    )


# Gemeenten
@app.cli.group()
def gemeenten():
    """Gemeenten gerelateerde commands"""
    pass


@gemeenten.command()
def toon_alle_gemeenten():
    """
    Toon alle gemeenten in de database
    """
    for user in User.query.all():
        print('"%s","%s","%s"' %
            (
                user.gemeente_naam, user.gemeente_code, user.email
            )
        )


@gemeenten.command()
def verwijder_alle_gemeenten():
    """
    Gebruik dit enkel in development. Deze command verwijdert alle
    gemeenten uit te database.
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten wilt verwijderen uit de database? (y/N): '
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
def eenmalig_gemeenten_aanmaken():
    """
    Gebruik deze command slechts eenmaal(!) om alle gemeenten in de
    database aan te maken op basis van 'app/data/gemeenten.csv'
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten wilt aanmaken in de database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten aangemaakt')
            return

    with open('app/data/gemeenten.csv', newline='') as IN:
        reader = csv.DictReader(IN)
        total_created = 0
        for row in reader:
            user = User(
                gemeente_naam=row['gemeente_naam'],
                gemeente_code=row['gemeente_code'],
                email=row['email']
            )
            user.set_password(os.urandom(24))
            db.session.add(user)
            total_created += 1
        # Only commit if all users are successfully added
        db.session.commit()
        print('%d gemeenten aangemaakt' % (total_created))


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
        if result.lower() == 'y':
            print('Geen gemeenten ge-e-maild')
            return

    total_mailed = 0
    for user in User.query.all():
        send_invite(user)
        total_mailed += 1
    print('%d gemeenten ge-e-maild' % (total_mailed))
