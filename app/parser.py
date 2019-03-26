#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re

from app import app
from pyexcel_ods3 import get_data
from xlrd import open_workbook


valid_headers = [
    'Nummer stembureau',
    'Naam stembureau',
    'Website locatie',
    'BAG referentie nummer',
    'Extra adresaanduiding',
    'Longitude',
    'Latitude',
    'X',
    'Y',
    'Openingstijden',
    'Mindervaliden toegankelijk',
    'Akoestiek',
    'Mindervalide toilet aanwezig',
    'Contactgegevens',
    'Beschikbaarheid',
    'Verkiezingen',
    '1.1.a Aanduiding aanwezig',
    '1.1.b Aanduiding duidelijk zichtbaar',
    '1.1.c Aanduiding goed leesbaar',
    '1.2.a GPA aanwezig',
    '1.2.b Aantal vrij parkeerplaatsen binnen 50m van de entree',
    '1.2.c Hoogteverschil tussen parkeren en trottoir',
    '1.2.d Hoogteverschil',
    '1.2.e Type overbrugging',
    '1.2.f Overbrugging conform ITstandaard',
    '1.3.a Vlak, verhard en vrij van obstakels',
    '1.3.b Hoogteverschil',
    '1.3.c Type overbrugging',
    '1.3.d Overbrugging conform ITstandaard',
    '1.3.e Obstakelvrije breedte van de route',
    '1.3.f Obstakelvrije hoogte van de route',
    '1.4.a Is er een route tussen gebouwentree en stemruimte',
    '1.4.b Route duidelijk aangegeven',
    '1.4.c Vlak en vrij van obstakels',
    '1.4.d Hoogteverschil',
    '1.4.e Type overbrugging',
    '1.4.f Overbrugging conform ITstandaard',
    '1.4.g Obstakelvrije breedte van de route',
    '1.4.h Obstakelvrije hoogte van de route',
    '1.4.i Deuren in route bedien- en bruikbaar',
    '2.1.a Deurtype',
    '2.1.b Opstelruimte aan beide zijden van de deur',
    '2.1.c Bedieningskracht buitendeur',
    '2.1.d Drempelhoogte (t.o.v. straat/vloer niveau)',
    '2.1.e Vrije doorgangsbreedte buitendeur',
    '2.2.a Tussendeuren aanwezig in eventuele route',
    '2.2.b Deurtype',
    '2.2.c Opstelruimte aan beide zijden van de deur',
    '2.2.d Bedieningskracht deuren',
    '2.2.e Drempelhoogte (t.o.v. vloer niveau)',
    '2.2.f Vrije doorgangsbreedte deur',
    '2.3.a Deur aanwezig naar/van stemruimte',
    '2.3.b Deurtype',
    '2.3.c Opstelruimte aan beide zijden van de deur',
    '2.3.d Bedieningskracht deur',
    '2.3.e Drempelhoogte (t.o.v. vloer niveau)',
    '2.3.f Vrije doorgangsbreedte deur',
    '2.4.a Zijn er tijdelijke voorzieningen aangebracht',
    '2.4.b VLOERBEDEKKING: Randen over de volle lengte deugdelijk afgeplakt',
    (
        '2.4.c HELLINGBAAN: Weerbestendig (alleen van toepassing bij '
        'buitentoepassing)'
    ),
    '2.4.d HELLINGBAAN: Deugdelijk verankerd aan ondergrond',
    '2.4.e LEUNING BIJ HELLINGBAAN/TRAP: Leuning aanwezig en conform criteria',
    (
        '2.4.f DORPELOVERBRUGGING: Weerbestendig (alleen van toepassing bij '
        'buitentoepassing)'
    ),
    '2.4.g DORPELOVERBRUGGING: Deugdelijk verankerd aan ondergrond',
    '3.1.a Obstakelvrije doorgangen',
    '3.1.b Vrije draaicirkel / manoeuvreerruimte',
    '3.1.c Idem voor stemtafel en stemhokje',
    '3.1.d Opstelruimte voor/naast stembus',
    '3.2.a Stoelen in stemruimte aanwezig',
    '3.2.b 1 op 5 Stoelen uitgevoerd met armleuningen',
    '3.3.a Hoogte van het laagste schrijfblad',
    '3.3.b Schrijfblad onderrijdbaar',
    '3.4.a Hoogte inworpgleuf stembiljet',
    '3.4.b Afstand inwerpgleuf t.o.v. de opstelruimte',
    '3.5.a Leesloep (zichtbaar) aanwezig',
    '3.6.a Kandidatenlijst in stemlokaal aanwezig',
    '3.6.b Opstelruimte voor de kandidatenlijst aanwezig'
]

