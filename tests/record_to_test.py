def record_to_test(election_date, closing_time = '21:00:00'):
    return {
        'gemeente': "'s-Gravenhage",
        'cbs gemeentecode': 'GM0518',
        'nummer stembureau': 517,
        'naam stembureau': 'Stadhuis',
        'type stembureau': 'regulier',
        'gebruiksdoel van het gebouw': 'Kantoor',
        'website locatie': (
            'https://www.denhaag.nl/nl/contact-met-de-gemeente/stadhuis-den-haag/'
        ),
        'wijknaam': 'Centrum',
        'cbs wijknummer': 'WK051828',
        'buurtnaam': 'Kortenbos',
        'cbs buurtnummer': 'BU05182811',
        'bag nummeraanduiding id': '0518200000747446',
        'straatnaam': 'Spui',
        'huisnummer': 70,
        'huisletter': '',
        'huisnummertoevoeging': '',
        'postcode': '2511 BT',
        'plaats': 'Den Haag',
        'extra adresaanduiding': '',
        'x': '81611',
        'y': '454909',
        'latitude': '52.0775912',
        'longitude': '4.3166395',
        'openingstijd': f'{election_date}T07:30:00',
        'sluitingstijd': f'{election_date}T{closing_time}',
        'toegankelijk voor mensen met een lichamelijke beperking': 'ja',
        'toegankelijke ov-halte': 'ja',
        'gehandicaptentoilet': 'ja',
        'host': 'ja',
        'geleidelijnen': 'buiten en binnen',
        'stemmal met audio-ondersteuning': 'ja',
        'kandidatenlijst in braille': 'ja',
        'kandidatenlijst met grote letters': 'ja',
        'gebarentolk (ngt)': 'op locatie',
        'gebarentalig stembureaulid (ngt)': 'ja',
        'akoestiek geschikt voor slechthorenden': 'ja',
        'prikkelarm': 'ja',
        'extra toegankelijkheidsinformatie': (
            'Dit stembureau is ingericht voor kwetsbare mensen, stembureau is '
            'volledig toegankelijk voor mensen met een lichamelijke beperking er '
            'is echter geen gehandicaptenparkeerplaats, gebarentolk op locatie '
            '(NGT) is aanwezig van 10:00-12:00 en 16:00-18:00, oefenstembureau'
        ),
        'overige informatie': '',
        'kieskring id': "'s-Gravenhage",
        'hoofdstembureau': '',
        'tellocatie': 'ja',
        'contactgegevens gemeente': (
            'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den '
            'Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag'
        ),
        'verkiezingswebsite gemeente': 'https://www.stembureausindenhaag.nl/',
        'verkiezingen': ['waterschapsverkiezingen voor Delfland']
    }
