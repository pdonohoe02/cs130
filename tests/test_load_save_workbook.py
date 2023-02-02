import decimal
import unittest
import sheets
import json

class TestLoadSaveWorkbook(unittest.TestCase):
    '''
    This class contains the tests relating to loading and saving workbooks.
    '''
    def test_load_workbook(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "'123")
        wb.set_cell_contents(name2, 'a1', "'123")
        wb.set_cell_contents(name, 'b1', "5.3")
        wb.set_cell_contents(name2, 'b1', "5.3")
        wb.set_cell_contents(name, 'c1', "=a1*b1")
        wb.set_cell_contents(name2, 'c1', "=a1*b1")

        with open('tests/jsons/temp.json', 'r') as f:
            loaded_wb = wb.load_workbook(f)

        self.assertEqual(wb.sheets.keys(), loaded_wb.sheets.keys())
        self.assertEqual(wb.sheet_names, loaded_wb.sheet_names)
        self.assertEqual(wb.get_cell_value(name, 'a1'),
                         loaded_wb.get_cell_value(name, 'a1'))
        self.assertEqual(wb.get_cell_value(name2, 'a1'),
                         loaded_wb.get_cell_value(name2, 'a1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'),
                         loaded_wb.get_cell_value(name, 'b1'))
        self.assertEqual(wb.get_cell_value(name2, 'b1'),
                         loaded_wb.get_cell_value(name2, 'b1'))
        self.assertEqual(wb.get_cell_value(name, 'c1'),
                         loaded_wb.get_cell_value(name, 'c1'))
        self.assertEqual(wb.get_cell_value(name2, 'c1'),
                         loaded_wb.get_cell_value(name2, 'c1'))

        with open('tests/jsons/unparseable.json', 'r') as f:
            self.assertRaises(json.JSONDecodeError, wb.load_workbook, f)
        with open('tests/jsons/key_error.json', 'r') as f:
            self.assertRaises(KeyError, wb.load_workbook, f)
        with open('tests/jsons/type_error.json', 'r') as f:
            self.assertRaises(TypeError, wb.load_workbook, f)
        with open('tests/jsons/type_error2.json', 'r') as f:
            self.assertRaises(TypeError, wb.load_workbook, f)
        with open('tests/jsons/load_error.json', 'r') as f:
            self.assertRaises(ValueError, wb.load_workbook, f)

    def test_save_workbook(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', '=b1+c1')
        wb.set_cell_contents(name, 'b1', '=c1')
        wb.set_cell_contents(name, 'c1', '1')
        with open('tests/jsons/temp2.json', 'w') as f:
            wb.save_workbook(f)
        with open('tests/jsons/temp2.json', 'r') as f:
            temp2 = json.load(f)
        temp = {"sheets": [{"name": "Sheet1", "cell-contents":
               {"A1": "=b1+c1", "B1": "=c1", "C1": "1"}},
               {"name": "Sheet2", "cell-contents": {}}]}
        self.assertEqual(temp, temp2)
