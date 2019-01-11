#!/usr/bin/env python
import os
import unittest

from xlrd import open_workbook

from app.parser import BaseParser, ExcelParser

test_record = {
    'nummer_stembureau': 517.0,
    'naam_stembureau': 'Stadhuis',
    'website_locatie': 'https://www.denhaag.nl/nl/bestuur-en-organisatie/contact-met-de-gemeente/stadhuis-den-haag.htm',
    'bag_referentienummer': '0518200000747446',
    'extra_adresaanduiding': '',
    'x': '81611.0',
    'y': '454909.0',
    'longitude': '4.3166395',
    'latitude': '52.0775912',
    'openingstijden': '2019-03-20T07:30:00 tot 2019-03-20T21:00:00',
    'mindervaliden_toegankelijk': 'Y',
    'akoestiek': 'N',
    'mindervalide_toilet_aanwezig': 'Y',
    'contactgegevens': 'Unit Verkiezingen, verkiezingen@denhaag.nl 070-3534488 Gemeente Den Haag Publiekszaken/Unit Verkiezingen Postbus 84008 2508 AA Den Haag',
    'beschikbaarheid': 'https://www.stembureausindenhaag.nl/',
    'verkiezingen': ['waterschapsverkiezingen voor Delfland'],
    'bereikbaarheid': '',
    'v1_1_aanduiding_op_openbare_weg': '',
    'v1_2_parkeergelegenheid': '',
    'v1_3_route_tussen_openbare_weg_en_entree_gebouw_stembureau': '',
    'v1_4_route_tussen_entree_gebouw_stembureau_en_stemruimte': '',
    'betreedbaarheid': '',
    'v2_1_entree_buitendeur_van_gebouw_stemlokaal': '',
    'v2_2_tussendeuren_in_de_route_in_het_gebouw_naar_stemruimte': '',
    'v2_3_deur_stemruimte': '',
    'v2_4_tijdelijke_voorzieningen': '',
    'bruikbaarheid': '',
    'v3_1_verkeersruimte_stemlokaal': '',
    'v3_2_stoelen_in_stemruimte': '',
    'v3_3_stemhokje': '',
    'v3_4_stembus': '',
    'v3_5_leesloep': '',
    'v3_6_kandidatenlijst': '',
    'v1_1_a_aanduiding_aanwezig': 'Y',
    'v1_1_b_aanduiding_duidelijk_zichtbaar': 'Y',
    'v1_1_c_aanduiding_goed_leesbaar': 'Y',
    'v1_2_a_gpa_aanwezig': 'N',
    'v1_2_b_aantal_vrij_parkeerplaatsen_binnen_50m_van_de_entree': 6.0,
    'v1_2_c_hoogteverschil_tussen_parkeren_en_trottoir': 'Y',
    'v1_2_d_hoogteverschil': 20.0,
    'v1_2_e_type_overbrugging': 'Helling',
    'v1_2_f_overbrugging_conform_itstandaard': 'Y',
    'v1_3_a_vlak_verhard_en_vrij_van_obstakels': 'Y',
    'v1_3_b_hoogteverschil': 30.0,
    'v1_3_c_type_overbrugging': 'Lift',
    'v1_3_d_overbrugging_conform_itstandaard': 'Y',
    'v1_3_e_obstakelvrije_breedte_van_de_route': 120.0,
    'v1_3_f_obstakelvrije_hoogte_van_de_route': 200.0,
    'v1_4_a_is_er_een_route_tussen_gebouwentree_en_stemruimte': 'Y',
    'v1_4_b_route_duidelijk_aangegeven': 'Y',
    'v1_4_c_vlak_en_vrij_van_obstakels': 'Y',
    'v1_4_d_hoogteverschil': 10.0,
    'v1_4_e_type_overbrugging': 'Helling',
    'v1_4_f_overbrugging_conform_itstandaard': 'Y',
    'v1_4_g_obstakelvrije_breedte_van_de_route': 110.0,
    'v1_4_h_obstakelvrije_hoogte_van_de_route': 220.0,
    'v1_4_i_deuren_in_route_bedien_en_bruikbaar': 'Y',
    'v2_1_a_deurtype': 'Handbediend',
    'v2_1_b_opstelruimte_aan_beide_zijden_van_de_deur': 'Y',
    'v2_1_c_bedieningskracht_buitendeur': '<40N',
    'v2_1_d_drempelhoogte_t_o_v_straat_vloer_niveau': '<2cm',
    'v2_1_e_vrije_doorgangsbreedte_buitendeur': '>85cm',
    'v2_2_a_tussendeuren_aanwezig_in_eventuele_route': 'Y',
    'v2_2_b_deurtype': 'Handbediend',
    'v2_2_c_opstelruimte_aan_beide_zijden_van_de_deur': 'Y',
    'v2_2_d_bedieningskracht_deuren': '<40N',
    'v2_2_e_drempelhoogte_t_o_v_vloer_niveau': '<2cm',
    'v2_2_f_vrije_doorgangsbreedte_deur': '>85cm',
    'v2_3_a_deur_aanwezig_naar_van_stemruimte': 'Y',
    'v2_3_b_deurtype': 'Handbediend',
    'v2_3_c_opstelruimte_aan_beide_zijden_van_de_deur': 'Y',
    'v2_3_d_bedieningskracht_deur': '<40N',
    'v2_3_e_drempelhoogte_t_o_v_vloer_niveau': '<2cm',
    'v2_3_f_vrije_doorgangsbreedte_deur': '>85cm',
    'v2_4_a_zijn_er_tijdelijke_voorzieningen_aangebracht': 'Y',
    'v2_4_b_vloerbedekking_randen_over_de_volle_lengte_deugdelijk_afgeplakt': 'Y',
    'v2_4_c_hellingbaan_weerbestendig_alleen_van_toepassing_bij_buitentoepassing': 'Y',
    'v2_4_d_hellingbaan_deugdelijk_verankerd_aan_ondergrond': 'Y',
    'v2_4_e_leuning_bij_hellingbaan_trap_leuning_aanwezig_en_conform_criteria': 'Y',
    'v2_4_f_dorpeloverbrugging_weerbestendig_alleen_van_toepassing_bij_buitentoepassing': 'Y',
    'v2_4_g_dorpeloverbrugging_deugdelijk_verankerd_aan_ondergrond': 'Y',
    'v3_1_a_obstakelvrije_doorgangen': 'Y',
    'v3_1_b_vrije_draaicirkel_manoeuvreerruimte': 'Y',
    'v3_1_c_idem_voor_stemtafel_en_stemhokje': 'Y',
    'v3_1_d_opstelruimte_voor_naast_stembus': 'Y',
    'v3_2_a_stoelen_in_stemruimte_aanwezig': 'Y',
    'v3_2_b_1_op_5_stoelen_uitgevoerd_met_armleuningen': 'Y',
    'v3_3_a_hoogte_van_het_laagste_schrijfblad': 60.0,
    'v3_3_b_schrijfblad_onderrijdbaar': 'Y',
    'v3_4_a_hoogte_inworpgleuf_stembiljet': 70.0,
    'v3_4_b_afstand_inwerpgleuf_t_o_v_de_opstelruimte': 160.0,
    'v3_5_a_leesloep_zichtbaar_aanwezig': 'Y',
    'v3_6_a_kandidatenlijst_in_stemlokaal_aanwezig': 'Y',
    'v3_6_b_opstelruimte_voor_de_kandidatenlijst_aanwezig': 'Y'
}


