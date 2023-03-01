import unittest
import decimal
import sheets

class TestFunctions(unittest.TestCase):
    # TODO: TEST ERROR PROPAGATION 
    def test_and_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'd1', '=AND(A1 < B1, B1 < C1)')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('2'))
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=AND (A1 < B1, B1 < C1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=AND (1, 0)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=AND(0, 0)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=AND(1, 1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        # testing with false
        wb.set_cell_contents(name, 'd1', '=AND(B1 < A1, B1 < C1)')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('2'))
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=AND (B1 < A1, B1 < C1)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=AND(true, true, false)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), False)

        wb.set_cell_contents(name, 'd1', '=AND()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'b1', 'hello')
        wb.set_cell_contents(name, 'd1', '=AND(A1, B1)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=AND(A1, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=AND(#CIRCREF!, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_or_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        wb.set_cell_contents(name, 'd1', '=OR(A1 < B1, B1 < C1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=OR(A1 < B1, C1 < B1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=OR (A1 < B1, B1 < C1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=OR (B1 < A1, C1 < B1)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=OR(B1 < A1, C1 < B1)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=OR(false, false)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=OR(true, true)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=OR(false, false, true)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=OR()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'b1', 'hello')
        wb.set_cell_contents(name, 'd1', '=OR(A1, B1)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=OR(A1, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=OR(#CIRCREF!, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_not_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'd1', '=NOT(A1 < B1)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=NOT(A1 > B1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=NOT(false)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=NOT(true)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=NOT(true, false)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'b1', 'hello')
        wb.set_cell_contents(name, 'd1', '=NOT(A1, B1)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=NOT(A1, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=NOT(#CIRCREF!, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=NOT()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

    def test_xor_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        wb.set_cell_contents(name, 'd1', '=XOR(A1 < B1, B1 < C1)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(A1 > B1, B1 > C1)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(A1 < B1, B1 > C1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(A1 > B1, B1 < C1)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(false, false)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(false, true)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(true, false)')
        self.assertTrue(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(true, true)')
        self.assertFalse(wb.get_cell_value(name, 'd1'))

        wb.set_cell_contents(name, 'd1', '=XOR(false, false, true)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=XOR()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'b1', 'hello')
        wb.set_cell_contents(name, 'd1', '=XOR(A1, B1)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=XOR(A1, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=XOR(#CIRCREF!, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_exact_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'b1', 'HelLo')
        wb.set_cell_contents(name, 'c1', "hello")
        wb.set_cell_contents(name, 'd1', '=EXACT(A1, B1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), False)

        wb.set_cell_contents(name, 'd1', '=EXACT(A1, C1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'A1', None)
        wb.set_cell_contents(name, 'b1', "'")
        wb.set_cell_contents(name, 'd1', '=EXACT(A1, B1)')
        self.assertEqual(wb.get_cell_value(name, 'b1'), "")
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=EXACT(2, 2)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)
        wb.set_cell_contents(name, 'd1', '=EXACT(2, 3)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), False)

        wb.set_cell_contents(name, 'A1', 'true')
        wb.set_cell_contents(name, 'b1', 'true')
        wb.set_cell_contents(name, 'd1', '=EXACT(a1, b1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)
        wb.set_cell_contents(name, 'd1', '=EXACT(a1, false)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), False)

        wb.set_cell_contents(name, 'd1', '=EXACT(AND(false, true), AND(true, false))')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=EXACT(#REF!, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=EXACT()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        
        wb.set_cell_contents(name, 'd1', '=EXACT(TRUE, TRUE, TRUE)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

    def test_if_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        wb.set_cell_contents(name, 'd1', '=IF(A1 < B1, 1, 2)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal('1'))

        wb.set_cell_contents(name, 'd1', '=IF(A1 > B1, 1, 2)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal('2'))

        wb.set_cell_contents(name, 'd1', '=IF(A1 > B1, 1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), False)

        wb.set_cell_contents(name, 'd1', '=IF(A1 > B1, true, true)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=IF()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=IF(1 < 2, true, true, true)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'd1', '=IF(A1, 1, 2)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=IF(1, "hello",#REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertEqual(value, 'hello')

        wb.set_cell_contents(name, 'd1', '=IF(0, "hello",#REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=IF(#CIRCREF!, #REF!, 1)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_if_error_function(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'd1', '=IFERROR(A1 < B1, 1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=IFERROR(#REF!, 1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal('1'))

        wb.set_cell_contents(name, 'd1', '=IFERROR(#REF!)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), "")

        wb.set_cell_contents(name, 'd1', '=ISERROR(A1+)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.PARSE_ERROR)

        wb.set_cell_contents(name, 'b1', '=A1+')
        wb.set_cell_contents(name, 'd1', '=ISERROR(B1)')
        self.assertEqual(wb.get_cell_value(name, 'd1'), True)

        wb.set_cell_contents(name, 'd1', '=IFERROR()')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'd1', '=IFERROR(1 < 2, true, true)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'A1', 'hello')
        wb.set_cell_contents(name, 'd1', '=IFERROR(A1, 1)')
        value = wb.get_cell_value(name, 'd1')
        self.assertEqual(value, 'hello')

        wb.set_cell_contents(name, 'd1', '=IFERROR(1, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertEqual(value, decimal.Decimal('1'))

        wb.set_cell_contents(name, 'd1', '=IFERROR(#CIRCREF!, #REF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'd1', '=IFERROR(#CIRCREF!)')
        value = wb.get_cell_value(name, 'd1')
        self.assertEqual(value, "")

    def test_functions_in_expressions(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        wb.set_cell_contents(name, 'd1', '=AND(A1 < B1, B1 < C1)')
        wb.set_cell_contents(name, 'e1', '=2 + d1')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('1'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('2'))
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('3'))

        wb.set_cell_contents(name, 'e1', '=2 * d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('2'))

        wb.set_cell_contents(name, 'e1', '=2 & d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), '2TRUE')

        wb.set_cell_contents(name, 'e1', '=-d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('-1'))

        # testing with false
        wb.set_cell_contents(name, 'd1', '=AND(FALSE, FALSE)')
        wb.set_cell_contents(name, 'e1', '=2 + d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('2'))

        wb.set_cell_contents(name, 'e1', '=2 * d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('0'))

        wb.set_cell_contents(name, 'e1', '=2 & d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), '2FALSE')

        wb.set_cell_contents(name, 'e1', '=-d1')
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('0'))

    def test_nested_functions(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'A1', '1')
        wb.set_cell_contents(name, 'b1', '2')
        wb.set_cell_contents(name, 'c1', "3")
        wb.set_cell_contents(name, 'd1', "14")
        wb.set_cell_contents(name, 'e1', '=OR(AND(A1 > 5, B1 < 2), AND(C1 < 6, D1 = 14))')
        self.assertEqual(wb.get_cell_value(name, 'e1'), True)

        wb.set_cell_contents(name, 'e1', '=OR(AND(A1 > 5, B1 < 2), AND(C1 > 6, D1 = 14))')
        self.assertEqual(wb.get_cell_value(name, 'e1'), False)
        
    def test_general_errors(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', '=hello(5)')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_NAME)

if __name__ == '__main__':
    unittest.main()
