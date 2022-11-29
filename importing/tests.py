import unittest

import importer as imp


class ImportTests(unittest.TestCase):

    # fix_parts(target, head, parts):

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


if __name__ == '__main__':
    unittest.main()
