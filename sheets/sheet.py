'''
This file contains code that handles basic sheet operations, such as getting
and setting cell values, getting and setting cell contents, and also getting
the extent of a sheet.
'''

import re
from queue import PriorityQueue


class Sheet:
    '''
    A class representing a sheet in a workbook.
    '''
    def __init__(self):
        '''
        Initializes a new empty sheet.
        '''
        # maps cell location to a dictionary with value and contents keys
        self.cells = {}
        self.dependent_cells = {}
        self.extent_row = PriorityQueue()
        self.extent_col = PriorityQueue()

    def set_cell_value(self, cell_location: str, refined_contents: str, value,
                       dependent_cells=None):
        '''
        Sets a cell's value to a specified value.

        Parameters:
            cell_location (str): the cell's location
            refined_contents (str): the cell's contents
            value (int, str, or CellErrorType): the cell's value to be set
            dependent_cells (list): the cells that are dependent on the 
                                    current cell
        '''
        if dependent_cells is not None:
            self.dependent_cells[cell_location.lower()] = dependent_cells
        self.cells[cell_location.lower()] = {'contents': refined_contents, 
                                             'value': value}

        match = re.match(r"([a-z]+)([0-9]+)", cell_location, re.I)
        col, row = match.groups()
        self.extent_col.put((-(ord(col.lower()) - 96), cell_location.lower()))
        self.extent_row.put((-int(row), cell_location.lower()))

    def get_dependent_cells(self, cell_location: str):
        '''
        Gets the cells that are dependent on a specified cell.

        Parameters:
            cell_location (str): the cell's location

        Returns:
            dict: a dictionary mapping a cell to a list of its dependent cells;
            else None if the specified cell location is not found.
        '''
        if cell_location.lower() not in self.dependent_cells:
            return None
        return self.dependent_cells[cell_location.lower()]

    def get_cell_contents(self, cell_location: str):
        '''
        Gets the specified cell's contents.

        Parameters:
            cell_location (str): the cell's location
        
        Returns:
            string: the cell's contents;
            else None if the specified cell location is not found.
        '''
        if cell_location.lower() in self.cells:
            return self.cells[cell_location.lower()]['contents']
        else:
            return None

    def get_cell_value(self, cell_location: str):
        '''
        Gets the specified cell's value.

        Parameters:
            cell_location (str): the cell's location
        
        Returns:
            string: the cell's value;
            else None if the specified cell location is not found.
        '''
        if cell_location.lower() in self.cells:
            return self.cells[cell_location.lower()]['value']
        else:
            return None

    def get_extent(self):
        '''
        Gets the extent of a sheet. 
        
        Note that a sheet with one entry at D14 will have an extent of (4, 14).

        Returns:
            tuple: the size of the sheet in the form (row, col)
        '''
        return_row = 0
        return_col = 0

        while not self.extent_row.empty():
            temp_row, temp_cell = self.extent_row.queue[0]
            if temp_cell in self.cells and self.cells[temp_cell]['contents'] is not None:
                return_row = -temp_row
                break
            else:
                self.extent_row.get()

        while not self.extent_col.empty():
            temp_col, temp_cell = self.extent_col.queue[0]
            if temp_cell in self.cells and self.cells[temp_cell]['contents'] is not None:
                return_col = -temp_col
                break
            else:
                self.extent_col.get()
                
        return return_col, return_row
