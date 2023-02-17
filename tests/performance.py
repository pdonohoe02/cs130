from pstats import Stats
import unittest
import cProfile
import sheets


class TestPerformance(unittest.TestCase):
    '''
    This class contains performance tests for the spreadsheet engine.
    '''
    def create_long_chains_refs(self, wb, name, num_chains, num_references):
        for i in range(num_chains):
            if i == num_chains - 1:
                wb.set_cell_contents(name, f'a{i}', '10')
                break
            contents = ''
            for j in range(i + 1, num_chains - (num_chains - num_references)):
                if j == num_chains - (num_chains - num_references) - 1:
                    contents += f'a{j + 1}'
                else:
                    contents += f'a{j + 1} + '

            if contents != '':
                wb.set_cell_contents(name, f'a{i}', f'=a{i + 1} + {contents}')
            else:
                wb.set_cell_contents(name, f'a{i}', f'=a{i + 1}')
        return wb

    def enable_profile(self):
        profiler = cProfile.Profile()
        profiler.enable()
        return profiler

    def disable_profile(self, profiler, num_lines):
        profiler.disable()
        stats = Stats(profiler).sort_stats("cumtime")
        stats.print_stats(num_lines)

    def test_long_chains(self):
        '''
        Test performance of a test that requires updates to propagate through
        long chains of cell references.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        self.create_long_chains_refs(wb, name, 100, 1)

        profiler = self.enable_profile()
        wb.set_cell_contents(name, 'a99', '20')
        self.disable_profile(profiler, 10)

    def test_long_references(self):
        '''
        Test performance of a test that where each cell is referenced by many
        other cells with shallower chains, but still with large amounts of cell
        updates.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        self.create_long_chains_refs(wb, name, 25, 20)

        profiler = self.enable_profile()
        wb.set_cell_contents(name, 'a24', '20')
        self.disable_profile(profiler, 10)

    def test_long_cycles(self):
        '''
        Test performance of workbook with large cycles that contain many cells,
        and repeatedly making then breaking cycles.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_cycles = 30
        profiler = self.enable_profile()

        for i in range(1, num_cycles):
            if i == num_cycles - 1:
                wb.set_cell_contents(name, f'a{i}', '=a1')
            else:
                wb.set_cell_contents(name, f'a{i}', f'=a{i+1}')
        for _ in range(5):
            wb.set_cell_contents(name, 'a20', '5')
            wb.set_cell_contents(name, 'a20', '=a21')
        self.disable_profile(profiler, 10)

    def test_short_cycles(self):
        '''
        Test performance of workbook with many short cycles,
        and repeatedly making then breaking cycles.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_cycles = 50
        cycle_length = 3
        profiler = self.enable_profile()
        for i in range(1, num_cycles):
            if i % cycle_length == 0 or i == num_cycles - 1:
                wb.set_cell_contents(name,
                                     f'a{i}', f'=a{i - cycle_length + 1}')
            else:
                wb.set_cell_contents(name, f'a{i}', f'=a{i+1}')
        for _ in range(5):
            # breaking the cycle
            for i in range(cycle_length - 1, num_cycles, cycle_length):
                wb.set_cell_contents(name, f'a{i}', '5')

            # making cycle again
            for i in range(cycle_length - 1, num_cycles, cycle_length):
                wb.set_cell_contents(name,
                                     f'a{i}',
                                     f'=a{i - cycle_length + 1}')
        self.disable_profile(profiler, 10)

    def test_one_cell_in_cycles(self):
        '''
        Test performance of workbook with one cell participating in many
        different cycles, and repeatedly making then breaking cycles.
        '''
        wb = sheets.Workbook()
        (_, name) = wb.new_sheet()
        num_cycles = 50
        cycle_length = 3
        profiler = self.enable_profile()
        for i in range(1, num_cycles):
            if i % cycle_length == 0 or i == num_cycles - 1:
                wb.set_cell_contents(name, f'a{i}', '=a1')
            else:
                wb.set_cell_contents(name, f'a{i}', f'=a{i+1}')
        for _ in range(5):
            # breaking the cycle
            for i in range(cycle_length - 1, num_cycles, cycle_length):
                wb.set_cell_contents(name, f'a{i}', '5')
            # making the cycle
            for i in range(cycle_length - 1, num_cycles, cycle_length):
                wb.set_cell_contents(name, f'a{i}', '=a1')
        self.disable_profile(profiler, 10)

    # def test_set_unset_cells(self):
    #     '''
    #     Test performance of workbook that repeatedly sets then unsets cells.
    #     '''
    #     wb = sheets.Workbook()
    #     (_, name) = wb.new_sheet()
    #     num_cells = 100
    #     profiler = self.enable_profile()
    #     for i in range(1, num_cells):
    #         wb.set_cell_contents(name, f'a{i}', f'{i}')
    #         wb.set_cell_contents(name, f'a{i}', None)
    #         wb.get_cell_contents(name, f'a{i}')
    #     self.disable_profile(profiler, 10)


if __name__ == '__main__':
    unittest.main()
