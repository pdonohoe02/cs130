import decimal
import unittest
import sheets


class TestWorkbook(unittest.TestCase):
    def test_num_sheets(self):
        # Make a new empty workbook
        wb = sheets.Workbook()
        self.assertEqual(wb.num_sheets(), 0)
        (_, name1) = wb.new_sheet()
        self.assertEqual(wb.num_sheets(), 1)
        (_, name2) = wb.new_sheet()
        self.assertEqual(wb.num_sheets(), 2)
        wb.del_sheet(name2)
        self.assertEqual(wb.num_sheets(), 1)
        wb.del_sheet(name1)
        self.assertEqual(wb.num_sheets(), 0)
        (_, _) = wb.new_sheet()
        self.assertEqual(wb.num_sheets(), 1)
        
    
    def test_new_sheet(self):
        wb = sheets.Workbook()
        (_, _) = wb.new_sheet('Blank')
        self.assertRaises(ValueError, wb.new_sheet, 'blank')
        self.assertRaises(ValueError, wb.new_sheet, ' hello')
        self.assertRaises(ValueError, wb.new_sheet, 'hello ')
        self.assertRaises(ValueError, wb.new_sheet, '')
        self.assertRaises(ValueError, wb.new_sheet, "'")
        self.assertRaises(ValueError, wb.new_sheet, '"')

        (_, name1) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        (_, name3) = wb.new_sheet()
        self.assertEqual(name1, "Sheet1")
        self.assertEqual(name2, "Sheet2")
        self.assertEqual(name3, "Sheet3")
        wb.del_sheet(name3)
        (_, name4) = wb.new_sheet()
        self.assertEqual(name4, "Sheet3")


    def test_del_sheet(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.del_sheet(name.upper())
        self.assertEqual(wb.num_sheets(), 0)
        self.assertRaises(KeyError, wb.del_sheet, 'blank')


    def test_list_sheets(self):
        wb = sheets.Workbook()
        wb.new_sheet('Blank')
        wb.new_sheet()
        wb.new_sheet('hello Bye')
        wb.new_sheet()
        lst = wb.list_sheets()
        self.assertEqual(lst[0], 'Blank')
        self.assertEqual(lst[1], 'Sheet1')
        self.assertEqual(lst[2], 'hello Bye')
        self.assertEqual(lst[3], 'Sheet2')
        wb.del_sheet('Blank')
        lst = wb.list_sheets()
        self.assertEqual(lst[0], 'Sheet1')
        self.assertEqual(lst[1], 'hello Bye')
        self.assertEqual(lst[2], 'Sheet2')


    def test_sheet_extent(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (0, 0))
        wb.set_cell_contents(name, 'd14', 'green')
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (4, 14))
        wb.set_cell_contents(name, 'E14', 'green')
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (5, 14))
        wb.set_cell_contents(name, 'b34', 'green')
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (5, 34))
        wb.set_cell_contents(name, 'b34', '')
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (5, 14))
        wb.set_cell_contents(name, 'E14', None)
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (4, 14))
        wb.set_cell_contents(name, 'd14', '   ')
        self.assertEqual(wb.sheets[name.lower()].get_extent(), (0, 0))


    def test_is_cell_location_valid(self):
        wb = sheets.Workbook()
        self.assertTrue(wb.is_valid_cell_location('a15'))
        self.assertTrue(wb.is_valid_cell_location('A15'))
        self.assertTrue(wb.is_valid_cell_location('ZZZZ9999'))
        self.assertFalse(wb.is_valid_cell_location(' a15'))
        self.assertFalse(wb.is_valid_cell_location(' a15 '))
        self.assertFalse(wb.is_valid_cell_location(''))
        self.assertFalse(wb.is_valid_cell_location(' '))
        self.assertFalse(wb.is_valid_cell_location('SHEET1'))
        self.assertFalse(wb.is_valid_cell_location('0'))
        self.assertFalse(wb.is_valid_cell_location('!'))


    def test_get_and_set_cell_contents(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', '12')
        wb.set_cell_contents(name, 'b1', '34')
        wb.set_cell_contents(name, 'c1', '3.00')
        wb.set_cell_contents(name, 'd1', "'hello")
        wb.set_cell_contents(name, 'e1', "3*4")
        wb.set_cell_contents(name, 'f1', "=g1")
        wb.set_cell_contents(name, 'f2', "=g2+5")
        self.assertEqual(wb.get_cell_contents(name, 'a1'), '12')
        self.assertEqual(wb.get_cell_contents(name, 'b1'), '34')
        self.assertEqual(wb.get_cell_contents(name, 'c1'), '3.00')
        self.assertEqual(wb.get_cell_contents(name, 'd1'), "'hello")
        self.assertEqual(wb.get_cell_contents(name, 'e1'), '3*4')
        self.assertEqual(wb.get_cell_contents(name, 'f1'), '=g1')
        self.assertEqual(wb.get_cell_contents(name, 'g1'), None)
        self.assertEqual(wb.get_cell_contents(name, 'f2'), '=g2+5')

        wb.set_cell_contents(name, 'B1', '50')
        wb.set_cell_contents(name, 'c1', '=a1+b1')
        wb.set_cell_contents(name, 'd1', '')

        self.assertEqual(wb.get_cell_contents(name, 'a1'), '12')
        self.assertEqual(wb.get_cell_contents(name, 'b1'), '50')
        self.assertEqual(wb.get_cell_contents(name, 'c1'), '=a1+b1')
        self.assertEqual(wb.get_cell_contents(name, 'd1'), None)

        self.assertRaises(KeyError, wb.get_cell_contents, 'blank', 'a1')
        self.assertRaises(ValueError, wb.get_cell_contents, name, 'A')
        self.assertRaises(KeyError, wb.set_cell_contents, 'blank', 'a1', '10')
        self.assertRaises(ValueError, wb.set_cell_contents, name, 'A', '10')

        wb.set_cell_contents(name, 'e1', '#div/0!')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        self.assertEqual(wb.get_cell_contents(name, 'e1'), '#div/0!')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)

        wb.set_cell_contents(name, 'e1', '#circref!')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'e1', '#ERROR!')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'e1', '#ref!')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'e1', '#name?')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_NAME)

        wb.set_cell_contents(name, 'e1', '#value')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)


    def test_get_cell_value(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', '3.000')
        wb.set_cell_contents(name, 'a2', '3.14000')
        wb.set_cell_contents(name, 'a3', '3.1')
        wb.set_cell_contents(name, 'a4', '3.14159')
        wb.set_cell_contents(name, 'e1', "3*4")
        wb.set_cell_contents(name, 'a5', '=a4*100')
        wb.set_cell_contents(name, 'a6', '=a3*10')
        wb.set_cell_contents(name, 'a7', '=5.0*3.4')
        wb.set_cell_contents(name, 'f1', "=g1")
        wb.set_cell_contents(name, 'f2', "=g2+5")
        wb.set_cell_contents(name, 'f3', None)
        wb.set_cell_contents(name, 'f4', '')
        self.assertEqual(str(wb.get_cell_value(name, 'a1')), '3')
        self.assertEqual(str(wb.get_cell_value(name, 'a2')), '3.14')
        self.assertEqual(wb.get_cell_value(name, 'a3'), decimal.Decimal('3.1'))
        self.assertEqual(wb.get_cell_value(name, 'e1'), '3*4')
        self.assertEqual(wb.get_cell_value(name, 'a4'), decimal.Decimal('3.14159'))
        self.assertEqual(str(wb.get_cell_value(name, 'a5')), '314.159')
        self.assertEqual(str(wb.get_cell_value(name, 'a6')), '31')
        self.assertEqual(str(wb.get_cell_value(name, 'a7')), '17')
        self.assertEqual(wb.get_cell_value(name, 'f1'), decimal.Decimal('0'))
        self.assertEqual(wb.get_cell_value(name, 'f2'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'f3'), None)
        self.assertEqual(wb.get_cell_value(name, 'f4'), None)

        self.assertRaises(KeyError, wb.get_cell_value, 'blank', 'a1')
        self.assertRaises(ValueError, wb.get_cell_value, name, 'A')
    

    def test_calculate_contents(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a5', "    5")
        wb.set_cell_contents(name, 'a6', '5')
        wb.set_cell_contents(name, 'a7', '=a5+a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'a7'), decimal.Decimal('10'))

        wb.set_cell_contents(name, 'a5', "'    123")
        wb.set_cell_contents(name, 'a6', "5.3")
        wb.set_cell_contents(name, 'a7', '=a5*a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), '    123')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5.3'))
        self.assertEqual(wb.get_cell_value(name, 'a7'), 
                         decimal.Decimal('651.9'))
        
        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "'5.3")
        wb.set_cell_contents(name, 'a7', '=a5&a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), '5.3')
        self.assertEqual(wb.get_cell_value(name, 'a7'), 'hello5.3')

        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "5.3")
        wb.set_cell_contents(name, 'a7', '=a5&a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5.3'))
        self.assertEqual(wb.get_cell_value(name, 'a7'), 'hello5.3')

        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "bye")
        wb.set_cell_contents(name, 'a7', '=a5&a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), 'bye')
        self.assertEqual(wb.get_cell_value(name, 'a7'), 'hellobye')

        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "'   5.3")
        wb.set_cell_contents(name, 'a7', '=a5&a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), '   5.3')
        self.assertEqual(wb.get_cell_value(name, 'a7'), 'hello   5.3')

        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "=g1")
        wb.set_cell_contents(name, 'a7', '=a5&a6')
        wb.set_cell_contents(name, 'a8', '=a6&a5')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('0'))
        self.assertEqual(wb.get_cell_value(name, 'a7'), 'hello0')
        self.assertEqual(wb.get_cell_value(name, 'a8'), '0hello')

        wb.set_cell_contents(name, 'b1', "hello")
        wb.set_cell_contents(name, 'a2', "=b1&h1")
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a2'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'h1'), None)


    def test_type_error(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "5.3")
        wb.set_cell_contents(name, 'a7', '=a5+a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5.3'))
        value = wb.get_cell_value(name, 'a7')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)


    def test_parse_error(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=!/0")
        wb.set_cell_contents(name, 'a2', "5")
        wb.set_cell_contents(name, 'a7', '=a1')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)
        self.assertEqual(wb.get_cell_value(name, 'a2'), decimal.Decimal('5'))
        self.assertTrue(isinstance(value, sheets.CellError))
        value = wb.get_cell_value(name, 'a7')
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'a1', "=a&b")
        wb.set_cell_contents(name, 'a2', "='a'&'b'")
        wb.set_cell_contents(name, 'a3', '="a"&"b"')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)
        value = wb.get_cell_value(name, 'a3')
        self.assertEqual(value, 'ab')


    def test_div_by_zero_error(self):
        '''
        Tests the division by zero carry over error.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a2', "=15/0")
        wb.set_cell_contents(name, 'a1', "=a2+5")
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)

        
    def test_circ_ref_error(self):
        '''
        Tests the circular reference error and makes sure it is thrown.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=b1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'c1', '=b1/0')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        
        wb.del_sheet(name)
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=B1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'C1', '=b1/0')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        
        wb.del_sheet(name)
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=a2")
        wb.set_cell_contents(name, 'a2', "=a1+invalidsheet!a1")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.del_sheet(name)
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=#circref!")
        wb.set_cell_contents(name, 'a2', "=#ref!")
        wb.set_cell_contents(name, 'a3', "=a1+a2")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)
        value = wb.get_cell_value(name, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)


    def test_update_workbook(self):
        wb = sheets.Workbook()
        (_, name1) = wb.new_sheet()
        wb.set_cell_contents(name1, 'a1', "=#circref!")
        wb.set_cell_contents(name1, 'a2', "5")
        wb.set_cell_contents(name1, 'a3', "=a1+a2")
        value = wb.get_cell_value(name1, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name1, 'a2')
        self.assertEqual(value, 5)
        value = wb.get_cell_value(name1, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        # resetting a1
        wb.set_cell_contents(name1, 'a1', '5')
        value = wb.get_cell_value(name1, 'a3')
        self.assertEqual(value, decimal.Decimal('10'))

        (_, name2) = wb.new_sheet()
        wb.set_cell_contents(name2, 'a1', f"={name1}!a1")
        value = wb.get_cell_value(name2, 'a1')
        self.assertEqual(value, decimal.Decimal('5'))
        wb.del_sheet(name1)
        value = wb.get_cell_value(name2, 'a1')
        #print(wb.sheets[name2.lower()].cells)
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

    
    def test_smoke_test(self):
        '''
        Initial smoke test for the sheets module to make sure everything is
        running smoothly.
        '''
        # Should print the version number of your sheets library,
        # which should be 1.0 for the first project.
        # print(f'Using sheets engine version {sheets.version}')

        # Make a new empty workbook
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()

        # Should print:  New spreadsheet "Sheet1" at index 0
        # print(f'New spreadsheet "{name}" at index {index}')

        wb.set_cell_contents(name, 'a1', '12')
        wb.set_cell_contents(name, 'b1', '34')
        wb.set_cell_contents(name, 'c1', '=a1+b1')

        # value should be a decimal.Decimal('46')
        value = wb.get_cell_value(name, 'c1')
        self.assertEqual(value, decimal.Decimal('46'))

        # Should print:  c1 = 46
        # print(f'c1 = {value}')

        wb.set_cell_contents(name, 'd3', '=nonexistent!b4')

        # value should be a CellError with type BAD_REFERENCE
        value = wb.get_cell_value(name, 'd3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # Cells can be set to error values as well
        wb.set_cell_contents(name, 'e1', '#div/0!')
        wb.set_cell_contents(name, 'e2', '=e1+5')
        value = wb.get_cell_value(name, 'e2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)
    

if __name__ == '__main__':
    unittest.main()
