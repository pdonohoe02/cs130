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

    def test_copy_sheet(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        self.assertRaises(KeyError, wb.copy_sheet, 'unknown')
        wb.set_cell_contents(name, 'a1', "=5+4")
        wb.set_cell_contents(name, 'a2', "=a3")
        wb.set_cell_contents(name, 'a3', '=a4+a5')
        wb.set_cell_contents(name, 'a4', '=a1*10')
        wb.set_cell_contents(name, 'a5', '=a3')
        wb.set_cell_contents(name, 'a6', "=sheet1_1_1!a1")
        wb.set_cell_contents(name, 'a7', '=a8')
        wb.set_cell_contents(name, 'a8', '=a9')
        wb.set_cell_contents(name, 'a9', '=a7')
        wb.set_cell_contents(name, 'a10', "=a1+a4")
        (_, name2) = wb.copy_sheet(name)
        self.assertEqual(name2, "Sheet1_1")
        sheet1 = wb.sheets[name.lower()]
        sheet2 = wb.sheets[name2.lower()]
        for cell1, cell2 in zip(sheet1.cells.keys(), sheet2.cells.keys()):
            self.assertEqual(sheet1.get_cell_contents(cell1),
                             sheet2.get_cell_contents(cell2))
        for cell1, cell2 in zip(sheet1.cells.keys(), sheet2.cells.keys()):
            value1 = sheet1.get_cell_value(cell1)
            value2 = sheet2.get_cell_value(cell2)
            if isinstance(value1, sheets.CellError):
                self.assertTrue(isinstance(value1, sheets.CellError))
                self.assertEqual(value1.get_type(), value2.get_type())
            else:
                self.assertEqual(value1, value2)
        (_, name3) = wb.copy_sheet(name.upper())
        self.assertEqual(name3, "Sheet1_2")
        wb.del_sheet(name2)
        (_, name4) = wb.copy_sheet(name)
        self.assertEqual(name4, "Sheet1_1")
        value = wb.get_cell_value(name4, 'a6')
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)
        (i, name5) = wb.copy_sheet(name4)
        self.assertEqual(name5, "Sheet1_1_1")
        self.assertEqual(i, 3)
        self.assertEqual(wb.get_cell_value(name5, 'a6'), decimal.Decimal(9))

    def test_formulas(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.new_sheet('other totals')
        wb.set_cell_contents(name, 'a1', "='other totals'!g15")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(0))

    def test_rename_sheet(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        (_, name3) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', f'=b1+{name2}!c1')
        wb.set_cell_contents(name, 'b1', f'={name3}!d1')
        wb.set_cell_contents(name2, 'c1', f'={name3}!d1')
        wb.set_cell_contents(name3, 'd1', "6")
        wb.set_cell_contents(name3, 'e1', f'={name2}!f1')
        wb.set_cell_contents(name2, 'f1', '=g1')
        wb.set_cell_contents(name, 'g1', '5')
        wb.set_cell_contents(name, 'h1', '=new_sheet!a1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(12))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(6))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(6))
        self.assertEqual(wb.get_cell_value(name3, 'd1'), decimal.Decimal(6))
        self.assertEqual(wb.get_cell_value(name3, 'e1'), decimal.Decimal(0))
        self.assertEqual(wb.get_cell_value(name2, 'f1'), decimal.Decimal(0))
        self.assertEqual(wb.get_cell_value(name, 'g1'), decimal.Decimal(5))
        value = wb.get_cell_value(name, 'h1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.rename_sheet(name2, 'new_sheet')
        name2 = 'new_sheet'
        self.assertEqual(list(wb.sheet_names.keys()),[name.lower(), name2.lower(), name3.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), '=b1+new_sheet!c1')
        self.assertEqual(wb.get_cell_contents(name, 'b1'), '=Sheet3!d1')
        self.assertEqual(wb.get_cell_contents(name2, 'c1'), '=Sheet3!d1')
        self.assertEqual(wb.get_cell_contents(name3, 'd1'), '6')
        self.assertEqual(wb.get_cell_contents(name3, 'e1'), '=new_sheet!f1')
        self.assertEqual(wb.get_cell_contents(name2, 'f1'), '=g1')
        self.assertEqual(wb.get_cell_contents(name, 'g1'), '5')
        self.assertEqual(wb.get_cell_contents(name, 'h1'), '=new_sheet!a1')

        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(12))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(6))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(6))
        self.assertEqual(wb.get_cell_value(name3, 'd1'), decimal.Decimal(6))
        self.assertEqual(wb.get_cell_value(name3, 'e1'), decimal.Decimal(0))
        self.assertEqual(wb.get_cell_value(name2, 'f1'), decimal.Decimal(0))
        self.assertEqual(wb.get_cell_value(name, 'g1'), decimal.Decimal(5))
        # h1's value needs to be recalculated
        self.assertEqual(wb.get_cell_value(name, 'h1'), decimal.Decimal(0))
