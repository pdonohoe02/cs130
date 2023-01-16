import decimal
import unittest
import sheets


class TestWorkbook(unittest.TestCase):
    def test_is_cell_location_valid(self):
        # Make a new empty workbook
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

    def test_set_cell_contents(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', '12')
        wb.set_cell_contents(name, 'b1', '34')
        self.assertEqual(wb.get_cell_contents(name, 'b1'), '34')

        wb.set_cell_contents(name, 'B1', '50')
        wb.set_cell_contents(name, 'c1', '=a1+b1')
        wb.set_cell_contents(name, 'd1', '')

        self.assertEqual(wb.get_cell_contents(name, 'a1'), '12')
        self.assertEqual(wb.get_cell_contents(name, 'b1'), '50')
        self.assertEqual(wb.get_cell_contents(name, 'c1'), '=a1+b1')
        self.assertEqual(wb.get_cell_contents(name, 'd1'), None)

        self.assertRaises(KeyError, wb.set_cell_contents, 'blank', 'a1', '10')
        self.assertRaises(ValueError, wb.set_cell_contents, name, 'A', '10')

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

    def test_calculate_contents(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()

        wb.set_cell_contents(name, 'a5', "    5")
        wb.set_cell_contents(name, 'a6', '5')
        wb.set_cell_contents(name, 'a7', '=a5+a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5'))
        print(type(wb.get_cell_value(name, 'a5')))
        self.assertEqual(wb.get_cell_value(name, 'a7'), decimal.Decimal('10'))

        wb.set_cell_contents(name, 'a5', "'    123")
        wb.set_cell_contents(name, 'a6', "5.3")
        wb.set_cell_contents(name, 'a7', '=a5*a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), '    123')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5.3'))
        self.assertEqual(
            wb.get_cell_value(
                name,
                'a7'),
            decimal.Decimal('651.9'))

        # type error
        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "5.3")
        wb.set_cell_contents(name, 'a7', '=a5+a6')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5.3'))
        value = wb.get_cell_value(name, 'a7')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

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

        # # type error
        # wb.set_cell_contents(name, 'a1', "abc")
        # wb.set_cell_contents(name, 'a2', "5")
        # wb.set_cell_contents(name, 'a7', '=a1+a2')
        # print(wb.get_cell_value(name, 'a7'))

        # parse error
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

        # division by zero carry over error
        wb.set_cell_contents(name, 'a2', "=15/0")
        wb.set_cell_contents(name, 'a1', "=a2+5")
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.DIVIDE_BY_ZERO)

        # circref error
        # TODO

    def test_smoke_test(self):
        # Should print the version number of your sheets library,
        # which should be 1.0 for the first project.
        print(f'Using sheets engine version {sheets.version}')

        # Make a new empty workbook
        wb = sheets.Workbook()
        (index, name) = wb.new_sheet()

        # Should print:  New spreadsheet "Sheet1" at index 0
        print(f'New spreadsheet "{name}" at index {index}')

        wb.set_cell_contents(name, 'a1', '12')
        wb.set_cell_contents(name, 'b1', '34')
        wb.set_cell_contents(name, 'c1', '=a1+b1')

        # value should be a decimal.Decimal('46')
        value = wb.get_cell_value(name, 'c1')
        self.assertEqual(value, decimal.Decimal('46'))

        # Should print:  c1 = 46
        print(f'c1 = {value}')

        wb.set_cell_contents(name, 'd3', '=nonexistent!b4')

        # value should be a CellError with type BAD_REFERENCE
        value = wb.get_cell_value(name, 'd3')
        #print(value)
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
