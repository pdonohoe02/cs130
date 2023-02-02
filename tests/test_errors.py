import decimal
import unittest
import sheets

class TestErrors(unittest.TestCase):
    '''
    This class contains the tests relating to formula calculation errors.
    '''
    def test_bad_ref_error(self):
        # If A's BAD_REFERENCE error is due to missing a sheet S, and S gets
        # added, then A should no longer be a BAD_REFERENCE error.
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=unknown!a2")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)
        wb.new_sheet('unknown')
        wb.set_cell_contents(name, 'a1', "=unknown!a2")
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('0'))


        # deleting an existing sheet, cells that reference old sheet should
        # now be BAD_REFERERENCE errors
        wb.set_cell_contents(name, 'a2', "=unknown!a2")
        wb.set_cell_contents(name, 'a3', "=unknown!a2")
        value2 = wb.get_cell_value(name, 'a2')
        value3 = wb.get_cell_value(name, 'a3')
        wb.del_sheet('unknown')
        value2 = wb.get_cell_value(name, 'a2')
        value3 = wb.get_cell_value(name, 'a3')
        self.assertTrue(isinstance(value2, sheets.CellError))
        self.assertEqual(value2.get_type(), sheets.CellErrorType.BAD_REFERENCE)
        self.assertTrue(isinstance(value3, sheets.CellError))
        self.assertEqual(value3.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # cells referring to locations > ZZZZ9999 should be BAD_REFERENCE
        # errors
        wb.set_cell_contents(name, 'a4', "=SHEET1 + 5")
        value = wb.get_cell_value(name, 'a4')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.new_sheet('hello')
        wb.set_cell_contents(name, 'a5', "=hello!SHEET1")
        value = wb.get_cell_value(name, 'a5')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'a6', "=-SHEET1")
        value = wb.get_cell_value(name, 'a6')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        wb.set_cell_contents(name, 'a7', "=a8")
        wb.set_cell_contents(name, 'a8', "=#ref!")
        value = wb.get_cell_value(name, 'a7')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)
        value = wb.get_cell_value(name, 'a8')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

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

        # test that a string {plus, times, minus, divided by} a string results
        # in a type error.
        wb.set_cell_contents(name, 'a1', "hello")
        wb.set_cell_contents(name, 'a2', "bye")
        wb.set_cell_contents(name, 'a3', '=a1+a2')
        value = wb.get_cell_value(name, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'a3', '=a1-a2')
        value = wb.get_cell_value(name, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)

        wb.set_cell_contents(name, 'a3', '=a1&5')
        value = wb.get_cell_value(name, 'a3')
        self.assertEqual(value, 'hello5')

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

        # Check the case where a cell directly refers to itself
        wb.set_cell_contents(name, 'a1', "=a1")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'a1', "=b1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'c1', '=b1/0')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.del_sheet(name)
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=B1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'C1', '=b1/0')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.del_sheet(name)
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=a2")
        wb.set_cell_contents(name, 'a2', "=a1+invalidsheet!a1")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.del_sheet(name)
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=#circref!")
        wb.set_cell_contents(name, 'a2', "=#ref!")
        wb.set_cell_contents(name, 'a3', "=a1+a2")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)
        value = wb.get_cell_value(name, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_quoted_circ_ref(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.new_sheet('other totals')
        wb.set_cell_contents(name, 'a1', "=b1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'c1', "='other totals'!d1")
        wb.set_cell_contents('other totals', 'd1', f'={name}!a1')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value('other totals', 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_multiple_errors(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a5', "hello")
        wb.set_cell_contents(name, 'a6', "5.3")
        wb.set_cell_contents(name, 'a7', '=a5+a6')
        wb.set_cell_contents(name, 'a8', '=a7+a9')
        wb.set_cell_contents(name, 'a9', '=a8')
        self.assertEqual(wb.get_cell_value(name, 'a5'), 'hello')
        self.assertEqual(wb.get_cell_value(name, 'a6'), decimal.Decimal('5.3'))
        value = wb.get_cell_value(name, 'a7')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.TYPE_ERROR)
        value = wb.get_cell_value(name, 'a8')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)
        
        value = wb.get_cell_value(name, 'a9')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_unary_circref(self):
        '''
        Test if A is a circref error, and B=-A, then B is also a circref
        error.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=#circref!")
        
        wb.set_cell_contents(name, 'b1', "=-a1")
        value = wb.get_cell_value(name, 'b1')
        
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
    
    def test_simple_loops(self):
        '''
        Check the case where there is a single and multiple loops.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=b1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'c1', '=d1')
        wb.set_cell_contents(name, 'd1', '=a1')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

        wb.set_cell_contents(name, 'a2', "=b2")
        wb.set_cell_contents(name, 'b2', "=c2")
        wb.set_cell_contents(name, 'c2', '=d2')
        wb.set_cell_contents(name, 'd2', '=a2')
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'd2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_sheets_circref(self):
        '''
        Check that cycles should be detected when they span multiple sheets.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        (_, name2) = wb.new_sheet()
        (_, name3) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', f"={name2}!b1")
        wb.set_cell_contents(name2, 'b1', f"={name3}!c1")
        wb.set_cell_contents(name3, 'c1', f"={name}!a1")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name2, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name3, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_marking_cycles(self):
        '''
        Cells not involved in the cycles should not be marked
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=5+4")
        wb.set_cell_contents(name, 'a2', "=a3")
        wb.set_cell_contents(name, 'a3', '=a4+a5')
        wb.set_cell_contents(name, 'a4', '=a1*10')
        wb.set_cell_contents(name, 'a5', '=a3')
        wb.set_cell_contents(name, 'a6', "=10*a10")
        wb.set_cell_contents(name, 'a7', '=a8')
        wb.set_cell_contents(name, 'a8', '=a9')
        wb.set_cell_contents(name, 'a9', '=a7')
        wb.set_cell_contents(name, 'a10', "=a1+a4")
        value = wb.get_cell_value(name, 'a1')
        self.assertEqual(value, decimal.Decimal(9))
        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a4')
        self.assertEqual(value, decimal.Decimal(90))
        value = wb.get_cell_value(name, 'a5')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a6')
        self.assertEqual(value, decimal.Decimal(990))
        value = wb.get_cell_value(name, 'a7')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a8')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a9')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'a10')
        self.assertEqual(value, decimal.Decimal(99))


    def test_multiple_circref(self):
        '''
        Check the case where there are multiple loops.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        # first loop
        wb.set_cell_contents(name, 'a1', "=b1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'c1', '=a1')

        # second loop
        wb.set_cell_contents(name, 'a2', "=b2")
        wb.set_cell_contents(name, 'b2', "=c2")
        wb.set_cell_contents(name, 'c2', '=a2')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

        value = wb.get_cell_value(name, 'a2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c2')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)

    def test_cell_point_to_circref(self):
        '''
        Test special case where the cell is not participating in the cycle but
        points to a cell that is.
        TODO: THIS IS WORKING PROPERLY?
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.set_cell_contents(name, 'a1', "=b1")
        wb.set_cell_contents(name, 'b1', "=c1")
        wb.set_cell_contents(name, 'c1', '=d1')
        wb.set_cell_contents(name, 'd1', '=a1')
        wb.set_cell_contents(name, 'e1', '=b1')
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'b1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'c1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'd1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name, 'e1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        wb.set_cell_contents(name, 'd1', '5')
        self.assertEqual(wb.get_cell_value(name, 'a1'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'b1'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'c1'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'd1'), decimal.Decimal('5'))
        self.assertEqual(wb.get_cell_value(name, 'e1'), decimal.Decimal('5'))

    def test_update_workbook_errors(self):
        wb = sheets.Workbook()
        (_, name1) = wb.new_sheet()
        wb.set_cell_contents(name1, 'a1', "=#circref!")
        wb.set_cell_contents(name1, 'a2', "5")
        wb.set_cell_contents(name1, 'a3', "=a1+a2")
        value = wb.get_cell_value(name1, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
        value = wb.get_cell_value(name1, 'a2')
        self.assertEqual(value, 5)
        value = wb.get_cell_value(name1, 'a3')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(
            value.get_type(),
            sheets.CellErrorType.CIRCULAR_REFERENCE)
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
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

    def test_error_literals(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()

        # test formulas with addition involving error literals
        wb.set_cell_contents(name, 'a1', "=#REF! + 5")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test formulas with subtraction involving error literals
        wb.set_cell_contents(name, 'a1', "=#REF! - 5")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test formulas with multiplication involving error literals
        wb.set_cell_contents(name, 'a1', "=#REF! * 5")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test formulas with division involving error literals
        wb.set_cell_contents(name, 'a1', "=#REF! / 5")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test formulas with parentheses involving error literals
        wb.set_cell_contents(name, 'a1', "=(#REF!)")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

        # test formulas with unary operators involving error literals
        wb.set_cell_contents(name, 'a1', "=-#REF!")
        value = wb.get_cell_value(name, 'a1')
        self.assertTrue(isinstance(value, sheets.CellError))
        self.assertEqual(value.get_type(), sheets.CellErrorType.BAD_REFERENCE)

if __name__ == '__main__':
    unittest.main()