class TestBaseParser(unittest.TestCase):
    def setUp(self):
        self.parser = BaseParser()

    def test_parse(self):
        with self.assertRaises(NotImplementedError):
            self.parser.parse('/dev/null')


class TestExcelParser(unittest.TestCase):
    def setUp(self):
        self.parser = ExcelParser()
        self.file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data/waarismijnstemlokaal.nl_invulformulier.xlsx')
        self.records = [test_record, test_record]

    # After running _get_headers and _clean_headers the list
    # of headers should contain all values from column A in
    # the spreadsheet, even the ones that don't hold values
    # (e.g. 'bereikbaarheid')
    def test_get_headers_good(self):
        wb = open_workbook(self.file_path)
        sh = wb.sheet_by_index(1)
        headers = self.parser._get_headers(sh)
        clean_headers = self.parser._clean_headers(headers)
        self.assertListEqual(
            clean_headers,
            [
                'nummer_stembureau',
                'naam_stembureau',
                'website_locatie',
                'bag_referentienummer',
                'extra_adresaanduiding',
                'x',
                'y',
                'longitude',
                'latitude',
                'openingstijden',
                'mindervaliden_toegankelijk',
                'akoestiek',
                'mindervalide_toilet_aanwezig',
                'contactgegevens',
                'beschikbaarheid',
                'verkiezingen',
                'bereikbaarheid',
                'v1_1_aanduiding_op_openbare_weg',
                'v1_1_a_aanduiding_aanwezig',
                'v1_1_b_aanduiding_duidelijk_zichtbaar',
                'v1_1_c_aanduiding_goed_leesbaar',
                'v1_2_parkeergelegenheid',
                'v1_2_a_gpa_aanwezig',
                'v1_2_b_aantal_vrij_parkeerplaatsen_binnen_50m_van_de_entree',
                'v1_2_c_hoogteverschil_tussen_parkeren_en_trottoir',
                'v1_2_d_hoogteverschil',
                'v1_2_e_type_overbrugging',
                'v1_2_f_overbrugging_conform_itstandaard',
                'v1_3_route_tussen_openbare_weg_en_entree_gebouw_stembureau',
                'v1_3_a_vlak_verhard_en_vrij_van_obstakels',
                'v1_3_b_hoogteverschil',
                'v1_3_c_type_overbrugging',
                'v1_3_d_overbrugging_conform_itstandaard',
                'v1_3_e_obstakelvrije_breedte_van_de_route',
                'v1_3_f_obstakelvrije_hoogte_van_de_route',
                'v1_4_route_tussen_entree_gebouw_stembureau_en_stemruimte',
                'v1_4_a_is_er_een_route_tussen_gebouwentree_en_stemruimte',
                'v1_4_b_route_duidelijk_aangegeven',
                'v1_4_c_vlak_en_vrij_van_obstakels',
                'v1_4_d_hoogteverschil',
                'v1_4_e_type_overbrugging',
                'v1_4_f_overbrugging_conform_itstandaard',
                'v1_4_g_obstakelvrije_breedte_van_de_route',
                'v1_4_h_obstakelvrije_hoogte_van_de_route',
                'v1_4_i_deuren_in_route_bedien_en_bruikbaar',
                'betreedbaarheid',
                'v2_1_entree_buitendeur_van_gebouw_stemlokaal',
                'v2_1_a_deurtype',
                'v2_1_b_opstelruimte_aan_beide_zijden_van_de_deur',
                'v2_1_c_bedieningskracht_buitendeur',
                'v2_1_d_drempelhoogte_t_o_v_straat_vloer_niveau',
                'v2_1_e_vrije_doorgangsbreedte_buitendeur',
                'v2_2_tussendeuren_in_de_route_in_het_gebouw_naar_stemruimte',
                'v2_2_a_tussendeuren_aanwezig_in_eventuele_route',
                'v2_2_b_deurtype',
                'v2_2_c_opstelruimte_aan_beide_zijden_van_de_deur',
                'v2_2_d_bedieningskracht_deuren',
                'v2_2_e_drempelhoogte_t_o_v_vloer_niveau',
                'v2_2_f_vrije_doorgangsbreedte_deur',
                'v2_3_deur_stemruimte',
                'v2_3_a_deur_aanwezig_naar_van_stemruimte',
                'v2_3_b_deurtype',
                'v2_3_c_opstelruimte_aan_beide_zijden_van_de_deur',
                'v2_3_d_bedieningskracht_deur',
                'v2_3_e_drempelhoogte_t_o_v_vloer_niveau',
                'v2_3_f_vrije_doorgangsbreedte_deur',
                'v2_4_tijdelijke_voorzieningen',
                'v2_4_a_zijn_er_tijdelijke_voorzieningen_aangebracht',
                'v2_4_b_vloerbedekking_randen_over_de_volle_lengte_deugdelijk_afgeplakt',
                'v2_4_c_hellingbaan_weerbestendig_alleen_van_toepassing_bij_buitentoepassing',
                'v2_4_d_hellingbaan_deugdelijk_verankerd_aan_ondergrond',
                'v2_4_e_leuning_bij_hellingbaan_trap_leuning_aanwezig_en_conform_criteria',
                'v2_4_f_dorpeloverbrugging_weerbestendig_alleen_van_toepassing_bij_buitentoepassing',
                'v2_4_g_dorpeloverbrugging_deugdelijk_verankerd_aan_ondergrond',
                'bruikbaarheid',
                'v3_1_verkeersruimte_stemlokaal',
                'v3_1_a_obstakelvrije_doorgangen',
                'v3_1_b_vrije_draaicirkel_manoeuvreerruimte',
                'v3_1_c_idem_voor_stemtafel_en_stemhokje',
                'v3_1_d_opstelruimte_voor_naast_stembus',
                'v3_2_stoelen_in_stemruimte',
                'v3_2_a_stoelen_in_stemruimte_aanwezig',
                'v3_2_b_1_op_5_stoelen_uitgevoerd_met_armleuningen',
                'v3_3_stemhokje',
                'v3_3_a_hoogte_van_het_laagste_schrijfblad',
                'v3_3_b_schrijfblad_onderrijdbaar',
                'v3_4_stembus',
                'v3_4_a_hoogte_inworpgleuf_stembiljet',
                'v3_4_b_afstand_inwerpgleuf_t_o_v_de_opstelruimte',
                'v3_5_leesloep',
                'v3_5_a_leesloep_zichtbaar_aanwezig',
                'v3_6_kandidatenlijst',
                'v3_6_a_kandidatenlijst_in_stemlokaal_aanwezig',
                'v3_6_b_opstelruimte_voor_de_kandidatenlijst_aanwezig'
            ]
        )

    # Test if the records are parsed correctly. This should still
    # include the fields that will not hold any value (e.g.,
    # 'bereikbaarheid') and exclude all fields that are added
    # later (e.g., 'gemeente')
    def test_get_rows_good(self):
        rows = self.parser.parse(self.file_path)
        self.maxDiff = None
        self.assertDictEqual(rows[0], self.records[0])
        self.assertDictEqual(rows[1], self.records[1])
