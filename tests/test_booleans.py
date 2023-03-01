import unittest
import decimal
import sheets

class TestBooleans(unittest.TestCase):
    def test_boolean_literals(self):
        wb = sheets.Workbook()
        wb.new_sheet()
        wb.set_cell_contents('Sheet1', 'A1', 'true')
        assert isinstance(wb.get_cell_value('Sheet1', 'A1'), bool)
        assert wb.get_cell_value('Sheet1', 'A1')

        wb.set_cell_contents('Sheet1', 'A2', '=FaLsE')
        assert isinstance(wb.get_cell_value('Sheet1', 'A2'), bool)
        assert not wb.get_cell_value('Sheet1', 'A2')

    def test_number_comparisons(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '3')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('3'))
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        # testing w/decimals
        wb.set_cell_contents(name, 'A1', '1.0001')
        wb.set_cell_contents(name, 'b1', '1.0001')
        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

    def test_string_comparisons(self):
        # test strings
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', 'BLUE')
        wb.set_cell_contents(name, 'b1', 'blue')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'c1'), True)

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertEqual(wb.get_cell_value(name, 'c1'), True)

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertEqual(wb.get_cell_value(name, 'c1'), False)

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertEqual(wb.get_cell_value(name, 'c1'), False)

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertEqual(wb.get_cell_value(name, 'c1'), False)

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'A1', 'a')
        wb.set_cell_contents(name, 'b1', '[')
        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

    def test_bool_comparisons(self):
        # test bool
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', 'false')
        wb.set_cell_contents(name, 'b1', 'true')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), False)
        self.assertEqual(wb.get_cell_value(name, 'b1'), True)
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'A1', '=faLSE')
        wb.set_cell_contents(name, 'b1', '=tRUE')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), False)
        self.assertEqual(wb.get_cell_value(name, 'b1'), True)
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

    def test_diff_type_comparisons(self):
        # test diff types
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', "'12")
        wb.set_cell_contents(name, 'b1', '12')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), '12')
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('12'))
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        # test bool w/strings
        wb.set_cell_contents(name, 'A1', "'true")
        wb.set_cell_contents(name, 'b1', '=false')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), "true")
        self.assertEqual(wb.get_cell_value(name, 'b1'), False)
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        # test bool w/numbers
        wb.set_cell_contents(name, 'A1', "false")
        wb.set_cell_contents(name, 'b1', '5')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), False)
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('5'))
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

    def test_empty_comparisons(self):
        # test empty cells with default 0
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), None)
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        # test empty cells with default ""
        wb.set_cell_contents(name, 'A1', 'a')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), 'a')
        self.assertEqual(wb.get_cell_value(name, 'b1'), None)
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        # test empty cells with default bool
        wb.set_cell_contents(name, 'A1', 'true')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), True)
        self.assertEqual(wb.get_cell_value(name, 'b1'), None)
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        # test both cells empty
        wb.set_cell_contents(name, 'A1', None)
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), None)
        self.assertEqual(wb.get_cell_value(name, 'b1'), None)
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1!=b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

    def test_error_comparisons(self):
        # test error propagation 
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '#REF!')
        wb.set_cell_contents(name, 'b1', '3')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test actual error
        wb.set_cell_contents(name, 'A1', '=hello!a1')
        wb.set_cell_contents(name, 'b1', '3')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test error order of operations
        wb.set_cell_contents(name, 'A1', '=#circref!')
        wb.set_cell_contents(name, 'b1', '#error!')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'A1', '=#circref!')
        wb.set_cell_contents(name, 'b1', '#div/0!')
        wb.set_cell_contents(name, 'c1', '=a1=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1==b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1>b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1>=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'c1', '=a1<=b1')
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_comparisons_precedence(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'c1', '=a1 = b1 & d1')
        wb.set_cell_contents(name, 'b1', '3')
        wb.set_cell_contents(name, 'd1', "  type")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('3'))
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 == b1 & d1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 != b1 & d1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 <> b1 & d1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 > b1 & d1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 >= b1 & d1')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 < b1 & d1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

        wb.set_cell_contents(name, 'c1', '=a1 <= b1 & d1')
        self.assertTrue(wb.get_cell_value(name, 'c1'))

    def test_multiple_comparisons(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()

        # wb.set_cell_contents(name, 'a4', '=3 - 6*5')
        # wb.set_cell_contents(name, )
        for _ in range(1000):
            wb.set_cell_contents(name, 'A1', '1')
            wb.set_cell_contents(name, 'b1', '2')
            wb.set_cell_contents(name, 'c1', "3")
            wb.set_cell_contents(name, 'd1', '=a1 < b1 < c1')
            self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
            self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('2'))
            self.assertEqual(wb.get_cell_value(name, 'c1'), decimal.Decimal('3'))
            self.assertFalse(wb.get_cell_value(name, 'd1'))


        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'd1', '=AND(A1 < B1, B1 < C1)')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('2'))
        self.assertTrue(wb.get_cell_value(name, 'd1'))

    def test_comparisons_functions(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'c1', '= FALSE == AND(TRUE, TRUE)')
        self.assertFalse(wb.get_cell_value(name, 'c1'))

    def test_boolean_type_conversions(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()

        # testing true -> 1, false -> 0
        wb.set_cell_contents(name, 'A1', 'true')
        wb.set_cell_contents(name, 'c1', '=a1+2')
        self.assertEqual(wb.get_cell_value(name, 'a1'), True)
        self.assertEqual(wb.get_cell_value(name, 'c1'), decimal.Decimal('3'))
        wb.set_cell_contents(name, 'A1', 'false')
        wb.set_cell_contents(name, 'c1', '=a1+2')
        self.assertEqual(wb.get_cell_value(name, 'a1'), False)
        self.assertEqual(wb.get_cell_value(name, 'c1'), decimal.Decimal('2'))

        # testing true -> 'TRUE', false -> 'FALSE'
        wb.set_cell_contents(name, 'A1', 'true')
        wb.set_cell_contents(name, 'c1', '=a1&2')
        self.assertEqual(wb.get_cell_value(name, 'a1'), True)
        self.assertEqual(wb.get_cell_value(name, 'c1'), 'TRUE2')
        wb.set_cell_contents(name, 'A1', 'false')
        wb.set_cell_contents(name, 'c1', '=a1&2')
        self.assertEqual(wb.get_cell_value(name, 'a1'), False)
        self.assertEqual(wb.get_cell_value(name, 'c1'), 'FALSE2')

if __name__ == '__main__':
    unittest.main()
