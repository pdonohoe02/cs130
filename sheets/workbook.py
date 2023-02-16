'''
This file contains the bulk of the spreadsheet engine, which allows for the
basic functions of spreadsheets (creating workbooks, creating and deleting
sheets, populating cells, and calculating formulas). Currently, the engine
handles both string and integers in the cells.
'''

from typing import List, Optional, Tuple, TextIO, Any
from lark_impl import parse_contents
from lark import Token
import re
import decimal
from copy import deepcopy
from queue import PriorityQueue
import json
import lark

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
        self.parser = lark.Lark.open('sheets/formulas.lark', start='formula')

        # dictionary of sheets mapping name to Sheet object
        self.sheets = {}

        # maps lower case names to case-sensitive name
        self.sheet_names = {}

        # maps cell to cells that depend on it
        self.forward_graph = {}

        # maps cell to cells that it depends on
        self.backward_graph = {}

        # maps sheet that does not exist to all cells that are referenced from
        # other sheets in that sheet
        self.notify_functions = []
        self.test_notify_cells = {}

    def num_sheets(self) -> int:
        '''
        Gets the number of sheets in a workbook.

        Returns:
            int: the number of sheets
        '''
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

        if sheet_name.lower() in self.forward_graph:
            for cell in self.forward_graph[sheet_name.lower()]:
                self.update_workbook(sheet_name.lower(), cell)

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
        # first we need to handle all refereneces in and out of the sheet
        sheet_name = sheet_name.lower()
        if sheet_name in self.sheets:
            update_cell = []
            if sheet_name in self.forward_graph:
                for cell_key in self.forward_graph[sheet_name].keys():
                    for cell in self.forward_graph[sheet_name][cell_key]:
                        update_cell.append(cell)

            del self.sheets[sheet_name]
            del self.sheet_names[sheet_name]
            for v in update_cell:
                self.update_workbook(v[0], v[1])
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
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet name not found.")

        return self.sheets[sheet_name.lower()].get_extent()

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
                if (v[0] in self.forward_graph and
                   v[1] in self.forward_graph[v[0]]):
                    for u in self.forward_graph[v[0]][v[1]]:
                        if u not in visited:
                            stack.append(u)
                            on_stack[u] = None
                            stack_cpy.append(u)
                        elif u in on_stack:
                            low[v] = min(low[v], disc_time[u])
            else:  # Leaving the node
                if low[v] == disc_time[v]:
                    temp = -1
                    scc = []
                    while temp != v:
                        temp = stack_cpy.pop()
                        scc.append(temp)
                    sccs.append(scc)
                k = stack.pop()
                if k in on_stack:
                    del on_stack[k]
                topo_sort.append(k)
            cycles = []
            for i in sccs:
                if len(i) > 1:
                    cycles.append(i)
        return (cycles, topo_sort[::-1])

    def update_cell_value(self, sheetname, location):
        pass

    def update_workbook(self, sheet_name: str, location: str,
                        notify_base_cell=False):
        '''
        Helper method that updates the workbook after a change is made.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): the location of a cell
        '''
        cycles, topo_sort = self.tarjan_iter(sheet_name, location)
        for cycle in cycles:
            for v in cycle:
                if v[0] not in self.sheet_names:
                    continue
                detail = 'Cell is part of circular reference.'
                contents = self.get_cell_contents(v[0], v[1])
                circ_ref = CellError(CellErrorType.CIRCULAR_REFERENCE, detail)
                self.sheets[v[0].lower()].set_cell_value(
                    v[1], contents, circ_ref)

        if (sheet_name in self.forward_graph and
           sheet_name in self.sheet_names and
           location in self.forward_graph[sheet_name] and
           (sheet_name, location) in self.forward_graph[sheet_name][location]):
            detail = 'Cell is part of circular reference.'
            contents = self.get_cell_contents(sheet_name, location)
            circ_ref = CellError(CellErrorType.CIRCULAR_REFERENCE, detail)
            self.sheets[sheet_name].set_cell_value(
                location, contents, circ_ref)

        notify_cells = []
        for v in topo_sort:
            if v[0] not in self.sheet_names:
                continue
            old_value = self.get_cell_value(v[0], v[1])
            contents = self.get_cell_contents(v[0], v[1]) # TODO: We need a function that handes this 
            # If contents are not new, then why are we 
            self.internal_set_cell_contents(v[0], v[1], contents, is_new=False)
            #self.recalculate_contents(v[0], v[1])
            if (self.get_cell_value(v[0], v[1]) != old_value or
               (v == (sheet_name, location) and notify_base_cell)):
                notify_cells.append((self.sheet_names[v[0]], v[1].upper()))

        for func in self.notify_functions:
            # Note that the following try except block is bad coding practice.
            # This is because we want the notify function to ignore ALL errors
            # or exceptions that may be thrown so that the next notify function
            # is still able to receive notifications.
            # pylint: disable=bare-except
            try:
                func(self, notify_cells)
                self.test_notify_cells[str(func)] = notify_cells
            except:
                continue

    def is_string_float(self, val):
        '''
        Helper method that checks if a string is a float.

        Parameters:
            val (str): the string to be checked

        Returns:
            bool: True if string is float,
                  False otherwise
        '''
        return re.match(r'^[-+]?\d*(?:\.\d+)$', val) is not None

    def is_string_digit(self, val):
        '''
        Helper method that checks if a string is a number.

        Parameters:
            val (str): the string to be checked

        Returns:
            bool: True if string is a number,
                  False otherwise
        '''
        return re.match('^[-+]?[0-9]+$', val) is not None

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

    def calculate_contents(self, sheet_name, contents: Optional[str], old_tree=None):
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
            value, tree = parse_contents(self.parser, sheet_name, contents, self, old_tree)
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
            elif self.is_string_digit(value):
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
        sheet_name_dict = {'QUOTED_SHEET_NAMES': [], 'SHEET_NAMES': []}
        while stack:
            while_sheet_name = sheet_name
            node = stack.pop()
            if isinstance(node, Token):
                continue
            elif node.data == 'cell':
                temp_sheet_name = None
                if node.children[0].type == 'SHEET_NAME':
                    temp_sheet_name = node.children[0].value
                    cell = node.children[1].value
                    sheet_name_dict['SHEET_NAMES'].append(temp_sheet_name)
                elif node.children[0].type == 'QUOTED_SHEET_NAME':
                    temp_sheet_name = node.children[0].value[1:-1]
                    cell = node.children[1].value
                    sheet_name_dict['QUOTED_SHEET_NAMES'].append(
                        node.children[0].value)
                else:
                    cell = node.children[0].value

                if temp_sheet_name is not None:
                    while_sheet_name = temp_sheet_name
                cell_refs.append((while_sheet_name.lower(), cell.lower()))
            else:
                for i in node.children:
                    stack.append(i)

        return cell_refs, sheet_name_dict

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

        old_value = self.get_cell_value(sheet_name, location)
        # TODO: Is the tree BUUUSSSSINN
        
        old_tree = self.sheets[sheet_name].get_cell_tree(location)
        if is_new:
            old_tree = None
        contents, value, tree = self.calculate_contents(sheet_name, contents, old_tree)

        if tree is None:
            self.sheets[sheet_name].set_cell_value(location, contents, value)

        if tree is not None:
            inherit_cells, sheet_name_dict = self.tree_dfs(tree, sheet_name)
            self.sheets[sheet_name].set_cell_value(location, contents, value, tree, sheet_name_dict)
            
            for i in inherit_cells:
                curr_name = i[0].lower()
                curr_loc = i[1].lower()
                if curr_name in self.forward_graph:
                    if curr_loc in self.forward_graph[curr_name]:
                        if ((sheet_name, location) not in self.forward_graph[curr_name][curr_loc]):
                            self.forward_graph[curr_name][curr_loc].append((sheet_name, location))
                    else:
                        self.forward_graph[curr_name][curr_loc] = [(sheet_name, location)]
                else:
                    self.forward_graph[curr_name] = {curr_loc: [(sheet_name, location)]}

            if sheet_name in self.backward_graph:
                self.backward_graph[sheet_name][location] = inherit_cells
            else:
                self.backward_graph[sheet_name] = {location: inherit_cells}

        if is_new:
            if old_value != value:
                self.update_workbook(sheet_name, location, True)
            else:
                self.update_workbook(sheet_name, location)

    def recalculate_contents(self, sheet_name, location):
        '''
        Recalculating and setting cell contents for the cells that do not need
        the formula itself to be re-parsed.
        '''
        location = location.lower()
        sheet_name = sheet_name.lower()

        contents = self.get_cell_contents(sheet_name, location)

        #old_value = self.get_cell_value(sheet_name, location)
        old_tree = self.sheets[sheet_name].get_cell_tree(location)
        contents, value, tree = self.calculate_contents(sheet_name, contents, old_tree)

        if tree is None:
            self.sheets[sheet_name].set_cell_value(location, contents, value)
        else:
            _, sheet_name_dict = self.tree_dfs(tree, sheet_name)
            self.sheets[sheet_name].set_cell_value(
                location, contents, value, tree, sheet_name_dict)
                

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

    @staticmethod
    def load_workbook(fp: TextIO):
        '''
        Loads a workbook from a text file or file-like object in JSON format.

        If the contents of the input cannot be parsed by the Python json
        module then a json.JSONDecodeError is raised.
        If an IO read error occurs (unlikely but possible), any raised
        exception propagates through.

        If any expected value in the input JSON is missing (e.g. a sheet
        object doesn't have the "cell-contents" key), a KeyError is raised.

        If any expected value in the input JSON is not of the proper type
        (e.g. an object instead of a list, or a number instead of a string),
        a TypeError is raised.

        Parameters:
            fp (TextIO): the already opened json file to load workbook from

        Returns:
            Workbook: the new Workbook instance loaded from the file
        '''
        # json.load(fp) outputs a dictionary with one key 'sheets'
        try:
            # list of dictionaries w/keys 'name' and 'cell-contents'
            sheets_lst = json.load(fp)['sheets']
            wb = Workbook()
            for sheet_dict in sheets_lst:
                name = sheet_dict['name']
                wb.new_sheet(name)
                for cell_loc in sheet_dict['cell-contents'].keys():
                    wb.set_cell_contents(
                        name, cell_loc, sheet_dict['cell-contents'][cell_loc])
            return wb
        except KeyError:
            raise KeyError('JSON missing expected values.')
        except IOError as e:
            raise e
        except (TypeError, AttributeError):
            raise TypeError('JSON contains values with unexpected types.')

    def save_workbook(self, fp: TextIO) -> None:
        '''
        Saves a workbook to a text file or file-like object in JSON format.

        If an IO write error occurs (unlikely but possible), any raised
        exception propagates through.

        Parameters:
            fp (TextIO): the already opened json file to load workbook from
        '''
        wb_dict = {}
        sheets_lst = []
        for (sheet_name, sheet) in self.sheets.items():
            sheet_dict = {}
            contents_dict = {}
            for (cell_loc, content_value) in sheet.cells.items():
                contents_dict[cell_loc.upper()] = content_value['contents']
            sheet_dict['name'] = self.sheet_names[sheet_name]
            sheet_dict['cell-contents'] = contents_dict
            sheets_lst.append(sheet_dict)
        wb_dict['sheets'] = sheets_lst
        fp.write(json.dumps(wb_dict, indent=4))

    def notify_cells_changed(self, notify_function) -> None:
        '''
        Requests that all changes to cell values in the workbook are reported
        to the specified notify_function. The values passed to the notify
        function are the workbook, and an iterable of 2-tuples of strings,
        of the form ([sheet name], [cell location]). The notify_function is
        expected not to return any value; any return-value will be ignored.

        Multiple notification functions may be registered on the workbook;
        functions will be called in the order that they are registered.

        A given notification function may be registered more than once; it
        will receive each notification as many times as it was registered.

        If the notify_function raises an exception while handling a
        notification, this will not affect workbook calculation updates or
        calls to other notification functions.

        A notification function is expected to not mutate the workbook or
        iterable that it is passed to it.  If a notification function violates
        this requirement, the behavior is undefined.

        Parameters:
            notify_function (func): the notify function to report new cell
                                    changes ([sheet name], [cell location]) to
        '''
        self.notify_functions.append(notify_function)

    def rename_sheet(self, sheet_name: str, new_sheet_name: str) -> None:
        '''
        Renames the specified sheet to the new sheet name. All cell formulas
        that referenced the original sheet name are updated to reference the
        new sheet name (using the same case as the new sheet name, and
        single-quotes iff [if and only if] necessary).

        The sheet_name match is case-insensitive; the text must match but the
        case does not have to.

        As with new_sheet(), the case of the new_sheet_name is preserved by
        the workbook.

        If the sheet_name is not found, a KeyError is raised.

        If the new_sheet_name is an empty string or is otherwise invalid, a
        ValueError is raised.

        Parameters:
            sheet_name (str): the old sheet name
            new_sheet_name (str): the name to rename the old name
        '''
        if sheet_name.lower() not in self.sheets:
            raise KeyError('Sheet name not found.')
        if not self.is_valid_sheet_name(new_sheet_name):
            raise ValueError('Invalid new spreadsheet name.')

        sheet_name = sheet_name.lower()

        new_sheet_name_lower = new_sheet_name.lower()

        index = 0
        for k in self.sheets:
            if sheet_name == k:
                break
            index += 1

        # updating cell contents/references to new sheet name
        if sheet_name in self.forward_graph:
            for start_cell in self.forward_graph[sheet_name].keys():
                for cell_tuple in self.forward_graph[sheet_name][start_cell]:
                    if cell_tuple[1] not in self.sheets[cell_tuple[0]].cells:
                        continue
                    self.sheets[cell_tuple[0]].change_contents_sheet_ref(
                        cell_tuple[1],
                        sheet_name,
                        new_sheet_name)

        # updating backward graph
        if sheet_name in self.backward_graph:
            for start_cell in self.backward_graph[sheet_name].keys():
                for cell_tuple in self.backward_graph[sheet_name][start_cell]:
                    forward_cells = self.forward_graph[cell_tuple[0]]
                    if (cell_tuple[0] in self.forward_graph and
                       cell_tuple[1] in forward_cells):
                        for i in range(len(forward_cells[cell_tuple[1]])):
                            if forward_cells[cell_tuple[1]][i] == (sheet_name,
                                                                   start_cell):
                                forward_cells[cell_tuple[1]][i] = (
                                    new_sheet_name_lower, start_cell)
            del self.backward_graph[sheet_name]
        self.sheets[new_sheet_name_lower] = self.sheets[sheet_name]
        del self.sheets[sheet_name]
        self.sheet_names[new_sheet_name_lower] = new_sheet_name
        del self.sheet_names[sheet_name]

        # updating forward graph
        self.move_sheet(new_sheet_name_lower, index)
        if sheet_name in self.forward_graph:
            if new_sheet_name_lower not in self.forward_graph:
                self.forward_graph[new_sheet_name_lower] = \
                    self.forward_graph[sheet_name]
            else:
                new_forward_graph = self.forward_graph[new_sheet_name_lower]
                for (key, value) in self.forward_graph[sheet_name].items():
                    if key in new_forward_graph:
                        for i in value:
                            if i not in new_forward_graph[key]:
                                new_forward_graph[key].append(i)
                    else:
                        self.forward_graph[new_sheet_name_lower][key] = value
            del self.forward_graph[sheet_name]

        #for cell in self.sheets[new_sheet_name_lower].cells:
        #    self.set_cell_contents(new_sheet_name_lower, cell, self.get_cell_contents(new_sheet_name_lower, cell))
        if new_sheet_name_lower in self.forward_graph:
            for cell in self.forward_graph[new_sheet_name_lower]:                
                self.update_workbook(new_sheet_name_lower, cell)

    def move_sheet(self, sheet_name: str, index: int) -> None:
        '''
        Moves the specified sheet to the specified index in the workbook's
        ordered sequence of sheets. The index can range from 0 to
        workbook.num_sheets() - 1. The index is interpreted as if the
        specified sheet were removed from the list of sheets, and then
        re-inserted at the specified index.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        If the specified sheet name is not found, a KeyError is raised.

        If the index is outside the valid range, an IndexError is raised.

        Parameters:
            sheet_name (str): the old sheet name
            index (int): the index in the workbook to move the sheet to
        '''
        sheet_name = sheet_name.lower()
        if sheet_name not in self.sheets:
            raise KeyError('Sheet name not found.')
        elif index < 0 or index >= len(self.sheets.keys()):
            raise IndexError('Index outside of valid range.')

        new_sheets = {}
        new_sheet_names = {}
        counter = -1
        for key in self.sheets:
            counter += 1
            if key == sheet_name and counter != index:
                continue
            if counter == index:
                new_sheets[sheet_name] = self.sheets[sheet_name]
                new_sheet_names[sheet_name] = self.sheet_names[sheet_name]
            new_sheets[key] = self.sheets[key]
            new_sheet_names[key] = self.sheet_names[key]
        self.sheets = new_sheets
        self.sheet_names = new_sheet_names

    def copy_sheet_helper(self, sheet, new_sheet):
        '''
        Helper method for copy_sheet. Makes deep copies of a sheet.
        '''
        new_cells = {}
        new_extent_row = PriorityQueue()
        new_extent_col = PriorityQueue()

        for key in sheet.cells.keys():
            new_cells[key] = {'contents': sheet.cells[key]['contents'],
                              'value': sheet.cells[key]['value'],
                              'tree': None,
                              'sheet_name_dict': sheet.cells[key]['sheet_name_dict']
                              }
        new_extent_row.queue = deepcopy(sheet.extent_row.queue)
        new_extent_col.queue = deepcopy(sheet.extent_col.queue)
        new_sheet.cells = new_cells
        new_sheet.extent_row = new_extent_row
        new_sheet.extent_col = new_extent_col
        return new_sheet

    def copy_sheet(self, sheet_name: str) -> Tuple[int, str]:
        '''
        Makes a copy of the specified sheet, storing the copy at the end of
        the workbook's sequence of sheets. The copy's name is generated by
        appending "_1", "_2", ... to the original sheet's name (preserving the
        original sheet name's case), incrementing the number until a unique
        name is found.  As usual, "uniqueness" is determined in a
        case-insensitive manner.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        The copy should be added to the end of the sequence of sheets in the
        workbook.  Like new_sheet(), this function returns a tuple with two
        elements:  (0-based index of copy in workbook, copy sheet name).  This
        allows the function to report the new sheet's name and index in the
        sequence of sheets.

        If the specified sheet name is not found, a KeyError is raised.

        Parameters:
            sheet_name (str): the name of the sheet to be copied

        Returns:
            tuple: (0-based index of copy in workbook, copy sheet name)
        '''
        sheet_name = sheet_name.lower()
        if sheet_name not in self.sheets:
            raise KeyError('Sheet name not found.')

        counter = 1
        curr = ''
        while True:
            curr = sheet_name + '_' + str(counter)
            if curr not in self.sheets:
                break
            counter += 1

        case_sheet_name = self.sheet_names[sheet_name]
        self.sheet_names[curr] = case_sheet_name + '_' + str(counter)
        self.sheets[curr] = self.copy_sheet_helper(self.sheets[sheet_name],
                                                   Sheet())
        # for every cell in forward dict we need to calculate contents
        for cell in self.sheets[curr].cells.keys():
            self.internal_set_cell_contents(
                curr, cell, self.sheets[curr].get_cell_contents(cell), False)
        notify_cells = []
        for cell in self.sheets[curr].cells:
            notify_cells.append((self.sheet_names[curr], cell.upper()))
        if curr.lower() in self.forward_graph:
            for cell in self.forward_graph[curr.lower()]:
                self.update_workbook(curr.lower(), cell)

        for func in self.notify_functions:
            try:
                for cell in notify_cells:
                    if cell not in self.test_notify_cells[str(func)]:
                        self.test_notify_cells[str(func)].append(cell)
                func(self, self.test_notify_cells[str(func)])
            except:
                continue
        return (len(self.sheets) - 1, case_sheet_name + '_' + str(counter))
