'''
This file contains code relating to a row object.
'''


class Row:
    def __init__(self, cell_values, row, sort_cols, cell_dict_lst):
        # list of cell values in the row 
        self.cell_values = cell_values
        # index of row
        self.row = row
        self.sort_cols = sort_cols
        self.curr_col = 0
        self.cell_dict_lst = cell_dict_lst
        self.col_to_sort = 0

    def increment_col(self):
        self.curr_col += 1
    
    def get_cell_to_compare(self):
        self.col_to_sort = self.sort_cols[self.curr_col]
        if self.col_to_sort < 0:
            self.col_to_sort = -self.col_to_sort
        return self.cell_values[self.col_to_sort - 1]
