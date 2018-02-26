from app import app, db
from app.models import User, ckan, Election
from app.email import send_invite, send_mailcorrectie
from pprint import pprint
import click
import json
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
            "id": "primary_key",
            "type": "int"
        },
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
        }
    ]

    ckan.create_datastore(resource_id, fields)


@CKAN.command()
@click.argument('resource_id')
def test_upsert_datastore(resource_id):
    """
    Insert of update data in de datastore tabel in een resource met 1
    voorbeeld record als test
    """
    record = {
        "primary_key": 1,
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
        "ID": "NLODSGM0518stembureaus20180321001"
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
def eenmalig_gemeenten_en_verkiezingen_aanmaken():
    """
    Gebruik deze command slechts eenmaal(!) om alle gemeenten en
    verkiezingen in de database aan te maken op basis van
    'app/data/gemeenten.json'
    """
    if not app.debug:
        result = input(
            'Je voert deze command in PRODUCTIE uit. Weet je zeker dat je '
            'alle gemeenten en verkiezingen wilt aanmaken in de MySQL '
            'database? (y/N): '
        )
        # Print empty line for better readability
        print()
        if not result.lower() == 'y':
            print('Geen gemeenten en verkiezingen aangemaakt')
            return

    with open('app/data/gemeenten.json', newline='') as IN:
        data = json.load(IN)
        total_created = 0
        for item in data:
            user = User(
                gemeente_naam=item['gemeente_naam'],
                gemeente_code=item['gemeente_code'],
                email=item['email']
            )
            user.set_password(os.urandom(24))
            db.session.add(user)

            for verkiezing in item['verkiezingen']:
                election = Election(verkiezing=verkiezing, gemeente=user)

            total_created += 1
        # Only commit if all users are successfully added
        db.session.commit()
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
