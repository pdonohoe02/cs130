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

    def test_comparisons(self):
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

        # test strings

        # test bool

        # test diff types

        # test empty cells

        # test error propagation 
