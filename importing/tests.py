import unittest

import importer as imp

import common

table_info = common.MyTable()


class ImportTests(unittest.TestCase):

    def test_naml_fix(self):
        # correct would be:
        #
        # FILING_ID: '1111'
        # A_NAML: 'Smith'
        # A_NMAF: 'Joseph'
        # OTHER: 'yes'
        # B_NAML: 'Franklin'
        # B_NAMF: 'Bob'
        # NEXT: 'no'
        # C_NAML: 'Adams'
        # C_NAMF: 'Sally'
        # LAST: 'something'
        #

        head = ['FILING_ID', 'A_NAML', 'A_NAMF', 'OTHER',
                'B_NAML', 'B_NAMF', 'NEXT', 'C_NAML', 'C_NAMF', 'LAST']

        good_row = ['1111', 'Smith', 'Joseph', 'yes',
                    'Franklin', 'Bob', 'no', 'Adams', 'Sally', 'something']

        result = imp.fix_empty_naml(head, good_row)
        self.assertEqual(good_row, result)

        bad_row = ['1111', '', 'Smith', 'Joseph', 'yes',
                   'Franklin', 'Bob', 'no', 'Adams', 'Sally', 'something']

        result = imp.fix_empty_naml(head, bad_row)
        self.assertEqual(good_row, result)

        bad_row = ['1111', '', 'Smith', 'Joseph', 'yes',
                   '', 'Franklin', 'Bob', 'no', '', '', 'Adams', 'Sally', 'something']

        result = imp.fix_empty_naml(head, bad_row)
        self.assertEqual(good_row, result)

    def test_column_definitions(self):
        bm = table_info.table_columns()['ballot_measures']
        self.assertTrue('election_date' in list(bm.keys())[0])
        self.assertEqual(6, len(bm.keys()))

    def test_fix_broken_lines_NAMES(self):
        # line 307138: [
        #   0 '1347670',
        #   1 'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)'
        # ]
        #     parts # 2
        #
        # line 307139: [
        #   0 '',
        #   1 '',
        #   2 '',
        #   3 '',
        #   4 '',
        #   5 '',
        #   6 '',
        #   7 '',
        #   8 'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)'
        #  ]
        #     parts # 9
        #
        # NAMES has columns:
        #     NAMID   NAML    NAMF    NAMT    NAMS    MONIKER    MONIKER_POS
        #     NAMM    FULLNAME        NAML_SEARCH
        #     parts # 10
        #
        columns = ['NAMID', 'NAML', 'NAMF', 'NAMT', 'NAMS', 'MONIKER',
                   'MONIKER_POS', 'NAMM', 'FULLNAME', 'NAML_SEARCH']
        lines = [
            ['1347670', 'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)'],
            ['', '', '', '', '', '', '', '',
             'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data']
        ]
        expected = {
            'NAMID': '1347670',
            'NAML': 'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)',
            'NAMF': None,
            'NAMT': None,
            'NAMS': None,
            'MONIKER': None,
            'MONIKER_POS': None,
            'NAMM': None,
            'FULLNAME': None,
            'NAML_SEARCH': 'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)'
        }

        result = imp.importable_lines('names', columns, lines)
        self.assertEqual(expected, result)

    def _test_too_many_fields_CVR_CAMPAIGN_DISCLOSURE_1(self):
        # ERROR: 429
        # {
        #     0 FILING_ID: |591205|
        #     1 AMEND_ID: |0|
        #     2 REC_TYPE: |CVR|
        #     3 FORM_TYPE: |F460|
        #     4 FILER_ID: |962652|
        #     5 ENTITY_CD: |RCP|
        #     6 FILER_NAML: |Wesson For Assembly|
        #     7 FILER_NAMF: ||
        #     8 FILER_NAMT: ||
        #     9 FILER_NAMS: ||
        #     10 REPORT_NUM: |000|
        #     11 RPT_DATE: |2/23/2000 12:00:00 AM|
        #     12 STMT_TYPE: |PE|
        #     13 LATE_RPTNO: ||
        #     14 FROM_DATE: |1/23/2000 12:00:00 AM|
        #     15 THRU_DATE: |2/19/2000 12:00:00 AM|
        #     16 ELECT_DATE: |3/7/2000 12:00:00 AM|
        #     17 FILER_CITY: |Marina Del Rey|
        #     18 FILER_ST: |CA|
        #     19 FILER_ZIP4: |90292|
        #     20 FILER_PHON: |310-822-1742|
        #     21 FILER_FAX: ||
        #     22 FILE_EMAIL: ||
        #     23 MAIL_CITY: ||
        #     24 MAIL_ST: ||
        #     25 MAIL_ZIP4: ||
        #     26 TRES_NAML: |Wasson|
        #     27 TRES_NAMF: |Jan|
        #     28 TRES_NAMT: |Ms.|
        #     29 TRES_NAMS: ||
        #     30 TRES_CITY: |Marina Del Rey|
        #     31 TRES_ST: |CA|
        #     32 TRES_ZIP4: |90292|
        #     33 TRES_PHON: |310-822-1742|
        #     34 TRES_FAX: ||
        #     35 TRES_EMAIL: ||
        #     36 CMTTE_TYPE: |C|
        #     37 CONTROL_YN: ||
        #     38 SPONSOR_YN: ||
        #     39 PRIMFRM_YN: ||
        #     40 BRDBASE_YN: ||
        #     41 AMENDEXP_1: ||
        #     42 AMENDEXP_2: ||
        #     43 AMENDEXP_3: ||
        #     44 RPT_ATT_CB: ||
        #     45 CMTTE_ID: ||
        #     46 REPORTNAME: ||
        #     47 RPTFROMDT: ||
        #     48 RPTTHRUDT: ||
        #     49 EMPLBUS_CB: ||
        #     50 BUS_NAME: ||
        #     51 BUS_CITY: ||
        #     52 BUS_ST: ||
        #     53 BUS_ZIP4: ||
        #     54 BUS_INTER: ||
        #     55 BUSACT_CB: ||
        #     56 BUSACTVITY: ||
        #     57 ASSOC_CB: ||
        #     58 ASSOC_INT: ||
        #     59 OTHER_CB: ||
        #     60 OTHER_INT: ||
        #     61 CAND_NAML: ||
        #     62 CAND_NAMF: ||
        #     63 CAND_NAMT: ||
        #     64 CAND_NAMS: |Wesson|
        #     65 CAND_CITY: |Herman Jason|
        #     66 CAND_ST: |Mr.|
        #     67 CAND_ZIP4: |Jr.|
        #     68 CAND_PHON: |Sacramento|
        #     69 CAND_FAX: |CA|
        #     70 CAND_EMAIL: |95814|
        #     71 BAL_NAME: |310-822-1742|
        #     72 BAL_NUM: ||
        #     73 BAL_JURIS: ||
        #     74 OFFICE_CD: ||
        #     75 OFFIC_DSCR: ||
        #     76 JURIS_CD: ||
        #     77 JURIS_DSCR: |ASM|
        #     78 DIST_NO: ||
        #     79 OFF_S_H_CD: |ASM|
        #     80 SUP_OPP_CD: ||
        #     81 EMPLOYER: |47|
        #     82 OCCUPATION: ||
        #     83 SELFEMP_CB: ||
        #     84 BAL_ID: ||
        #     85 CAND_ID: ||
        #     86 MISSING: ||
        #     87 MISSING: ||
        #     88 MISSING: ||
        # }
        pass

    def _test_too_many_fields_CVR_CAMPAIGN_DISCLOSURE_2(self):
        # ERROR: 899
        # {
        #     0 filing_id: |591313|
        #     1 amend_id: |0|
        #     2 rec_type: |CVR|
        #     3 form_type: |F460|
        #     4 filer_id: |971861|
        #     5 entity_cd: |RCP|
        #     6 filer_naml: |Bob Pacheco for Assembly 2000|
        #     7 filer_namf: ||
        #     8 filer_namt: ||
        #     9 filer_nams: ||
        #     10 report_num: |000|
        #     11 rpt_date: |2/23/2000 12:00:00 AM|
        #     12 stmt_type: |PE|
        #     13 late_rptno: ||
        #     14 from_date: |1/23/2000 12:00:00 AM|
        #     15 thru_date: |2/19/2000 12:00:00 AM|
        #     16 elect_date: |3/7/2000 12:00:00 AM|
        #     17 filer_city: |Riverside|
        #     18 filer_st: |CA|
        #     19 filer_zip4: |92507|
        #     20 filer_phon: |909-781-2910|
        #     21 filer_fax: ||
        #     22 file_email: ||
        #     23 mail_city: ||
        #     24 mail_st: ||
        #     25 mail_zip4: ||
        #     26 tres_naml: |Trimble CPA|
        #     27 tres_namf: |James|
        #     28 tres_namt: ||
        #     29 tres_nams: ||
        #     30 tres_city: |Riverside|
        #     31 tres_st: |CA|
        #     32 tres_zip4: |92507|
        #     33 tres_phon: |909-781-2910|
        #     34 tres_fax: ||
        #     35 tres_email: ||
        #     36 cmtte_type: |C|
        #     37 control_yn: ||
        #     38 sponsor_yn: ||
        #     39 primfrm_yn: ||
        #     40 brdbase_yn: ||
        #     41 amendexp_1: ||
        #     42 amendexp_2: ||
        #     43 amendexp_3: ||
        #     44 rpt_att_cb: ||
        #     45 cmtte_id: ||
        #     46 reportname: ||
        #     47 rptfromdt: ||
        #     48 rptthrudt: ||
        #     49 emplbus_cb: ||
        #     50 bus_name: ||
        #     51 bus_city: ||
        #     52 bus_st: ||
        #     53 bus_zip4: ||
        #     54 bus_inter: ||
        #     55 busact_cb: ||
        #     56 busactvity: ||
        #     57 assoc_cb: ||
        #     58 assoc_int: ||
        #     59 other_cb: ||
        #     60 other_int: ||
        #     61 cand_naml: ||
        #     62 cand_namf: ||
        #     63 cand_namt: ||
        #     64 cand_nams: ||
        #     65 cand_city: ||
        #     66 cand_st: ||
        #     67 cand_zip4: ||
        #     68 cand_phon: ||
        #     69 cand_fax: ||
        #     70 cand_email: ||
        #     71 bal_name: ||
        #     72 bal_num: ||
        #     73 bal_juris: ||
        #     74 office_cd: ||
        #     75 offic_dscr: ||
        #     76 juris_cd: ||
        #     77 juris_dscr: ||
        #     78 dist_no: ||
        #     79 off_s_h_cd: ||
        #     80 sup_opp_cd: ||
        #     81 employer: ||
        #     82 occupation: ||
        #     83 selfemp_cb: ||
        #     84 bal_id: ||
        #     85 cand_id: ||
        #     86 MISSING: ||
        #     87 MISSING: ||
        #     88 MISSING: |Pacheco|
        #     89 MISSING: |Robert|
        #     90 MISSING: ||
        #     91 MISSING: ||
        #     92 MISSING: |Walnut|
        #     93 MISSING: |CA|
        #     94 MISSING: |91789|
        #     95 MISSING: |909-781-2910|
        #     96 MISSING: |909-788-6135|
        #     97 MISSING: ||
        #     98 MISSING: ||
        #     99 MISSING: ||
        #     100 MISSING: ||
        #     101 MISSING: |ASM|
        #     102 MISSING: ||
        #     103 MISSING: |ASM|
        #     104 MISSING: ||
        #     105 MISSING: |60|
        #     106 MISSING: ||
        #     107 MISSING: ||
        #     108 MISSING: ||
        #     109 MISSING: ||
        #     110 MISSING: ||
        #     111 MISSING: ||
        #     112 MISSING: ||
        # }
        pass

    def _test_fix_CVR_SO_CD(self):
        # ERROR: 46077
        #
        # {
        #     0 FILING_ID: |1389096|
        #     1 AMEND_ID: |2|
        #     2 LINE_ITEM: |5|
        #     3 REC_TYPE: |CVR2|
        #     4 FORM_TYPE: |F410|
        #     5 TRAN_ID: |SPO1|
        #     6 ENTITY_CD: |SPO|
        #     7 ENTY_NAML: ||
        #     8 ENTY_NAMF: |Service Employees International Union Local 721 CTW, CLC|
        #     9 ENTY_NAMT: ||
        #     10 ENTY_NAMS: ||
        #     11 ITEM_CD: ||
        #     12 MAIL_CITY: |SPO|
        #     13 MAIL_ST: |Los Angeles|
        #     14 MAIL_ZIP4: |CA|
        #     15 DAY_PHONE: |90017|
        #     16 FAX_PHONE: |(213)368-8660|
        #     17 EMAIL_ADR: ||
        #     18 CMTE_ID: ||
        #     19 IND_GROUP: ||
        #     20 OFFICE_CD: |Labor Organization|
        #     21 OFFIC_DSCR: ||
        #     22 JURIS_CD: ||
        #     23 JURIS_DSCR: ||
        #     24 DIST_NO: ||
        #     25 OFF_S_H_CD: ||
        #     26 NON_PTY_CB: ||
        #     27 PARTY_NAME: ||
        #     28 BAL_NUM: ||
        #     29 BAL_JURIS: ||
        #     30 SUP_OPP_CD: ||
        #     31 YEAR_ELECT: ||
        #     32 POF_TITLE: ||
        #     33 MISSING: ||
        # }
        pass

    def test_fix_broken_lines_FILERNAME(self):
        # {   lines[1]                                  lines[0]
        #     0 XREF_FILER_ID: |1449339|
        #     1 FILER_ID: |1449339|
        #     2 FILER_TYPE: |RECIPIENT COMMITTEE|
        #     3 STATUS: |ACTIVE|				        ERROR: 1131229
        #     4 EFFECT_DT: |07/15/2022|			        {
        #     5 NAML: |MARROCCO FOR TRUSTEE 2022; RENA|	    0 XREF_FILER_ID: ||
        #     6 NAMF: MISSING				                1 FILER_ID: ||
        #     7 NAMT: MISSING				                2 FILER_TYPE: ||
        #     8 NAMS: MISSING				                3 STATUS: ||
        #     9 ADR1: MISSING				                4 EFFECT_DT: ||
        #     10 ADR2: MISSING				                5 NAML: ||
        #     11 CITY: MISSING				                6 NAMF: |VISTA |
        #     12 ST: MISSING				                7 NAMT: |CA|
        #     13 ZIP4: MISSING				                8 NAMS: |92084    |
        #     14 PHON: MISSING				                9 ADR1: |7603328398|
        #     15 FAX: MISSING				                10 ADR2: ||
        #     16 EMAIL: MISSING				                11 CITY: |readyforrena@gmail.com|

        columns = [
            'XREF_FILER_ID', 'FILER_ID', 'FILER_TYPE', 'STATUS',
            'EFFECT_DT', 'NAML', 'NAMF', 'NAMT', 'NAMS', 'ADR1',
            'ADR2', 'CITY', 'ST', 'ZIP4', 'PHON', 'FAX', 'EMAIL']
        lines = [
            ['', '', '', '', '', '', 'VISTA ', 'CA', '92084    ', '7603328398', '', 'readyforrena@gmail.com'],
            ['1449339', '1449339', 'RECIPIENT COMMITTEE', 'ACTIVE', '07/15/2022', 'MARROCCO FOR TRUSTEE 2022; RENA'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data'],
            ['data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data', 'data']
        ]
        expected = {
            'XREF_FILER_ID': '1449339',
            'FILER_ID': '1449339',
            'FILER_TYPE': 'RECIPIENT COMMITTEE',
            'STATUS': 'ACTIVE',
            'EFFECT_DT': '2022-07-15',
            'NAML': 'MARROCCO FOR TRUSTEE 2022; RENA',
            'NAMF': None,
            'NAMT': None,
            'NAMS': None,
            'ADR1': None,
            'ADR2': None,
            'CITY': 'VISTA ',
            'ST': 'CA',
            'ZIP4': '92084    ',
            'PHON': '7603328398',
            'FAX': None,
            'EMAIL': 'readyforrena@gmail.com'
        }

        result = imp.importable_lines('filername', columns, lines)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