parse_as_integer = [
    'nummer_stembureau',
    'v1_2_b_aantal_vrij_parkeerplaatsen_binnen_50m_van_de_entree',
    'v1_2_d_hoogteverschil',
    'v1_3_b_hoogteverschil',
    'v1_3_e_obstakelvrije_breedte_van_de_route',
    'v1_3_f_obstakelvrije_hoogte_van_de_route',
    'v1_4_d_hoogteverschil',
    'v1_4_g_obstakelvrije_breedte_van_de_route',
    'v1_4_h_obstakelvrije_hoogte_van_de_route',
    'v3_3_a_hoogte_van_het_laagste_schrijfblad',
    'v3_4_a_hoogte_inworpgleuf_stembiljet',
    'v3_4_b_afstand_inwerpgleuf_t_o_v_de_opstelruimte'
]

yes_no_empty_fields = [
    'mindervaliden_toegankelijk',
    'akoestiek',
    'mindervalide_toilet_aanwezig',
    'v1_1_a_aanduiding_aanwezig',
    'v1_1_b_aanduiding_duidelijk_zichtbaar',
    'v1_1_c_aanduiding_goed_leesbaar',
    'v1_2_a_gpa_aanwezig',
    'v1_2_c_hoogteverschil_tussen_parkeren_en_trottoir',
    'v1_2_f_overbrugging_conform_itstandaard',
    'v1_3_a_vlak_verhard_en_vrij_van_obstakels',
    'v1_3_d_overbrugging_conform_itstandaard',
    'v1_4_a_is_er_een_route_tussen_gebouwentree_en_stemruimte',
    'v1_4_b_route_duidelijk_aangegeven',
    'v1_4_c_vlak_en_vrij_van_obstakels',
    'v1_4_f_overbrugging_conform_itstandaard',
    'v1_4_i_deuren_in_route_bedien_en_bruikbaar',
    'v2_1_b_opstelruimte_aan_beide_zijden_van_de_deur',
    'v2_2_a_tussendeuren_aanwezig_in_eventuele_route',
    'v2_2_c_opstelruimte_aan_beide_zijden_van_de_deur',
    'v2_3_a_deur_aanwezig_naar_van_stemruimte',
    'v2_3_c_opstelruimte_aan_beide_zijden_van_de_deur',
    'v2_4_a_zijn_er_tijdelijke_voorzieningen_aangebracht',
    'v2_4_b_vloerbedekking_randen_over_de_volle_lengte_deugdelijk_afgeplakt',
    (
        'v2_4_c_hellingbaan_weerbestendig_alleen_van_toepassing_bij_'
        'buitentoepassing'
    ),
    'v2_4_d_hellingbaan_deugdelijk_verankerd_aan_ondergrond',
    'v2_4_e_leuning_bij_hellingbaan_trap_leuning_aanwezig_en_conform_criteria',
    (
        'v2_4_f_dorpeloverbrugging_weerbestendig_alleen_van_toepassing_bij_'
        'buitentoepassing'
    ),
    'v2_4_g_dorpeloverbrugging_deugdelijk_verankerd_aan_ondergrond',
    'v3_1_a_obstakelvrije_doorgangen',
    'v3_1_b_vrije_draaicirkel_manoeuvreerruimte',
    'v3_1_c_idem_voor_stemtafel_en_stemhokje',
    'v3_1_d_opstelruimte_voor_naast_stembus',
    'v3_2_a_stoelen_in_stemruimte_aanwezig',
    'v3_2_b_1_op_5_stoelen_uitgevoerd_met_armleuningen',
    'v3_3_b_schrijfblad_onderrijdbaar',
    'v3_5_a_leesloep_zichtbaar_aanwezig',
    'v3_6_a_kandidatenlijst_in_stemlokaal_aanwezig',
    'v3_6_b_opstelruimte_voor_de_kandidatenlijst_aanwezig'
]

overbrugging_fields = [
    'v1_2_e_type_overbrugging',
    'v1_3_c_type_overbrugging',
    'v1_4_e_type_overbrugging'
]

deurtype_fields = [
    'v2_1_a_deurtype',
    'v2_2_b_deurtype',
    'v2_3_b_deurtype'
]

bedieningskracht_fields = [
    'v2_1_c_bedieningskracht_buitendeur',
    'v2_2_d_bedieningskracht_deuren',
    'v2_3_d_bedieningskracht_deur'
]

drempelhoogte_fields = [
    'v2_1_d_drempelhoogte_t_o_v_straat_vloer_niveau',
    'v2_2_e_drempelhoogte_t_o_v_vloer_niveau',
    'v2_3_e_drempelhoogte_t_o_v_vloer_niveau'
]

