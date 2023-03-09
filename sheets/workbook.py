'''
This file contains the bulk of the spreadsheet engine, which allows for the
basic functions of spreadsheets (creating workbooks, creating and deleting
sheets, populating cells, and calculating formulas). Currently, the engine
handles both string and integers in the cells.
'''

from typing import List, Optional, Tuple, TextIO, Any
import re
import decimal
import json
import string
import lark
from lark_impl import parse_contents
from row import Row
from lark import Token
from functools import lru_cache, cmp_to_key

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
        self.parsed_trees = {}
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
        self.notify_cells_master = set()

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

    def tarjan_iter(self, sheet_name, location, graph):
        '''
        Helper method that implements an iterative form of Tarjan's algorithm.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): the location of a cell

        Returns:
            (list, list): a tuple of a list of cycles and a list of
                          dependencies
        '''
        #print(graph)
        stack = [(sheet_name, location)]
        on_stack = {(sheet_name, location): None}
        visited = {}
        #backtrack = {}
        topo_sort = []
        sccs = []
        disc_time = {}
        low = {}
        stack_cpy = [(sheet_name, location)]
        while stack:
            #print(stack)
            #print(low)
            v = stack[-1]
            #
            if v not in visited:
                visited[v] = None
                disc_time[v] = len(stack) - 1
                low[v] = len(stack) - 1
                if (v[0] in graph and
                   v[1] in graph[v[0]]):
                    for u in graph[v[0]][v[1]]:
                        if u not in visited:
                            stack.append(u)
                            on_stack[u] = None
                            stack_cpy.append(u)
                        elif u in on_stack:
                            low[v] = min(low[v], low[u])
            else:  # Leaving the node
                if (v[0] in graph and
                   v[1] in graph[v[0]]):
                    for u in graph[v[0]][v[1]]:
                        low[v] = min(low[v], low[u])
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

    def topo_sort(self, sheet_name, location, graph):
        '''
        Helper method that implements an iterative form of Tarjan's algorithm.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): the location of a cell

        Returns:
            (list, list): a tuple of a list of cycles and a list of
                          dependencies
        '''
        #print(graph)
        stack = [(sheet_name, location)]
        #on_stack = {(sheet_name, location): None}
        visited = set()
        topo_sort = []

        while stack:
            v = stack[-1]
            if v not in visited:
                visited.add(v)
                if (v[0] in graph and
                   v[1] in graph[v[0]]):
                    for u in graph[v[0]][v[1]]:
                        if u not in visited:
                            stack.append(u)
            else:  # Leaving the node
                k = stack.pop()
                topo_sort.append(k)

        return (topo_sort[::-1])

    def update_notify_cells_master(self, notify_cells):
        for cell in notify_cells:
            if cell not in self.notify_cells_master:
                self.notify_cells_master.add(cell)
    
    def send_notify_cells_to_functions(self):
        for func in self.notify_functions:
            try:
                func(self, self.notify_cells_master)
            # Note that the following try except block is bad coding practice.
            # This is because we want the notify function to ignore ALL errors
            # or exceptions that may be thrown so that the next notify function
            # is still able to receive notifications.
            # pylint: disable=bare-except
            except:
                continue

    def update_workbook(self, sheet_name: str, location: str,
                        notify_base_cell=False):
        '''
        Helper method that updates the workbook after a change is made.

        Parameters:
            sheet_name (str): the name of a sheet
            location (str): the location of a cell
        '''

        #topo_sort = self.topo_sort(sheet_name, location, self.forward_graph)
        
        cycles, topo_sort = self.tarjan_iter(sheet_name, location, self.forward_graph)
        #print(cycles)
        cycle_cells = set()
        for cycle in cycles:
            for v in cycle:
                if v[0] not in self.sheet_names:
                    continue
                detail = 'Cell is part of circular reference.'
                value = self.get_cell_value(v[0], v[1])
                if not (isinstance(value, CellError) and value.get_type() == CellErrorType.BAD_NAME):
                    contents = self.get_cell_contents(v[0], v[1])
                    cycle_cells.add(v)
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
            old_value = self.sheets[v[0].lower()].get_cell_value(v[1])
            #if v not in cycle_cells:
            contents = self.get_cell_contents(v[0], v[1])
            if v not in cycle_cells:
                self.internal_set_cell_contents(v[0], v[1], contents, is_new=False, internal_call=True)
            else:
                self.internal_set_cell_contents(v[0], v[1], contents, is_new=False, internal_call=True, in_scc = True)
            new_value = self.sheets[v[0].lower()].get_cell_value(v[1])
            if isinstance(old_value, CellError) and isinstance(new_value, CellError):
                if old_value.get_type() != new_value.get_type() or (v == (sheet_name, location) and notify_base_cell):
                    notify_cells.append((self.sheet_names[v[0]], v[1].upper()))
            elif new_value != old_value or (v == (sheet_name, location) and notify_base_cell):
                notify_cells.append((self.sheet_names[v[0]], v[1].upper()))

        self.update_notify_cells_master(notify_cells)

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
    
    def check_str_bool(self, value):
        value = str(value)
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        else:
            return value

    def calculate_contents(self, sheet_name, contents: Optional[str], old_tree=None, in_scc= False):
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
            return None, None, None, None
        contents = contents.strip()
        value = contents
        if contents[0] == '=':
            value, tree, calculated_refs = parse_contents(self.parser, self.parsed_trees, sheet_name, contents, self, old_tree, in_scc)
            if isinstance(value, decimal.Decimal) and '.' in str(value):
                temp = str(value).rstrip('0').rstrip('.')
                value = decimal.Decimal(temp)
            return contents, value, tree, calculated_refs
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
            else:
                value = self.check_str_bool(value)

        return contents, value, None, None
    
    @lru_cache()
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

        match = re.match(r"([a-z]+)([1-9][0-9]*)$", location, re.I)
        if not match:
            return False

        row, col = match.groups()
        if len(row) > 4 or len(col) > 4:
            return False

        return True

    @lru_cache()
    def tree_dfs(self, tree, sheet_name, calculated_refs):
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
        calculated_refs = list(calculated_refs)
        #print(calculated_refs)
        stack = [tree]
        cell_refs = []
        sheet_name_dict = {'QUOTED_SHEET_NAMES': [], 'SHEET_NAMES': [], 'CELLS': []}
        while stack:
            while_sheet_name = sheet_name
            node = stack.pop()
            if isinstance(node, Token):
                continue
            if node.data == 'cell':
                temp_sheet_name = None
                #print(node)
                if node.children[0].type == 'SHEET_NAME':
                    temp_sheet_name = node.children[0].value
                    cell = node.children[1].value
                    if node not in calculated_refs:
                        sheet_name_dict['CELLS'].append((cell, temp_sheet_name))
                        sheet_name_dict['SHEET_NAMES'].append(temp_sheet_name)
                elif node.children[0].type == 'QUOTED_SHEET_NAME':
                    temp_sheet_name = node.children[0].value[1:-1]
                    cell = node.children[1].value
                    if node not in calculated_refs:
                        sheet_name_dict['CELLS'].append((cell, node.children[0].value))
                        sheet_name_dict['QUOTED_SHEET_NAMES'].append(
                            node.children[0].value)
                else:
                    cell = node.children[0].value
                    
                    if node not in calculated_refs:
                        sheet_name_dict['CELLS'].append((cell, None))

                if temp_sheet_name is not None:
                    while_sheet_name = temp_sheet_name
                cell_refs.append((while_sheet_name.lower(), cell.lower()))
            else:
                for i in node.children:
                    stack.append(i)
        #print(sheet_name_dict)
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
        #print(contents)
        return self.internal_set_cell_contents(sheet_name, location, contents,
                                               is_new=True, internal_call=False)

    def internal_set_cell_contents(self, sheet_name: str, location: str,
                                   contents: Optional[str],
                                   is_new: Optional[bool],
                                   internal_call: Optional[bool],
                                   in_scc = False) -> None:
        '''
        Internal set_cell_contents method.
        '''
        location = location.lower()
        sheet_name = sheet_name.lower()
        if sheet_name not in self.sheets:
            raise KeyError("Sheet name not found.")
        if not self.is_valid_cell_location(location):
            raise ValueError("Invalid cell location.")

        old_value = self.sheets[sheet_name.lower()].get_cell_value(location)
        
        old_tree = self.sheets[sheet_name].get_cell_tree(location)
        if is_new:
            old_tree = None
            if not internal_call:
                self.notify_cells_master = set()
                    
        contents, value, tree, calculated_refs  = self.calculate_contents(sheet_name, contents, old_tree, in_scc)
        if tree is None:
            self.sheets[sheet_name].set_cell_value(location, contents, value)
            if contents is None:
                return

        if tree is not None:
            inherit_cells, sheet_name_dict = self.tree_dfs(tree, sheet_name, tuple(calculated_refs))
            self.sheets[sheet_name].set_cell_value(location, contents, value, tree, sheet_name_dict)
            if sheet_name in self.backward_graph:
                if location in self.backward_graph[sheet_name]:
                    for c in self.backward_graph[sheet_name][location]:
                        if c[0] in self.forward_graph and c[1] in self.forward_graph[c[0]]:
                            if (sheet_name, location) in set(self.forward_graph[c[0]][c[1]]):
                                self.forward_graph[c[0]][c[1]].remove((sheet_name, location))
            #     self.backward_graph[sheet_name][location] = []
            
            for i in inherit_cells:
                curr_name = i[0].lower()
                curr_loc = i[1].lower()
                if curr_name in self.forward_graph:
                    if curr_loc in self.forward_graph[curr_name]:
                        if (sheet_name, location) not in self.forward_graph[curr_name][curr_loc]:
                            self.forward_graph[curr_name][curr_loc].append((sheet_name, location))
                    else:
                        self.forward_graph[curr_name][curr_loc] = [(sheet_name, location)]
                        
                else:
                    self.forward_graph[curr_name] = {curr_loc: [(sheet_name, location)]}

            if sheet_name in self.backward_graph:
                self.backward_graph[sheet_name][location] = inherit_cells
            else:
                self.backward_graph[sheet_name] = {location: inherit_cells}
        else:
            if sheet_name in self.backward_graph:
                if location in self.backward_graph[sheet_name]:
                    for c in self.backward_graph[sheet_name][location]:
                        if c[0] in self.forward_graph and c[1] in self.forward_graph[c[0]]:
                            if (sheet_name, location) in set(self.forward_graph[c[0]][c[1]]):
                                self.forward_graph[c[0]][c[1]].remove((sheet_name, location))
                    del self.backward_graph[sheet_name][location]
        if is_new:
            if isinstance(old_value, CellError) and isinstance(value, CellError):
                if old_value.get_type() == value.get_type():
                    self.update_workbook(sheet_name, location)
                else:
                    self.update_workbook(sheet_name, location, True)
            elif old_value != value:
                self.update_workbook(sheet_name, location, True)
            else:
                self.update_workbook(sheet_name, location)

        if not internal_call:
            self.send_notify_cells_to_functions()

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
        if self.sheets[sheet_name.lower()].get_cell_uncalc_status():
            self.internal_set_cell_contents(sheet_name, location, self.cells[sheet_name])
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

    # @lru_cache()
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

        self.notify_cells_master = set()

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
                        self,
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

        if new_sheet_name_lower in self.forward_graph:
            for cell in self.forward_graph[new_sheet_name_lower]:
                self.update_workbook(new_sheet_name_lower, cell)

        self.send_notify_cells_to_functions()

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
        if index < 0 or index >= len(self.sheets.keys()):
            raise IndexError('Index outside of valid range.')

        new_sheets = {}
        new_sheet_names = {}
        
        sheets_keys = list(self.sheets.keys())
        sheets_keys.reverse()

        sheets_keys.remove(sheet_name)

        counter = 0
        while counter < len(self.sheets.keys()):
            if counter == index:
                new_sheets[sheet_name] = self.sheets[sheet_name]
                new_sheet_names[sheet_name] = self.sheet_names[sheet_name]
            else:
                temp_name = sheets_keys.pop()
                new_sheets[temp_name] = self.sheets[temp_name]
                new_sheet_names[temp_name] = self.sheet_names[temp_name]
            counter += 1

        self.sheets = new_sheets
        self.sheet_names = new_sheet_names

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

        self.notify_cells_master = set()

        counter = 1
        curr = ''
        while True:
            curr = sheet_name + '_' + str(counter)
            if curr not in self.sheets:
                break
            counter += 1

        case_sheet_name = self.sheet_names[sheet_name]
        curr_case = case_sheet_name + '_' + str(counter)

        self.new_sheet(curr_case)
        for (cell_location, cell_info) in self.sheets[sheet_name].cells.items():
            self.cells[curr].set_cell_value(cell_location, cell_info['contents'], value=None, uncalc_value=True)
            #self.internal_set_cell_contents(curr, cell_location, cell_info['contents'], is_new=True, internal_call=True)

        notify_cells = []
        for cell in self.sheets[curr].cells:
            notify_cells.append((self.sheet_names[curr], cell.upper()))

        if curr in self.forward_graph:
            for cell in self.forward_graph[curr]:
                self.update_workbook(curr, cell)

        self.update_notify_cells_master(notify_cells)
        self.send_notify_cells_to_functions()
    
        return (len(self.sheets) - 1, case_sheet_name + '_' + str(counter))

    def num_to_col(self, num):
        res = ''
        while num > 0:
            num, remainder = divmod (num - 1, 26)
            res = chr(remainder + ord('a')) + res
        return res

    def col_to_num(self, col: str):
        num = 0
        for letter in col:
            if letter in string.ascii_letters:
                num = num * 26 + (ord(letter.upper()) - ord('A')) + 1
        return num

    def parse_cell_ref(self, cell_ref):
        match = re.match(r"([a-z]+)([1-9][0-9]*)$", cell_ref, re.I)
        if not match:
            return False
            
        col, row = match.groups()
        return col, row
    
    def find_top_left_bot_right_corners(self, start_location, end_location):
        start_col, start_row = self.parse_cell_ref(start_location)
        end_col, end_row = self.parse_cell_ref(end_location)
        start_row, end_row = int(start_row), int(end_row)
        top_row, bot_row = min(start_row, end_row), max(start_row, end_row)
        
        start_col_num, end_col_num = self.col_to_num(start_col), self.col_to_num(end_col)
        left_col_num, right_col_num = min(start_col_num, end_col_num), max(start_col_num, end_col_num)

        top_left = self.num_to_col(left_col_num) + str(top_row)
        bot_right = self.num_to_col(right_col_num) + str(bot_row)
        return top_left, bot_right

    def move_copy_helper(self, sheet_name: str, start_location: str,
            end_location: str, to_location: str, to_sheet: Optional[str] = None, is_move = False):
        
        self.notify_cells_master = set()
        
        if to_sheet is None:
            to_sheet = sheet_name
            
        sheet_name = sheet_name.lower()
        start_location = start_location.lower()
        end_location = end_location.lower()
        to_location = to_location.lower()
        to_sheet = to_sheet.lower()
        
        if sheet_name not in self.sheets or to_sheet not in self.sheets:
            raise KeyError("Sheet name not found.")
        if (not self.is_valid_cell_location(start_location) or 
                not self.is_valid_cell_location(end_location) or
                not self.is_valid_cell_location(to_location)):
            raise ValueError("Invalid cell location.")

        # finding scope of new cell location rectangle
        top_left, bot_right = self.find_top_left_bot_right_corners(start_location, end_location)

        top_left_col, top_left_row = self.parse_cell_ref(top_left)
        bot_right_col, bot_right_row = self.parse_cell_ref(bot_right)
        to_col, to_row = self.parse_cell_ref(to_location)

        col_diff = self.col_to_num(to_col) - self.col_to_num(top_left_col)
        final_col = self.col_to_num(bot_right_col) + col_diff

        row_diff = int(to_row) - int(top_left_row)
        final_row = int(bot_right_row) + row_diff
        if final_col > self.col_to_num('zzzz') or final_row > 9999:
            raise ValueError("Cells are out of bounds.")
        
        # map from initial cell to final cell
        change_cells = {}

        notify_cells = []
        for row in range(int(top_left_row), int(bot_right_row) + 1):
            for col_num in range(self.col_to_num(top_left_col), self.col_to_num(bot_right_col) + 1):
                cell_location = self.num_to_col(col_num) + str(row)
                if cell_location in self.sheets[sheet_name].cells:
                    change_cells[(col_num, row)] = self.sheets[sheet_name].cells[cell_location]
                    if is_move:
                        notify_cells.append((self.sheet_names[sheet_name], cell_location.upper()))
                        del self.sheets[sheet_name].cells[cell_location]
                else:
                    change_cells[(col_num, row)] = None

        for ((col_num, row), cell_dict) in change_cells.items():
            new_contents = self.sheets[sheet_name].update_cell_references(self, cell_dict, col_diff, row_diff)
            new_col = self.num_to_col(col_num + col_diff)
            new_row = row + row_diff
            new_ref = new_col + str(new_row)
            prev_val = self.get_cell_value(to_sheet, new_ref)
            self.set_cell_contents(to_sheet, new_ref, new_contents)
            new_val = self.get_cell_value(to_sheet, new_ref)
            if not isinstance(prev_val, CellError):
                if prev_val != new_val:
                    notify_cells.append((self.sheet_names[to_sheet], new_ref.upper()))
            elif isinstance(new_val, CellError) and prev_val.get_type() != new_val.get_type():
                notify_cells.append((self.sheet_names[to_sheet], new_ref.upper()))

        self.update_notify_cells_master(notify_cells)
        self.send_notify_cells_to_functions()

    def move_cells(self, sheet_name: str, start_location: str,
            end_location: str, to_location: str, to_sheet: Optional[str] = None) -> None:
        '''
        Move cells from one location to another, possibly moving them to
        another sheet.  All formulas in the area being moved will also have
        all relative and mixed cell-references updated by the relative
        distance each formula is being copied.
        
        Cells in the source area (that are not also in the target area) will
        become empty due to the move operation.
        
        The start_location and end_location specify the corners of an area of
        cells in the sheet to be moved.  The to_location specifies the
        top-left corner of the target area to move the cells to.
        
        Both corners are included in the area being moved; for example,
        copying cells A1-A3 to B1 would be done by passing
        start_location="A1", end_location="A3", and to_location="B1".
        
        The start_location value does not necessarily have to be the top left
        corner of the area to move, nor does the end_location value have to be
        the bottom right corner of the area; they are simply two corners of
        the area to move.
        
        This function works correctly even when the destination area overlaps
        the source area.
        
        The sheet name matches are case-insensitive; the text must match but
        the case does not have to.
        
        If to_sheet is None then the cells are being moved to another
        location within the source sheet.
        
        If any specified sheet name is not found, a KeyError is raised.
        If any cell location is invalid, a ValueError is raised.
        
        If the target area would extend outside the valid area of the
        spreadsheet (i.e. beyond cell ZZZZ9999), a ValueError is raised, and
        no changes are made to the spreadsheet.
        
        If a formula being moved contains a relative or mixed cell-reference
        that will become invalid after updating the cell-reference, then the
        cell-reference is replaced with a #REF! error-literal in the formula.
        '''
        self.move_copy_helper(sheet_name, start_location, end_location, to_location, to_sheet, is_move=True)
        
    def copy_cells(self, sheet_name: str, start_location: str,
            end_location: str, to_location: str, to_sheet: Optional[str] = None) -> None:
        '''
        Copy cells from one location to another, possibly copying them to
        another sheet.  All formulas in the area being copied will also have
        all relative and mixed cell-references updated by the relative
        distance each formula is being copied.
        
        Cells in the source area (that are not also in the target area) are
        left unchanged by the copy operation.
        
        The start_location and end_location specify the corners of an area of
        cells in the sheet to be copied.  The to_location specifies the
        top-left corner of the target area to copy the cells to.
        
        Both corners are included in the area being copied; for example,
        copying cells A1-A3 to B1 would be done by passing
        start_location="A1", end_location="A3", and to_location="B1".
        
        The start_location value does not necessarily have to be the top left
        corner of the area to copy, nor does the end_location value have to be
        the bottom right corner of the area; they are simply two corners of
        the area to copy.
        
        This function works correctly even when the destination area overlaps
        the source area.
        
        The sheet name matches are case-insensitive; the text must match but
        the case does not have to.
        
        If to_sheet is None then the cells are being copied to another
        location within the source sheet.
        
        If any specified sheet name is not found, a KeyError is raised.
        If any cell location is invalid, a ValueError is raised.
        
        If the target area would extend outside the valid area of the
        spreadsheet (i.e. beyond cell ZZZZ9999), a ValueError is raised, and
        no changes are made to the spreadsheet.
        
        If a formula being copied contains a relative or mixed cell-reference
        that will become invalid after updating the cell-reference, then the
        cell-reference is replaced with a #REF! error-literal in the formula.
        '''
        self.move_copy_helper(sheet_name, start_location, end_location, to_location, to_sheet, is_move=False)
        
    def cmp_rows(self, x, y):
        x_cell_val = x.get_cell_to_compare()
        y_cell_val = y.get_cell_to_compare()

        if x_cell_val == y_cell_val: 
            return 0 
        if x_cell_val is None:
            return -1
        if y_cell_val is None:
            return 1
        if isinstance(x_cell_val, CellError) and isinstance(y_cell_val, CellError):
            x_error_type = x_cell_val.get_type().value
            y_error_type = y_cell_val.get_type().value
            if x_error_type == y_error_type:
                return 0
            if x_error_type < y_error_type:
                return -1
            return 1
        # only one value is a CellError
        if isinstance(x_cell_val, CellError):
            return -1
        if isinstance(y_cell_val, CellError):
            return -1

    def sort_region(self, sheet_name: str, start_location: str, end_location: str, sort_cols: List[int]):
        '''
        Sort the specified region of a spreadsheet with a stable sort, using
        the specified columns for the comparison.
        
        The sheet name match is case-insensitive; the text must match but the
        case does not have to.
        
        The start_location and end_location specify the corners of an area of
        cells in the sheet to be sorted.  Both corners are included in the
        area being sorted; for example, sorting the region including cells B3
        to J12 would be done by specifying start_location="B3" and
        end_location="J12".
        
        The start_location value does not necessarily have to be the top left
        corner of the area to sort, nor does the end_location value have to be
        the bottom right corner of the area; they are simply two corners of
        the area to sort.
        
        The sort_cols argument specifies one or more columns to sort on.  Each
        element in the list is the one-based index of a column in the region,
        with 1 being the leftmost column in the region.  A column's index in
        this list may be positive to sort in ascending order, or negative to
        sort in descending order.  For example, to sort the region B3..J12 on
        the first two columns, but with the second column in descending order,
        one would specify sort_cols=[1, -2].
        
        The sorting implementation is a stable sort:  if two rows compare as
        "equal" based on the sorting columns, then they will appear in the
        final result in the same order as they are at the start.
        
        If multiple columns are specified, the behavior is as one would
        expect:  the rows are ordered on the first column indicated in
        sort_cols; when multiple rows have the same value for the first
        column, they are then ordered on the second column indicated in
        sort_cols; and so forth.
        
        No column may be specified twice in sort_cols; e.g. [1, 2, 1] or
        [2, -2] are both invalid specifications.
        
        The sort_cols list may not be empty.  No index may be 0, or refer
        beyond the right side of the region to be sorted.
        
        If the specified sheet name is not found, a KeyError is raised.
        If any cell location is invalid, a ValueError is raised.
        If the sort_cols list is invalid in any way, a ValueError is raised.
        '''
        self.notify_cells_master = set()
        
        sheet_name = sheet_name.lower()
        start_location = start_location.lower()
        end_location = end_location.lower()
        
        if sheet_name not in self.sheets :
            raise KeyError("Sheet name not found.")
        if (not self.is_valid_cell_location(start_location) or 
                not self.is_valid_cell_location(end_location)):
            raise ValueError("Invalid cell location.")
        
        # finding scope of new cell location rectangle
        top_left, bot_right = self.find_top_left_bot_right_corners(start_location, end_location)

        top_left_col, top_left_row = self.parse_cell_ref(top_left)
        bot_right_col, bot_right_row = self.parse_cell_ref(bot_right)
        
        abs_sort_cols = [abs(col) for col in sort_cols]
        if (len(sort_cols) == 0 
                or len(sort_cols) != len(set(abs_sort_cols)) 
                or 0 in abs_sort_cols 
                or len(sort_cols) > bot_right_row - top_left_row + 1):
            raise ValueError("Invalid columns to be sorted on.")

        # start sorting
        row_lst = []
        cell_values = []
        num_top_left_col = self.col_to_num(top_left_col)
        num_bot_right_col = self.col_to_num(bot_right_col)
        for i in range(top_left_row, bot_right_row + 1):
            for j in range(num_top_left_col, num_bot_right_col + 1):
                curr_loc = f'{self.num_to_col(j)}{i}'
                cell_values.append(self.get_cell_value(sheet_name, curr_loc))
            row_lst.append(Row(cell_values, i))
        
        #sorted_rows = [i for i in range(top_left_row, bot_right_row + 1)]
        range_of_equals = [(0, bot_right_row - top_left_row)]
        
        sort_cols.reverse()
        len_cols = num_bot_right_col - num_top_left_col + 1
        is_reverse = False
        while sort_cols and range_of_equals != []:
            col = sort_cols.pop()
            # if col > 0:
            #     is_reverse = False
            #     if col > len_cols:
            #         pass
            # elif col < 0:
            #     is_reverse = True
            #     col = -col
            #     if col > len_cols:
            #         pass
            if abs(col) > len_cols:
                raise ValueError("Column out of bounds.")
            if col < 0:
                is_reverse = True

            # how are we going to do the sorting, we need to be able to sort the list
            for (start, end) in range_of_equals:
                row_lst[start:end] = sorted(row_lst[start:end], key=cmp_to_key(self.cmp_rows), reverse=is_reverse)
            # finding the ones that need to be resorted
            new_range_of_equals = []
            range_stack = []
            for (start, end) in range_of_equals:
                for i in range(start + 1, end + 1):
                    if self.cmp_rows(row_lst[i], row_lst[i - 1]) == 0:
                        row_lst[i - 1].increment_col()
                        if len(range_stack) == 0:
                            range_stack.append(i - 1)
                            range_stack.append(i)
                        else:
                            range_stack.append(i)
                    else:
                        new_range_of_equals.append((range_stack[0], range_stack[-1]))
                # CHECK IF CORRECT
                row_lst[end].increment_col()
                    #   range_stack.append(i)   
            range_of_equals = new_range_of_equals

        # FIX THE CELL CONTENTS

        
        

# testing delete later
wb = Workbook()
_, sheet1 = wb.new_sheet()

wb.set_cell_contents(sheet1, 'b1', '1')
#print(parse_contents(wb.parser, wb.parsed_trees, sheet1, '=ISERROR(b1 & 5)', wb))
#print(parse_contents(wb.parser, wb.parsed_trees, sheet1, '=isblank("a2")', wb))
