# ==============================================================================
# Caltech CS130 - Winter 2023
#
# This file specifies the API that we expect your implementation to conform to.
# You will likely want to move these classes into various files, but the tests
# will expect these to be available when the "sheets" module is imported.

# If you are unfamiliar with Python 3 type annotations, see the Python standard
# library documentation for the typing module here:
#
#     https://docs.python.org/3/library/typing.html
#
# NOTE:  THIS FILE WILL NOT WORK AS-IS.  You are expected to incorporate it
#        into your project in whatever way you see fit.

from typing import *
from lark_impl import parse_contents
import re
import decimal

# import sys
# sys.path.append(".")
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
        dictionary of sheets mapping name to Sheet object
        '''
        self.sheets = {}

        # maps lower case names to case-sensitive name
        self.sheet_names = {}

    def num_sheets(self) -> int:
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

        A user should be able to mutate the return-value without affecting the
        workbook's internal state.
        '''
        return list(self.sheet_names.values())

    def is_valid_sheet_name(self, sheet_name):
        punctuation_characters = " .?!,:;!@#$%^&*()-_"
        if sheet_name[0] == ' ' or sheet_name[-1] == ' ':
            return False

        for char in sheet_name:
            if not (char.isalnum() or char in punctuation_characters):
                return False

        return True

    def generate_sheet_name(self):
        counter = 1
        while True:
            if f'sheet{counter}' not in self.sheet_names:
                return f'Sheet{counter}'
            counter += 1

            # remove later
            if counter > 1000:
                assert (False)

    def new_sheet(self, sheet_name: Optional[str] = None) -> Tuple[int, str]:
        # Add a new sheet to the workbook.  If the sheet name is specified, it
        # must be unique.  If the sheet name is None, a unique sheet name is
        # generated.  "Uniqueness" is determined in a case-insensitive manner,
        # but the case specified for the sheet name is preserved.
        #
        # The function returns a tuple with two elements:
        # (0-based index of sheet in workbook, sheet name).  This allows the
        # function to report the sheet's name when it is auto-generated.
        #
        # If the spreadsheet name is an empty string (not None), or it is
        # otherwise invalid, a ValueError is raised.
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
        # Delete the spreadsheet with the specified name.
        #
        # The sheet name match is case-insensitive; the text must match but the
        # case does not have to.
        #
        # If the specified sheet name is not found, a KeyError is raised.
        if sheet_name.lower() in self.sheets:
            del self.sheets[sheet_name.lower()]
            del self.sheet_names[sheet_name]
        else:
            raise KeyError("Sheet name not found")

    def get_sheet_extent(self, sheet_name: str) -> Tuple[int, int]:
        # Return a tuple (num-cols, num-rows) indicating the current extent of
        # the specified spreadsheet.
        #
        # The sheet name match is case-insensitive; the text must match but the
        # case does not have to.
        #
        # If the specified sheet name is not found, a KeyError is raised.
        if sheet_name.lower() in self.sheets:
            return self.sheets[sheet_name.lower()].get_extent()
        else:
            raise KeyError("Sheet name not found.")

    def update_workbook(self, sheet_name: str, location: str):
        # we need a graph dictionary which maps down the graph, from a cell to
        # all of its dependent cells
        # for updating we need to do a couple of things
        # first we need to return a topological sort
        # cycle dectection we need to know exactly what cells are in the cycles
        
        pass

    def is_string_float(self, val):
        return re.match(r'^-?\d+(?:\.\d+)$', val) is not None

    def convert_to_error(self, contents):
        error_dict = {
            "#ERROR!": {
                'type': CellErrorType.PARSE_ERROR,
                'detail': 'Formula cannot be parsed.'},
            "#CIRCREF!": {
                'type': CellErrorType.CIRCULAR_REFERENCE,
                'detail': 'Cell is part of Circular Reference'},
            "#REF!": {
                'type': CellErrorType.BAD_REFERENCE,
                'detail': 'Invalid cell reference in formula. Check sheet name and cell location.'},
            "#NAME?": {
                'type': CellErrorType.BAD_NAME,
                'detail': 'Cell is part of Circular Reference'},
            "#VALUE!": {
                'type': CellErrorType.TYPE_ERROR,
                'detail': 'Cell is part of Circular Reference'},
                
            "#DIV/0!": {
                'type': CellErrorType.DIVIDE_BY_ZERO,
                'detail': 'Cell is part of Circular Reference'}
            }
        if contents.upper() in error_dict:
            return CellError(error_dict[contents.upper()]['type'], error_dict[contents.upper()]['detail'])
        return contents

    def calculate_contents(
            self, sheet_name, contents: Optional[str]) -> Tuple[str, Union[int, str]]:
        '''
        Returns tuple of the (contents, value) for a cell.
        '''
        if contents is None or contents == '' or contents.isspace():
            return None, None

        contents = contents.strip()
        value = contents
        if contents[0] == '=':
            value = parse_contents(sheet_name, contents, self)
            # if type(value) is CellError:
            #     return contents, value, value_type
            return contents, value
        
        value = self.convert_to_error(contents)
        
        if contents[0] == "'":
            value = contents[1:]
        elif type(value) is not CellError:
            value = value.strip()
            if self.is_string_float(value):
                # string is a float
                value = decimal.Decimal(value)
            elif value.isdigit():
                # string is an int
                value = decimal.Decimal(value)

        return contents, value

    def is_valid_cell_location(self, location) -> bool:
        '''
        Checks if a cell location is valid, which takes the format of a letter
        followed by a number (case-insensitive). Note that cell location cannot
        exceed ZZZZ9999. Cell locations may not contain any whitespace;
        leading, trailing, or otherwise.
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
        '''
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet name not found.")
        if not self.is_valid_cell_location(location):
            raise ValueError("Invalid cell location.")

        contents, value = self.calculate_contents(sheet_name.lower(), contents)

        # if contents is None then Sheet will handle the empty cell
        self.sheets[sheet_name.lower()].set_cell_value(
            location, contents, value)
        self.update_workbook(sheet_name.lower(), location)

    def get_cell_contents(
            self,
            sheet_name: str,
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
        '''
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet name not found.")
        if not self.is_valid_cell_location(location):
            raise ValueError("Invalid cell location.")

        return self.sheets[sheet_name.lower()].get_cell_value(location)

# wb = Workbook()
# name = 'temp'
# wb.new_sheet(name)
# print('div')
# wb.set_cell_contents(name, 'e1', '#div/0!')
# print('e2')
# # wb.set_cell_contents(name, 'e2', '=e1+5')
# print(parse_contents(name, '#div/0!', Workbook()))
