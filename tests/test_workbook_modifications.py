import decimal
import unittest
import sheets


class TestWorkbookModifications(unittest.TestCase):
    '''
    This class contains the tests relating to the workbook manipulation
    functionalities corresponding to Project 2.
    '''
    def test_move_sheet(self):
        wb = sheets.Workbook()
        (_, name1) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        (_, name3) = wb.new_sheet()
        (_, name4) = wb.new_sheet()
        self.assertRaises(IndexError, wb.move_sheet, name1, 4)
        self.assertRaises(IndexError, wb.move_sheet, name1, -1)
        self.assertRaises(KeyError, wb.move_sheet, 'unknown', 4)
        wb.move_sheet(name1, 3)
        expected = {name2.lower(): wb.sheets[name2.lower()],
                    name3.lower(): wb.sheets[name3.lower()],
                    name1.lower(): wb.sheets[name1.lower()],
                    name4.lower(): wb.sheets[name4.lower()]}
        names = {name2.lower(): name2,
                 name3.lower(): name3,
                 name1.lower(): name1,
                 name4.lower(): name4}
        self.assertEqual(wb.sheets, expected)
        self.assertEqual(wb.sheet_names, names)

        wb.move_sheet(name1.upper(), 0)
        expected = {name1.lower(): wb.sheets[name1.lower()],
                    name2.lower(): wb.sheets[name2.lower()],
                    name3.lower(): wb.sheets[name3.lower()],   
                    name4.lower(): wb.sheets[name4.lower()]}
        names = {name1.lower(): name1,
                 name2.lower(): name2,
                 name3.lower(): name3,   
                 name4.lower(): name4}
        self.assertEqual(wb.sheets, expected)
        self.assertEqual(wb.sheet_names, names)

        wb.move_sheet(name4, 0)
        expected = {name4.lower(): wb.sheets[name4.lower()],
                    name1.lower(): wb.sheets[name1.lower()],
                    name2.lower(): wb.sheets[name2.lower()],
                    name3.lower(): wb.sheets[name3.lower()]}
        names = {name4.lower(): name4,
                 name1.lower(): name1,
                 name2.lower(): name2,
                 name3.lower(): name3}
        self.assertEqual(wb.sheets, expected)
        self.assertEqual(wb.sheet_names, names)

        (_, name5) = wb.new_sheet()
        expected = {name4.lower(): wb.sheets[name4.lower()],
                    name1.lower(): wb.sheets[name1.lower()],
                    name2.lower(): wb.sheets[name2.lower()],
                    name3.lower(): wb.sheets[name3.lower()],
                    name5.lower(): wb.sheets[name5.lower()]}
        names = {name4.lower(): name4,
                 name1.lower(): name1,
                 name2.lower(): name2,
                 name3.lower(): name3,
                 name5.lower(): name5}
        self.assertEqual(wb.sheets, expected)
        self.assertEqual(wb.sheet_names, names)
        