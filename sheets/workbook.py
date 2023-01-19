'''
This file contains the bulk of the spreadsheet engine, which allows for the
basic functions of spreadsheets (creating workbooks, creating and deleting
sheets, populating cells, and calculating formulas). Currently, the engine
handles both string and integers in the cells.
'''

from typing import List, Optional, Tuple, Any
from lark_impl import parse_contents
from lark import Token
import re
import decimal

from sheet import Sheet
from cellerror import CellErrorType, CellError


class Workbook:
    '''
    A workbook containing zero or more named spreadsheets.

    Any and all operations on a workbook that may affect calculated cell
    values should cause the workbook's contents to be updated properly.
    '''

    def __init__(self):
        '''
        Initialize a new empty workbook.
        '''
        # dictionary of sheets mapping name to Sheet object
        self.sheets = {}

        # maps lower case names to case-sensitive name
        self.sheet_names = {}

    def num_sheets(self) -> int:
        '''
        Gets the number of sheets in a workbook.

        Returns:
            int: the number of sheets
        '''
        # Return the number of spreadsheets in the workbook.
        return len(self.sheets.keys())

    def list_sheets(self) -> List[str]:
        '''
        Return a list of the spreadsheet names in the workbook, with the
        capitalization specified at creation, and in the order that the sheets
        appear within the workbook.

        In this project, the sheet names appear in the order that the user
        created them; later, when the user is able to move and copy sheets,
        the ordering of the sheets in this function's result will also reflect
        such operations.

        Returns:
            list: a list of spreadsheet names
        '''
        return list(self.sheet_names.values())

    def is_valid_sheet_name(self, sheet_name):
        '''
        Helper method to check if a sheet name is valid. Sheet names cannot
        contain quotes of any kind, cannot start or end with whitespace
        characters, and cannot be an empty string. All sheet names must be
        unique, regardless of case. "Uniqueness" is determined in a
        case-insensitive manner, but the case specified for the sheet name is
        preserved.

        Parameters:
            sheet_name (str): the name of a sheet

        Returns:
            bool: True if sheet name is valid,
                  False otherwise
        '''
        punctuation_characters = " .?!,:;!@#$%^&*()-_"
        if sheet_name is None or sheet_name == '':
            return False
        if sheet_name[0] == ' ' or sheet_name[-1] == ' ':
            return False
        if sheet_name.lower() in self.sheet_names:
            return False
        for char in sheet_name:
            if not (char.isalnum() or char in punctuation_characters):
                return False
        return True

    def generate_sheet_name(self):
        '''
        Helper method to generate new sheet names in the case where a user
        does not specify a sheet name. Default names will be of the form
        "Sheet1", "Sheet2", etc.

        Returns:
            str: a unique default sheet name
        '''
        counter = 1
        while True:
            if f'sheet{counter}' not in self.sheet_names:
                return f'Sheet{counter}'
            counter += 1

    def new_sheet(self, sheet_name: Optional[str] = None) -> Tuple[int, str]:
        '''
        Adds a new sheet to the workbook.

        Raises ValueError if the spreadsheet name is an empty string, or it is
        otherwise invalid.

        Parameters:
            sheet_name (str): the name of a sheet

        Returns:
            (int, str): (0-based index of sheet in workbook, sheet name);
        '''
        if sheet_name is None:
            sheet_name = self.generate_sheet_name()
        if self.is_valid_sheet_name(sheet_name):
            # add new Sheet with sheet_name to dictionary
            self.sheets[sheet_name.lower()] = Sheet()
            self.sheet_names[sheet_name.lower()] = sheet_name
        else:
            raise ValueError("Invalid spreadsheet name.")

        return (len(self.sheets.keys()) - 1, sheet_name)

    def del_sheet(self, sheet_name: str) -> None:
        '''
        Delete the spreadsheet with the specified name.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        If the specified sheet name is not found, a KeyError is raised.

        Parameters:
            sheet_name (str): the name of a sheet
        '''
        if sheet_name.lower() in self.sheets:
            check_yo_self = []
            for k in self.sheets[sheet_name.lower()].dependent_cells:
                for cell in self.sheets[sheet_name.lower()].dependent_cells[k]:
                    if cell[0] != sheet_name.lower():
                        check_yo_self.append(cell)

            del self.sheets[sheet_name.lower()]
            del self.sheet_names[sheet_name.lower()]
            for cell in check_yo_self:
                contents = self.get_cell_contents(cell[0], cell[1])
                self.internal_set_cell_contents(cell[0], cell[1], contents,
                                                is_new=True)
        else:
            raise KeyError("Sheet name not found.")

    def get_sheet_extent(self, sheet_name: str) -> Tuple[int, int]:
        '''
        Return a tuple (num-cols, num-rows) indicating the current extent of
        the specified spreadsheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        If the specified sheet name is not found, a KeyError is raised.

        Parameters:
            sheet_name (str): the name of a sheet
        '''
        if sheet_name.lower() in self.sheets:
            return self.sheets[sheet_name.lower()].get_extent()
        else:
            raise KeyError("Sheet name not found.")

    def tarjan_iter(self, sheet_name, location):
        '''
        Helper method that implements an iterative form of Tarjan's algorithm.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): the location of a cell

        Returns:
            (list, list): a tuple of a list of cycles and a list of
                          dependencies
        '''
        stack = [(sheet_name, location)]
        on_stack = {(sheet_name, location): None}
        visited = {}
        topo_sort = []
        sccs = []
        disc_time = {}
        low = {}
        stack_cpy = [(sheet_name, location)]
        while stack:
            v = stack[-1]
            if v not in visited:
                visited[v] = None
                disc_time[v] = len(stack) - 1
                low[v] = len(stack) - 1
                for u in self.sheets[v[0].lower()].get_dependent_cells(v[1]):
                    if u not in visited:
                        stack.append(u)
                        on_stack[u] = None
                        stack_cpy.append(u)
                    elif u in on_stack:
                        low[v] = min(low[v], disc_time[u])
            else:  # Leaving the node
                if low[v] == disc_time[v]:
                    w = -1
                    scc = []
                    while w != v:
                        w = stack_cpy.pop()
                        scc.append(w)
                    sccs.append(scc)
                k = stack.pop()
                del on_stack[k]
                topo_sort.append(k)
            cycles = []
            for i in sccs:
                if len(i) > 1:
                    cycles.append(i)
        return (cycles, topo_sort)

    def update_workbook(self, sheet_name: str, location: str):
        '''
        Helper method that updates the workbook after a change is made.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): the location of a cell
        '''
        cycles, topo_sort = self.tarjan_iter(sheet_name, location)
        for cycle in cycles:
            for v in cycle:
                detail = 'Cell is part of circular reference.'
                contents = self.get_cell_contents(v[0], v[1])
                circ_ref = CellError(CellErrorType.CIRCULAR_REFERENCE, detail)
                self.sheets[v[0].lower()].set_cell_value(
                    v[1], contents, circ_ref)

        for v in topo_sort:
            contents = self.get_cell_contents(v[0], v[1])
            self.internal_set_cell_contents(v[0], v[1], contents, is_new=False)

    def is_string_float(self, val):
        '''
        Helper method that checks if a string is a float.

        Parameters:
            val (str): the string to be checked

        Returns:
            bool: True if string is float,
                  False otherwise
        '''
        return re.match(r'^-?\d+(?:\.\d+)$', val) is not None

    def convert_to_error(self, contents):
        '''
        Helper method that converts the string representation of an error to
        an actual CellErrorType.

        Parameters:
            contents (str): the cell's contents to be converted

        Returns:
            CellError: error corresponding to its string representation.
        '''
        error_dict = {
            "#ERROR!": {
                'type': CellErrorType.PARSE_ERROR,
                'detail': 'Formula cannot be parsed.'},
            "#CIRCREF!": {
                'type': CellErrorType.CIRCULAR_REFERENCE,
                'detail': 'Cell is part of circular reference'},
            "#REF!": {
                'type': CellErrorType.BAD_REFERENCE,
                'detail': 'Invalid cell reference in formula. \
                           Check sheet name and cell location.'},
            "#NAME?": {
                'type': CellErrorType.BAD_NAME,
                'detail': 'Function name in formula is unrecognized.'},
            "#VALUE!": {
                'type': CellErrorType.TYPE_ERROR,
                'detail': 'Incompatible types of values.'},
            "#DIV/0!": {
                'type': CellErrorType.DIVIDE_BY_ZERO,
                'detail': 'Cannot divide by zero.'}}
        if contents.upper() in error_dict:
            return CellError(error_dict[contents.upper()]['type'],
                             error_dict[contents.upper()]['detail'])
        return contents

    def calculate_contents(
            self, sheet_name, contents: Optional[str]):
        '''
        Helper method that returns tuple of the (contents, value) for a cell.

        Parameters:
            sheet_name (str): the name of a sheet
            contents (str, None): contents of a cell

        Returns:
            (str, int or str, Tree): tuple containing a cell's contents, value,
                                     and parsed tree.
        '''
        if contents is None or contents == '' or contents.isspace():
            return None, None, None

        contents = contents.strip()
        value = contents
        if contents[0] == '=':
            value, tree = parse_contents(sheet_name, contents, self)
            if isinstance(value, decimal.Decimal) and '.' in str(value):
                temp = str(value).rstrip('0').rstrip('.')
                value = decimal.Decimal(temp)
            return contents, value, tree

        value = self.convert_to_error(contents)

        if contents[0] == "'":
            value = contents[1:]
        elif not isinstance(value, CellError):
            value = value.strip()
            if '.' in value:
                value = value.rstrip('0').rstrip('.')
            if self.is_string_float(value):
                value = decimal.Decimal(value)
            elif value.isdigit():
                value = decimal.Decimal(value)

        return contents, value, None

    def is_valid_cell_location(self, location) -> bool:
        '''
        Checks if a cell location is valid, which takes the format of a letter
        followed by a number (case-insensitive). Note that cell location cannot
        exceed ZZZZ9999. Cell locations may not contain any whitespace;
        leading, trailing, or otherwise.

        Parameters:
            location (str): a cell's location

        Returns:
            bool: True if location is valid,
                  False otherwise
        '''
        if not location or location is None:
            return False
        if location[0] == ' ' or location[-1] == ' ':
            return False

        match = re.match(r"([a-z]+)([0-9]+)", location, re.I)
        if not match:
            return False

        row, col = match.groups()
        if len(row) > 4 or len(col) > 4:
            return False

        return True

    def tree_dfs(self, tree, sheet_name):
        '''
        Helper method that implements DFS on a parsed tree to find cell
        references.

        Parameters:
            tree (Tree): a parsed tree
            sheet_name (str): the name of a sheet

        Returns:
            (list, list): a tuple of a list of cycles and a list of
                          dependencies
        '''
        stack = [tree]
        cell_refs = []
        while stack:
            node = stack.pop()
            if isinstance(node, Token):
                continue
            elif node.data == 'cell':
                temp_sheet_name = None
                if node.children[0].type == 'SHEET_NAME':
                    temp_sheet_name = node.children[0].value
                    cell = node.children[1].value
                else:
                    cell = node.children[0].value

                if (temp_sheet_name is not None and
                   temp_sheet_name.lower() in self.sheets):
                    sheet_name = temp_sheet_name
                cell_refs.append((sheet_name.lower(), cell.lower()))
            else:
                for i in node.children:
                    stack.append(i)

        return cell_refs

    def set_cell_contents(self, sheet_name: str, location: str,
                          contents: Optional[str]) -> None:
        '''
        Set the contents of the specified cell on the specified sheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.  Additionally, the cell location can be
        specified in any case.

        If the specified sheet name is not found, a KeyError is raised.
        If the cell location is invalid, a ValueError is raised.

        A cell may be set to "empty" by specifying a contents of None.

        Leading and trailing whitespace are removed from the contents before
        storing them in the cell.  Storing a zero-length string "" (or a
        string composed entirely of whitespace) is equivalent to setting the
        cell contents to None.

        If the cell contents appear to be a formula, and the formula is
        invalid for some reason, this method does not raise an exception;
        rather, the cell's value will be a CellError object indicating the
        naure of the issue.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): a cell's location
            contents (str or int): a cell's contents
        '''
        return self.internal_set_cell_contents(sheet_name, location, contents,
                                               is_new=True)

    def internal_set_cell_contents(self, sheet_name: str, location: str,
                                   contents: Optional[str],
                                   is_new: Optional[bool]) -> None:
        '''
        Internal set_cell_contents method.
        '''
        location = location.lower()
        sheet_name = sheet_name.lower()
        if sheet_name not in self.sheets:
            raise KeyError("Sheet name not found.")
        if not self.is_valid_cell_location(location):
            raise ValueError("Invalid cell location.")

        contents, value, tree = self.calculate_contents(sheet_name, contents)
        if is_new and location not in self.sheets[sheet_name].dependent_cells:
            self.sheets[sheet_name].set_cell_value(
                location, contents, value, [])
        else:
            self.sheets[sheet_name].set_cell_value(location, contents, value)

        if tree is not None:
            inherit_cells = self.tree_dfs(tree, sheet_name)
            for i in inherit_cells:
                curr_name = i[0].lower()
                curr_loc = i[1].lower()
                if curr_name not in self.sheets:
                    continue
                dep_cells = self.sheets[curr_name].dependent_cells
                if i[1] in dep_cells:
                    if (sheet_name, location) not in dep_cells[curr_loc]:
                        dep_cells[curr_loc].append((sheet_name, location))
                elif i[1] in self.sheets[curr_name].cells:
                    dep_cells[curr_loc] = [(sheet_name, location)]
                else:
                    self.sheets[curr_name].set_cell_value(i[1], None, None, [])
                    dep_cells[curr_loc] = [(sheet_name, location)]

        if is_new:
            self.update_workbook(sheet_name, location)

    def get_cell_contents(self, sheet_name: str,
                          location: str) -> Optional[str]:
        '''
        Return the contents of the specified cell on the specified sheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.  Additionally, the cell location can be
        specified in any case.

        If the specified sheet name is not found, a KeyError is raised.
        If the cell location is invalid, a ValueError is raised.

        Any string returned by this function will not have leading or trailing
        whitespace, as this whitespace will have been stripped off by the
        set_cell_contents() function.

        This method will never return a zero-length string; instead, empty
        cells are indicated by a value of None.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): a cell's location

        Returns:
            string: the cell's contents,
            None if cell is empty
        '''
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet name not found.")
        if not self.is_valid_cell_location(location):
            raise ValueError("Invalid cell location.")

        return self.sheets[sheet_name.lower()].get_cell_contents(location)

    def get_cell_value(self, sheet_name: str, location: str) -> Any:
        '''
        Return the evaluated value of the specified cell on the specified
        sheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.  Additionally, the cell location can be
        specified in any case.

        If the specified sheet name is not found, a KeyError is raised.
        If the cell location is invalid, a ValueError is raised.

        The value of empty cells is None.  Non-empty cells may contain a
        value of str, decimal.Decimal, or CellError.

        Decimal values will not have trailing zeros to the right of any
        decimal place, and will not include a decimal place if the value is a
        whole number.  For example, this function would not return
        Decimal('1.000'); rather it would return Decimal('1').

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): a cell's location

        Returns:
            str, int, CellValue: the value of the cell
        '''
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet name not found.")
        if not self.is_valid_cell_location(location):
            raise ValueError("Invalid cell location.")

        return self.sheets[sheet_name.lower()].get_cell_value(location)
