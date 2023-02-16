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
        self.extent_row = PriorityQueue()
        self.extent_col = PriorityQueue()

    def set_cell_value(self, cell_location: str, refined_contents: str,
                       value, tree=None, sheet_name_dict=None):
        '''
        Sets a cell's value to a specified value.

        Parameters:
            cell_location (str): the cell's location
            refined_contents (str): the cell's contents
            value (int, str, or CellErrorType): the cell's value to be set
        '''
        init_cell_dict = {'contents': refined_contents,
                          'value': value,
                          'tree': tree,
                          'sheet_name_dict': sheet_name_dict}
        self.cells[cell_location.lower()] = init_cell_dict

        match = re.match(r"([a-z]+)([0-9]+)", cell_location, re.I)
        col, row = match.groups()
        self.extent_col.put((-(ord(col.lower()) - 96), cell_location.lower()))
        self.extent_row.put((-int(row), cell_location.lower()))

    def check_quote_name(self, name):
        '''
        Returns true if the quoted name can be unquoted.
        '''
        if name[0] == "'":
            if ((name[1].isalpha() or name[1] == '_') and
                    (name[1:-1].isalnum() or '_' in name)):
                return True
        else:
            if ((name[0].isalpha() or name[0] == '_') and
               (name.isalnum() or '_' in name)):
                return True
        return False

    def change_contents_sheet_ref(self, cell_location, old_sheet_name,
                                  new_sheet_name):
        '''
        Changes the sheet name reference in a given cell to the new sheet name

        Parameters:
            cell_location: the cells whose contents are updated
            old_sheet_name: the old sheet name that is replaced
            new_sheet_name: the new sheet name that replaces the old sheet name
        '''
        temp_contents = self.cells[cell_location.lower()]['contents']
        sheet_name_dict = self.cells[cell_location.lower()]['sheet_name_dict']
        # go through quoted sheet names
        for quoted_name in sheet_name_dict['QUOTED_SHEET_NAMES'].copy():
            if quoted_name[1:-1].lower() == old_sheet_name.lower():
                sheet_name_dict['QUOTED_SHEET_NAMES'].remove(quoted_name)
                if self.check_quote_name(new_sheet_name) is True:
                    temp_contents = temp_contents.replace(
                        quoted_name, new_sheet_name)
                    sheet_name_dict['SHEET_NAMES'].append(new_sheet_name)
                else:
                    temp_contents = temp_contents.replace(
                        quoted_name, f"'{new_sheet_name}'")
                    sheet_name_dict['QUOTED_SHEET_NAMES'].append(
                        f"'{new_sheet_name}'")
            elif self.check_quote_name(quoted_name) is True:
                temp_contents = temp_contents.replace(
                    quoted_name, quoted_name[1:-1])

        for name in sheet_name_dict['SHEET_NAMES']:
            if name.lower() == old_sheet_name.lower():
                sheet_name_dict['SHEET_NAMES'].remove(name)
                if self.check_quote_name(new_sheet_name) is True:
                    temp_contents = temp_contents.replace(name, new_sheet_name)
                    sheet_name_dict['SHEET_NAMES'].append(new_sheet_name)
                else:
                    temp_contents = temp_contents.replace(
                        name, f"'{new_sheet_name}'")
                    sheet_name_dict['QUOTED_SHEET_NAMES'].append(
                        f"'{new_sheet_name}'")
        self.cells[cell_location.lower()]['contents'] = temp_contents
        self.cells[cell_location.lower()]['tree'] = None

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
        return None
        
    def get_cell_tree(self, cell_location:str):
        '''
        Gets the parse tree of a given cell
        '''
        
        if cell_location.lower() in self.cells:
            return self.cells[cell_location.lower()]['tree']
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
            if (temp_cell in self.cells and self.cells[temp_cell]['contents']
               is not None):
                return_row = -temp_row
                break
            self.extent_row.get()

        while not self.extent_col.empty():
            temp_col, temp_cell = self.extent_col.queue[0]
            if (temp_cell in self.cells and
               self.cells[temp_cell]['contents'] is not None):
                return_col = -temp_col
                break
            self.extent_col.get()

        return return_col, return_row
