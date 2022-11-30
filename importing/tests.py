import unittest

import common
import importer as imp


class ImportTests(unittest.TestCase):

    def test_naml_fix(self):
        target = "cvr"
        head = ['AAA', 'BBB', 'CCC', 'DDD']
        good_row = ['zero', 'one', 'two', 'three']
        bad_row = ['zero', 'one', '', 'three', 'four']
        fixed_row = ['zero', 'one', 'three', 'four']

        result = imp.fix_empty_naml(target, target, head, good_row, 2)
        self.assertEqual(good_row, result)

        result = imp.fix_empty_naml(target, target, head, bad_row, 2)
        self.assertEqual(fixed_row, result)

    def test_column_definitions(self):
        bm = common.table_columns()['ballot_measures']
        self.assertTrue('election_date' in list(bm.keys())[0])
        self.assertEqual(6, len(bm.keys()))

    def _test_fix_broken_lines_NAMES(self):
        # line 307138: ['1347670', 'CALIFORNIA CORRECTIONAL PEACE OFFICERS
        #     ASSOCIATION TRUTH IN AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)']
        #     parts # 2
        # line 307139: ['', '', '', '', '', '', '', '',
        #     'CALIFORNIA CORRECTIONAL PEACE OFFICERS ASSOCIATION TRUTH IN
        #     AMERICAN GOVERNMENT FUND(CCPOA TAG FUND)']
        #     parts # 9
        #
        # NAMES has columns:
        #     NAMID   NAML    NAMF    NAMT    NAMS    MONIKER    MONIKER_POS
        #     NAMM    FULLNAME        NAML_SEARCH
        #     parts # 10
        #
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

        result = imp.importable_lines(None, 'filername', columns, lines)

        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