doorgangsbreedte_fields = [
    'v2_1_e_vrije_doorgangsbreedte_buitendeur',
    'v2_2_f_vrije_doorgangsbreedte_deur',
    'v2_3_f_vrije_doorgangsbreedte_deur'
]


class BaseParser(object):
    def __init__(self, *args, **kwargs):
        pass

    def _header_valid(self, header):
        if isinstance(header, str):
            if header in valid_headers:
                return True
            else:
                return False
        else:
            return False

    # Rename columnnames which use different spellings
    def _clean_headers(self, headers):
        for idx, header in enumerate(headers):
            if header == 'bag_referentie_nummer':
                headers[idx] = 'bag_referentienummer'

        return headers

    def _clean_records(self, records):
        # Convert variations of 'Y' and 'N' to 'Y' and 'N'
        for record in records:
            for yes_no_empty_field in yes_no_empty_fields:
                if yes_no_empty_field in record:
                    if re.match('^[YyJj]$', str(record[yes_no_empty_field])):
                        record[yes_no_empty_field] = 'Y'
                    elif re.match('^[Nn]$', str(record[yes_no_empty_field])):
                        record[yes_no_empty_field] = 'N'

            for overbrugging_field in overbrugging_fields:
                if overbrugging_field in record:
                    match = str(record[overbrugging_field])
                    if re.match('^Helling$', match, re.IGNORECASE):
                        record[overbrugging_field] = 'Helling'
                    elif re.match('^Trap$', match, re.IGNORECASE):
                        record[overbrugging_field] = 'Trap'
                    elif re.match('^Lift$', match, re.IGNORECASE):
                        record[overbrugging_field] = 'Lift'
                    elif re.match('^Geen$', match, re.IGNORECASE):
                        record[overbrugging_field] = 'Geen'

            for deurtype_field in deurtype_fields:
                if deurtype_field in record:
                    match = str(record[deurtype_field])
                    if re.match('^Handbediend$', match, re.IGNORECASE):
                        record[deurtype_field] = 'Handbediend'
                    elif re.match('^Automatisch$', match, re.IGNORECASE):
                        record[deurtype_field] = 'Automatisch'

            for bedieningskracht_field in bedieningskracht_fields:
                if bedieningskracht_field in record:
                    match = str(record[bedieningskracht_field])
                    if re.match('^<40N$', match, re.IGNORECASE):
                        record[bedieningskracht_field] = '<40N'
                    elif re.match('^>40N$', match, re.IGNORECASE):
                        record[bedieningskracht_field] = '>40N'

            for drempelhoogte_field in drempelhoogte_fields:
                if drempelhoogte_field in record:
                    match = str(record[drempelhoogte_field])
                    if re.match('^<2cm$', match, re.IGNORECASE):
                        record[drempelhoogte_field] = '<2cm'
                    elif re.match('^>2cm$', match, re.IGNORECASE):
                        record[drempelhoogte_field] = '>2cm'

            for doorgangsbreedte_field in doorgangsbreedte_fields:
                if doorgangsbreedte_field in record:
                    match = str(record[doorgangsbreedte_field])
                    if re.match('^<85cm$', match, re.IGNORECASE):
                        record[doorgangsbreedte_field] = '<85cm'
                    elif re.match('^>85cm$', match, re.IGNORECASE):
                        record[doorgangsbreedte_field] = '>85cm'

            # Split the Verkiezingen string into a list in order to validate
            # the content. Afterwards in _create_record the list will be
            # changed back to a string again to save in CKAN.
            if record.get('verkiezingen'):
                record['verkiezingen'] = [
                    x.strip() for x in record['verkiezingen'].split(';')
                ]

        return records

    def _clean_bag_referentienummer(self, record):
        # Left pad this field with max 3 zeroes
        if len(record['bag_referentienummer']) == 15:
            record['bag_referentienummer'] = '0' + record[
                'bag_referentienummer'
            ]
        if len(record['bag_referentienummer']) == 14:
            record['bag_referentienummer'] = '00' + record[
                'bag_referentienummer'
            ]
        if len(record['bag_referentienummer']) == 13:
            record['bag_referentienummer'] = '000' + record[
                'bag_referentienummer'
            ]

        return record

    def parse(self, path):
        """
        Parses a file (Assumes). Returns a tuple of a list of headers and
        a list of records.
        """
        raise NotImplementedError


