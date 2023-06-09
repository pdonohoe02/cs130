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
        expected = [name2.lower(),
                    name3.lower(),
                    name4.lower(),
                    name1.lower()]
        names = [name2.lower(),
                 name3.lower(),
                 name4.lower(),
                 name1.lower()]
        self.assertEqual(list(wb.sheets.keys()), expected)
        self.assertEqual(list(wb.sheet_names.keys()), names)

        wb.move_sheet(name1.upper(), 0)
        expected = [name1.lower(),
                    name2.lower(),
                    name3.lower(),
                    name4.lower()]
        names = {name1.lower(): name1,
                 name2.lower(): name2,
                 name3.lower(): name3,
                 name4.lower(): name4}
        self.assertEqual(list(wb.sheets.keys()), expected)
        self.assertEqual(list(wb.sheet_names.keys()), list(names.keys()))

        wb.move_sheet(name4, 0)
        expected = {name4.lower(): wb.sheets[name4.lower()],
                    name1.lower(): wb.sheets[name1.lower()],
                    name2.lower(): wb.sheets[name2.lower()],
                    name3.lower(): wb.sheets[name3.lower()]}
        names = {name4.lower(): name4,
                 name1.lower(): name1,
                 name2.lower(): name2,
                 name3.lower(): name3}
        self.assertEqual(list(wb.sheets.keys()), list(expected.keys()))
        self.assertEqual(list(wb.sheet_names.keys()), list(names.keys()))

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
        self.assertEqual(list(wb.sheets.keys()), list(expected.keys()))
        self.assertEqual(list(wb.sheet_names.keys()), list(names.keys()))

        wb.move_sheet(name4, 1)
        expected = {name1.lower(): wb.sheets[name1.lower()],
                    name4.lower(): wb.sheets[name4.lower()],
                    name2.lower(): wb.sheets[name2.lower()],
                    name3.lower(): wb.sheets[name3.lower()],
                    name5.lower(): wb.sheets[name5.lower()]}
        names = {name1.lower(): name1,
                 name4.lower(): name4,
                 name2.lower(): name2,
                 name3.lower(): name3,
                 name5.lower(): name5}
        self.assertEqual(list(wb.sheets.keys()), list(expected.keys()))
        self.assertEqual(list(wb.sheet_names.keys()), list(names.keys()))

    def test_move_many_sheet(self):
        for i in range(1, 5):
            for j in range(5):
                wb = sheets.Workbook()
                (_, name1) = wb.new_sheet()
                (_, name2) = wb.new_sheet()
                (_, name3) = wb.new_sheet()
                (_, name4) = wb.new_sheet()
                (_, name5) = wb.new_sheet()

                expected = [name1.lower(),
                            name2.lower(),
                            name3.lower(),
                            name4.lower(),
                            name5.lower()]
                wb.move_sheet(f'sheet{i}', j)
                expected.remove(f'sheet{i}')
                expected.insert(j, f'sheet{i}')
                self.assertEqual(list(wb.sheets.keys()), expected)
                self.assertEqual(list(wb.sheet_names.keys()), expected)

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
    
    def test_copy_sheet_cell_errors(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        self.assertRaises(KeyError, wb.copy_sheet, 'unknown')
        wb.set_cell_contents(name, 'a1', "=a2")
        wb.set_cell_contents(name, 'a2', "=a3")
        wb.set_cell_contents(name, 'a3', '=a1')
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

    def test_copy_sheet_more_cell_errors(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=a2")
        wb.set_cell_contents(name, 'a2', "=#name?")
        wb.set_cell_contents(name, 'a3', '=#div/0!')
        wb.set_cell_contents(name, 'a4', '=a5')
        wb.set_cell_contents(name, 'a5', '=a4')
        wb.set_cell_contents(name, 'a6', '=!/0')
        wb.set_cell_contents(name, 'a7', '=Sheet1_1!a1')
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
        value = wb.get_cell_value(name2, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_NAME)
        value = wb.get_cell_value(name2, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_NAME)
        value = wb.get_cell_value(name2, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)
        value = wb.get_cell_value(name2, 'a4')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name2, 'a5')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name2, 'a6')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)
        value = wb.get_cell_value(name2, 'a7')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_NAME)

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

        self.assertRaises(KeyError, wb.rename_sheet, 'unknown', 'new_sheet')
        self.assertRaises(ValueError, wb.rename_sheet, name2, '  hello')
        wb.rename_sheet(name2.upper(), 'new_sheet')
        name2 = 'new_sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower(), name3.lower()])
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

    def test_rename_quotes(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "='Sheet1'!A5 + 'Sheet2'!A6")
        wb.set_cell_contents(name, 'a5', "5")
        wb.set_cell_contents(name2, 'a6', "20")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(25))
        self.assertEqual(wb.get_cell_value(name, 'a5'), decimal.Decimal(5))
        self.assertEqual(wb.get_cell_value(name2, 'a6'), decimal.Decimal(20))

        wb.rename_sheet(name2.upper(), 'Sheet3')
        name2 = 'Sheet3'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(
            wb.get_cell_contents(
                name,
                'a1'),
            "=Sheet1!A5 + Sheet3!A6")

        wb.rename_sheet(name2.upper(), 'new sheet')
        name2 = 'new sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(
            wb.get_cell_contents(
                name,
                'a1'),
            "=Sheet1!A5 + 'new sheet'!A6")

        # old sheet required quotes, renaming to a name that does not need
        # quotes
        wb.rename_sheet(name2.upper(), 'SheetBla')
        name2 = 'SheetBla'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(
            wb.get_cell_contents(
                name,
                'a1'),
            "=Sheet1!A5 + SheetBla!A6")
        self.assertEqual(wb.get_cell_contents(name, 'a5'), '5')
        self.assertEqual(wb.get_cell_contents(name2, 'a6'), '20')

        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(25))
        self.assertEqual(wb.get_cell_value(name, 'a5'), decimal.Decimal(5))
        self.assertEqual(wb.get_cell_value(name2, 'a6'), decimal.Decimal(20))

        wb.rename_sheet(name2.upper(), '3sheet')
        name2 = '3sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(
            wb.get_cell_contents(name, 'a1'), "=Sheet1!A5 + '3sheet'!A6")

        wb.rename_sheet(name2.upper(), '_sheet')
        name2 = '_sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "=Sheet1!A5 + _sheet!A6")

        # old sheet name did not need quotes, updating to name that needs
        # quotes
        wb.rename_sheet(name2.upper(), 'new*sheet')
        name2 = 'new*sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "=Sheet1!A5 + 'new*sheet'!A6")

        wb.rename_sheet(name, 'new sheet')
        name = 'new sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "='new sheet'!A5 + 'new*sheet'!A6")

        wb.rename_sheet(name, 'temp')
        name = 'temp'
        self.assertEqual(list(wb.sheet_names.keys()), [name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "=temp!A5 + 'new*sheet'!A6")

    def test_rename_update(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', f'=b1 + {name2}!c1')
        wb.set_cell_contents(name, 'b1', f'={name2}!c1')
        wb.set_cell_contents(name2, 'c1', f'={name}!d1 + {name2}!e1')
        wb.set_cell_contents(name, 'd1', '1')
        wb.set_cell_contents(name2, 'e1', '3')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(8))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(3))

        wb.rename_sheet(name2.upper(), '_sheet')
        name2 = '_sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "=b1 + _sheet!c1")
        self.assertEqual(wb.get_cell_contents(name, 'b1'), "=_sheet!c1")
        self.assertEqual(wb.get_cell_contents(name2, 'c1'), "=Sheet1!d1 + _sheet!e1")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(8))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(3))

        wb.rename_sheet(name2.upper(), 'new*sheet')
        name2 = 'new*sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "=b1 + 'new*sheet'!c1")
        self.assertEqual(wb.get_cell_contents(name, 'b1'), "='new*sheet'!c1")
        self.assertEqual(wb.get_cell_contents(name2, 'c1'), "=Sheet1!d1 + 'new*sheet'!e1")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(8))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(3))

        wb.rename_sheet(name, 'new sheet')
        name = 'new sheet'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(wb.get_cell_contents(name, 'a1'), "=b1 + 'new*sheet'!c1")
        self.assertEqual(wb.get_cell_contents(name, 'b1'), "='new*sheet'!c1")
        self.assertEqual(wb.get_cell_contents(name2, 'c1'), "='new sheet'!d1 + 'new*sheet'!e1")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(8))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(3))

        wb.rename_sheet(name, 'temp')
        name = 'temp'
        self.assertEqual(list(wb.sheet_names.keys()), [
                         name.lower(), name2.lower()])
        self.assertEqual(
            wb.get_cell_contents(
                name,
                'a1'),
            "=b1 + 'new*sheet'!c1")
        self.assertEqual(wb.get_cell_contents(name, 'b1'), "='new*sheet'!c1")
        self.assertEqual(wb.get_cell_contents(name2, 'c1'), "=temp!d1 + 'new*sheet'!e1")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(8))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(4))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(3))

        wb.set_cell_contents(name2, 'e1', '10')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(22))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(11))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(11))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(10))

        wb.set_cell_contents(name2, 'e1', '15')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(32))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(16))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(16))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(1))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(15))

        wb.set_cell_contents(name, 'd1', '10')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal(50))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal(25))
        self.assertEqual(wb.get_cell_value(name2, 'c1'), decimal.Decimal(25))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal(10))
        self.assertEqual(wb.get_cell_value(name2, 'e1'), decimal.Decimal(15))

    # def test_many_move_sheets(self):
    #     '''
    #     Test that one call to Workbook.reorder_sheets results in the correct
    #     order.
    #     '''
    #     wb = sheets.Workbook()
    #     (_, name1) = wb.new_sheet()
    #     (_, name2) = wb.new_sheet()
    #     (_, name3) = wb.new_sheet()
    #     (_, name4) = wb.new_sheet()
    #     self.assertRaises(IndexError, wb.move_sheet, name1, 4)
    #     self.assertRaises(IndexError, wb.move_sheet, name1, -1)
    #     self.assertRaises(KeyError, wb.move_sheet, 'unknown', 4)
    #     wb.move_sheet(name1, 3)
    #     expected = {name2.lower(): wb.sheets[name2.lower()],
    #                 name3.lower(): wb.sheets[name3.lower()],
    #                 name1.lower(): wb.sheets[name1.lower()],
    #                 name4.lower(): wb.sheets[name4.lower()]}
    #     names = {name2.lower(): name2,
    #              name3.lower(): name3,
    #              name1.lower(): name1,
    #              name4.lower(): name4}
    #     self.assertEqual(wb.sheets, expected)
    #     self.assertEqual(wb.sheet_names, names)

    #     wb.move_sheet(name1.upper(), 0)
    #     expected = {name1.lower(): wb.sheets[name1.lower()],
    #                 name2.lower(): wb.sheets[name2.lower()],
    #                 name3.lower(): wb.sheets[name3.lower()],
    #                 name4.lower(): wb.sheets[name4.lower()]}
    #     names = {name1.lower(): name1,
    #              name2.lower(): name2,
    #              name3.lower(): name3,
    #              name4.lower(): name4}
    #     self.assertEqual(wb.sheets, expected)
    #     self.assertEqual(wb.sheet_names, names)

    #     wb.move_sheet(name4, 0)
    #     expected = {name4.lower(): wb.sheets[name4.lower()],
    #                 name1.lower(): wb.sheets[name1.lower()],
    #                 name2.lower(): wb.sheets[name2.lower()],
    #                 name3.lower(): wb.sheets[name3.lower()]}
    #     names = {name4.lower(): name4,
    #              name1.lower(): name1,
    #              name2.lower(): name2,
    #              name3.lower(): name3}
    #     self.assertEqual(wb.sheets, expected)
    #     self.assertEqual(wb.sheet_names, names)

    #     (_, name5) = wb.new_sheet()
    #     expected = {name4.lower(): wb.sheets[name4.lower()],
    #                 name1.lower(): wb.sheets[name1.lower()],
    #                 name2.lower(): wb.sheets[name2.lower()],
    #                 name3.lower(): wb.sheets[name3.lower()],
    #                 name5.lower(): wb.sheets[name5.lower()]}
    #     names = {name4.lower(): name4,
    #              name1.lower(): name1,
    #              name2.lower(): name2,
    #              name3.lower(): name3,
    #              name5.lower(): name5}
    #     self.assertEqual(wb.sheets, expected)
    #     self.assertEqual(wb.sheet_names, names)

if __name__ == '__main__':
    unittest.main()
