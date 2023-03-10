from pstats import Stats
import unittest
import cProfile
import sheets


class TestLargeOpPerformance(unittest.TestCase):
    '''
    This class contains extended performance tests for the spreadsheet engine.
    '''
    def enable_profile(self):
        profiler = cProfile.Profile()
        profiler.enable()
        return profiler

    def disable_profile(self, profiler, num_lines):
        profiler.disable()
        stats = Stats(profiler).sort_stats("cumtime")
        stats.print_stats(num_lines)

    def num_to_col(self, num):
        res = ''
        while num > 0:
            num, remainder = divmod (num - 1, 26)
            res = chr(remainder + ord('a')) + res
        return res

    def create_sheet(self, wb, name, num_rows, num_cols, new_name):
        for i in range(1, num_rows):
            col = self.num_to_col(i)
            for j in range(1, num_cols):
                if new_name is None:
                    wb.set_cell_contents(name, f'{col}{j}', '=1')
                else:
                    wb.set_cell_contents(name, f'{col}{j}', f'={new_name}!{col}{j}')
        return wb

    def test_load_workbook_performance(self):
        '''
        Test performance of a test that repeatedly performs a large workbook
        loading request.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_rows = 70
        num_cols = 70
        self.create_sheet(wb, name, num_rows, num_cols, None)
        with open('tests/jsons/performance/load.json', 'w') as f:
            wb.save_workbook(f)

        with open('tests/jsons/performance/load.json', 'r') as f:
            profiler = self.enable_profile()
            wb.load_workbook(f)
            self.disable_profile(profiler, 10)

    def test_copy_sheet_performance(self):
        '''
        Test performance of a test that where a sheet with many cells is
        copied and all cells need to be recalculated.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_rows = 70
        num_cols = 70
        new_name = 'Sheet1_1'
        self.create_sheet(wb, name, num_rows, num_cols, new_name)

        profiler = self.enable_profile()
        wb.copy_sheet(name)
        #print(wb.sheets[name.lower()].cells)
        self.disable_profile(profiler, 10)

    def test_rename_sheet_no_cell_ref_performance(self):
        '''
        Test performance of a test that where a sheet with many cells is
        renamed and all cells need to be recalculated.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_rows = 70
        num_cols = 70
        new_name = 'hello'
        self.create_sheet(wb, name, num_rows, num_cols, None)

        profiler = self.enable_profile()
        wb.rename_sheet(name, new_name)
        self.disable_profile(profiler, 10)

    def test_rename_sheet_cell_ref_update_performance(self):
        '''
        Test performance of a test that where a sheet with many cells is
        renamed and all cells need to be recalculated.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_rows = 70
        num_cols = 70
        new_name = 'helloo'
        self.create_sheet(wb, name, num_rows, num_cols, name)

        profiler = self.enable_profile()
        wb.rename_sheet(name, new_name)
        self.disable_profile(profiler, 10)

    def test_move_cells_performance(self):
        '''
        Test performance of a test that where many cells in a sheet are
        moved.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_rows = 70
        num_cols = 70
        new_name = 'hello'
        wb.new_sheet(new_name)
        self.create_sheet(wb, name, num_rows, num_cols, new_name)

        profiler = self.enable_profile()
        wb.move_cells(name, 'a1', 'a99', 'a100', new_name)
        self.disable_profile(profiler, 10)

if __name__ == '__main__':
    unittest.main()
