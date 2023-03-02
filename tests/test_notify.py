import decimal
import unittest
import sheets


class TestNotify(unittest.TestCase):
    '''
    This class contains the tests relating to the workbook notify
    functionalities corresponding to Project 2.
    '''  
    def on_cells_changed(self, workbook, changed_cells):
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        workbook.get_cell_value(changed_cells[0][0], changed_cells[0][1])
        raise ValueError

    def on_cells_changed2(self, workbook, changed_cells):
        '''
        This function gets called when cells change in the workbook that the
        function was registered on.  The changed_cells argument is an iterable
        of tuples; each tuple is of the form (sheet_name, cell_location).
        '''
        workbook.get_cell_value(changed_cells[0][0], changed_cells[0][1])
        # print(changed_cells)

    def test_notify(self):
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        wb.notify_cells_changed(self.on_cells_changed)
        wb.notify_cells_changed(self.on_cells_changed2)
        # Generates one call to notify functions, with the argument [('Sheet1',
        # 'A1')].
        wb.set_cell_contents(name, "A1", "'123")
        # notify_func1 = str(self.on_cells_changed)
        notify_func2 = str(self.on_cells_changed2)
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A1')})

        # Generates one call to notify functions, with the argument [('Sheet1',
        # 'C1')].
        wb.set_cell_contents(name, "C1", "=A1+B1")
        self.assertEqual(wb.notify_cells_master, {('Sheet1', 'C1')})

        # Generates one or more calls to notify functions, indicating that
        # cells B1 and C1 have changed.  For example, there might be one call
        # with the argument [('Sheet1', 'B1'), ('Sheet1', 'C1')].
        wb.set_cell_contents(name, "B1", "5.3")
        self.assertEqual(wb.notify_cells_master, {('Sheet1', 'B1'), ('Sheet1', 'C1')})

        # c1 should not be reported, c1's value is not changing
        wb.set_cell_contents(name, "a1", "123")
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A1')})

        wb.set_cell_contents(name, "a2", "=sheet2!123")
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A2')})
        
        wb.set_cell_contents(name, "a2", "=sheet2!a1")
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A2')})
        
        (_, name2) = wb.new_sheet()
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A2')})

        wb.del_sheet(name2)
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A2')})

        (_, name2) = wb.new_sheet()
        self.assertEqual(
            wb.notify_cells_master, {('Sheet1', 'A2')})

        wb.rename_sheet(name2, 'temp')
        self.assertEqual(wb.notify_cells_master, set())

        wb.set_cell_contents(name, 'a3', '=sheet1_1!a2')
        
        self.assertEqual(wb.notify_cells_master, {('Sheet1', 'A3')})
        wb.copy_sheet(name)
        lst = {('Sheet1', 'A3'), ('Sheet1_1', 'A1'), ('Sheet1_1', 'C1'),
               ('Sheet1_1', 'B1'), ('Sheet1_1', 'A2'), ('Sheet1_1', 'A3')}
        self.assertEqual(wb.notify_cells_master, lst)

        wb.set_cell_contents(name, "a4", "=a1")
        wb.copy_cells(name, 'a1', 'a4', 'b1')
        lst = {('Sheet1', 'B4'), ('Sheet1', 'B1'), ('Sheet1', 'B2'), ('Sheet1', 'B3')}
        self.assertEqual(wb.notify_cells_master, lst)

        wb.move_cells(name, 'a1', 'a4', 'b1')
        lst = {('Sheet1', 'A1'), ('Sheet1', 'A2'), ('Sheet1', 'A3'), ('Sheet1', 'A4')}
        self.assertEqual(wb.notify_cells_master, lst)

        wb.move_cells(name, 'b1', 'b4', 'b2')
        lst = {('Sheet1', 'B5'), ('Sheet1', 'B1'), ('Sheet1', 'B2'), ('Sheet1', 'B3'), ('Sheet1', 'B4')}
        self.assertEqual(wb.notify_cells_master, lst)


if __name__ == '__main__':
    unittest.main()