class ODSParser(BaseParser):
    # Retrieve field names, lowercase them and replace spaces with
    # underscores
    def _get_headers(self, sh):
        headers = []
        found_valid_headers = False
        for header in sh[1:]:
            if header:
                if self._header_valid(header[0]):
                    found_valid_headers = True
                headers.append(str(header[0]).lower().replace(' ', '_'))
        if not found_valid_headers:
            app.logger.warning('Geen geldige veldnamen gevonden in bestand')
            raise ValueError()
        return headers

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, len(sh[0])):
            record = {}
            for idx, row in enumerate(sh[1:len(clean_headers)+1]):
                if row:
                    # No values left
                    if len(row) - 1 < col_num or len(row) <= 5:
                        continue
                    value = row[col_num]
                    try:
                        # Convert all to str except for bag_referentienummer
                        # as this field is interpreted as float by Excel so
                        # first cast it to int and then to str
                        if clean_headers[idx] == 'bag_referentienummer':
                            if type(value) == float or type(value) == int:
                                record[clean_headers[idx]] = str(
                                    int(value)
                                ).strip()
                            else:
                                record[clean_headers[idx]] = value.strip()
                        elif clean_headers[idx] == 'nummer_stembureau':
                            record[clean_headers[idx]] = value
                        else:
                            record[clean_headers[idx]] = str(value).strip()
                    except IndexError:
                        record[clean_headers[idx]] = ''

            if 'bag_referentienummer' in record:
                record = self._clean_bag_referentienummer(record)
            records.append(record)

        return records

    def parse(self, path):
        headers = []
        if not os.path.exists(path):
            return [], []

        wb = get_data(path)
        sh = wb['Attributen']

        headers = self._get_headers(sh)
        clean_headers = self._clean_headers(headers)

        records = self._get_records(sh, clean_headers)
        clean_records = self._clean_records(records)

        return clean_records


class ExcelParser(BaseParser):
    # Retrieve field names, lowercase them and replace spaces with
    # underscores
    def _get_headers(self, sh):
        headers = []
        all_headers_check = []
        found_valid_headers = False
        for header in sh.col_values(0)[1:]:
            if self._header_valid(header):
                found_valid_headers = True
                all_headers_check.append(header)
            # The mindervaliden checklist field names start with a
            # number, so we prepend those names with a 'v' (from
            # 'veld')
            if re.match('\d', str(header)):
                header = 'v' + str(header)
            # 'Slugify' the field name
            headers.append(
                re.sub(
                    '_+',
                    '_',
                    re.sub(
                        '[/: .,()\-]', '_', str(header).lower()
                    )
                ).rstrip('_').replace('\n', '')
            )
        if not found_valid_headers:
            app.logger.warning('Geen geldige veldnamen gevonden in bestand')
            raise ValueError()
        if sorted(valid_headers) != sorted(all_headers_check):
            app.logger.warning('Spreadsheet bevat niet alle veldnamen')
            raise ValueError()
        return headers

    def _get_records(self, sh, clean_headers):
        records = []
        for col_num in range(5, sh.ncols):
            record = {}
            for idx, value in enumerate(
                    sh.col_values(col_num)[1:len(clean_headers)+1]):
                # Convert all to str except for bag_referentienummer
                # as this field is interpreted as float by Excel so
                # first cast it to int and then to str
                if clean_headers[idx] == 'bag_referentienummer':
                    if type(value) == float or type(value) == int:
                        record[clean_headers[idx]] = str(
                            int(value)
                        ).strip()
                    else:
                        record[clean_headers[idx]] = value.strip()
                elif clean_headers[idx] in parse_as_integer:
                    record[clean_headers[idx]] = value
                else:
                    record[clean_headers[idx]] = str(value).strip()

            record = self._clean_bag_referentienummer(record)
            records.append(record)

        return records

    def parse(self, path):
        headers = []
        if not os.path.exists(path):
            return [], []

        wb = open_workbook(path)

        # als we 1 tab hebben dan de eerste, anders de tweede
        if wb.nsheets == 1:
            nsh = 0
        else:
            nsh = 1
        sh = wb.sheet_by_index(nsh)

        headers = self._get_headers(sh)
        clean_headers = self._clean_headers(headers)

        records = self._get_records(sh, clean_headers)
        clean_records = self._clean_records(records)

        return clean_records


class UploadFileParser(BaseParser):
    PARSERS = {
        '.ods': ODSParser,
        '.xlsx': ExcelParser,
        '.xls': ExcelParser
    }

    def parse(self, path):
        headers = []
        records = []
        if not os.path.exists(path):
            return [], []
        _, extension = os.path.splitext(path)
        if extension in self.PARSERS.keys():
            klass = self.PARSERS[extension]
            parser = klass()
            records = parser.parse(path)
        return records
