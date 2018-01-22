from app import app, db
from app.models import User
from app.email import send_invite
import csv
import os


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
        print('"%s","%s"' % (user.gemeente, user.email))

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
    database aan te maken op basis van 'data/gemeenten.csv'
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
            user = User(gemeente=row['gemeente'], email=row['email'])
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
