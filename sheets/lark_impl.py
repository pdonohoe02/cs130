'''
This file contains the lark parser for formulas.
'''
import re
import decimal

import lark
from lark import Tree
from lark.visitors import visit_children_decor
from functools import lru_cache
from copy import deepcopy
import string

from cellerror import CellErrorType, CellError
from version_file import version

class FormulaEvaluator(lark.visitors.Interpreter):
    '''
    This class is a helper class that evaluates formulas in cells.
    '''

    def __init__(self, sheet_name, workbook):
        '''
        Initializes a FormulaEvaluator.
        '''
        self.workbook = workbook
        self.sheet_name = sheet_name
        self.contains_func = False

    def convert_none_to_zero(self, value_zero, value_two):
        '''
        Converts none type to zero.
        '''
        if value_zero is None:
            value_zero = decimal.Decimal(0)
        if value_two is None:
            value_two = decimal.Decimal(0)
        return value_zero, value_two

    def is_string_float(self, val):
        '''
        Helper method to check if string can be interpreted as a float.
        '''
        return re.match(r'^-?\d+(?:\.\d+)$', val) is not None

    @lru_cache
    def convert_to_decimal(self, value):
        '''
        Converts a string to an integer if possible.
        '''
        if isinstance(value, str):
            value = value.strip()
            if self.is_string_float(value):
                # string is a float
                value = decimal.Decimal(value)
            elif value.isdigit():
                # string is an int
                value = decimal.Decimal(value)
            else:
                raise CellError(
                    CellErrorType.TYPE_ERROR,
                    'Incompatible types of values.')
        elif isinstance(value, bool):
            if value == True:
                value = decimal.Decimal(1)
            else:
                value = decimal.Decimal(0)
        return value

    def remove_dollar_sign(self, ref):
        return ref.replace('$', '')

    @visit_children_decor
    def cell(self, values):
        '''
        Handles single cell references in formulas.
        '''
        try:
            if values[0].type == 'SHEET_NAME':
                stripped_cell = self.remove_dollar_sign(values[1].value).lower()
                cell_value = self.workbook.get_cell_value(values[0].value, stripped_cell)
            elif values[0].type == 'QUOTED_SHEET_NAME':
                stripped_cell = self.remove_dollar_sign(values[1].value).lower()
                cell_value = self.workbook.get_cell_value(values[0].value[1:-1], stripped_cell)
            else:
                stripped_cell = self.remove_dollar_sign(values[0].value).lower()
                cell_value = self.workbook.get_cell_value(self.sheet_name, stripped_cell)
            return cell_value
        except (ValueError, KeyError) as e:
            detail = 'Invalid cell reference in formula. ' + \
                     'Check sheet name and cell location.'
            return CellError(CellErrorType.BAD_REFERENCE, detail, e)
    
    #@lru_cache
    def check_if_errors(self, values):

        ret_error = None
        for value in values:
            if (isinstance(value, CellError) and value.get_type() == CellErrorType.PARSE_ERROR):
                ret_error = CellError(CellErrorType.PARSE_ERROR,
                            'Formula cannot be parsed.')
                raise ret_error
            if (isinstance(value, CellError) and value.get_type() == CellErrorType.CIRCULAR_REFERENCE):
                ret_error = CellError(CellErrorType.CIRCULAR_REFERENCE, 'Cell is part of circular reference.')
            if isinstance(value, CellError) and not isinstance(ret_error, CellError):
                ret_error = value
        if ret_error is not None:
            raise ret_error
        
    def check_if_cell_range(self, values):
        for value in values:
            if isinstance(value, list):
                raise CellError(CellErrorType.TYPE_ERROR,
                                'Cell range not valid here.')

    @visit_children_decor
    def add_expr(self, values):
        '''
        Handles addition and subtraction.
        '''
        #print(values)
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        # self.check_if_error(values[0], values[2])
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        values[0] = self.convert_to_decimal(values[0])
        values[2] = self.convert_to_decimal(values[2])
        
        if values[1] == '+':
            return values[0] + values[2]

        # subtraction expression
        return values[0] - values[2]

    @visit_children_decor
    def mul_expr(self, values):
        '''
        Handles multiplication and division.
        '''
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        # self.check_if_error(values[0], values[2])
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        values[0] = self.convert_to_decimal(values[0])
        values[2] = self.convert_to_decimal(values[2])
        if values[1] == '*':
            return values[0] * values[2]

        # division expression
        if values[2] == 0:
            raise ZeroDivisionError
        return values[0] / values[2]

    @lru_cache
    @visit_children_decor
    def number(self, values):
        '''
        Handles numbers.
        '''
        # add in protections
        value_temp = str(values[0])
        if value_temp[-1] == '0':
            if '.' in value_temp:
                value_temp = value_temp.rstrip('0').rstrip('.')
            if self.is_string_float(value_temp) or self.workbook.is_string_digit(value_temp):
                return decimal.Decimal(value_temp)
        
        return decimal.Decimal(values[0])
    
    def convert_value_to_string(self, value):
        if isinstance(value, bool):
            if value == True:
                value = 'TRUE'
            else:
                value = 'FALSE'
        else:
            try:
                value = str(value)
            except TypeError as e:
                detail = 'Incompatible types of values.'
                value = CellError(CellErrorType.TYPE_ERROR, detail, e)
                raise value
        return value
    
    @visit_children_decor
    def concat_expr(self, values):
        '''
        Handles string concatenation.
        '''
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        if values[0] is None:
            values[0] = ''
        if values[1] is None:
            values[1] = ''
        if not isinstance(values[0], str):
            values[0] = self.convert_value_to_string(values[0])
        if not isinstance(values[1], str):
            values[1] = self.convert_value_to_string(values[1])
        # self.check_if_error(values[0], values[1])
        
        return values[0] + values[1]

    def check_str_bool(self, value):
        value = str(value)
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        else:
            return value.lower()

    #@lru_cache
    def comp_convert_values(self, value_zero, value_two):
        if type(value_zero) == decimal.Decimal:
            if type(value_two) == decimal.Decimal:
                return value_zero, value_two
            elif value_two is None:
                return value_zero, decimal.Decimal(0)
            else:
                return value_zero, value_two
        elif type(value_zero) == str:
            if type(value_two) == decimal.Decimal:
                return self.check_str_bool(value_zero), value_two
            elif value_two is None:
                return value_zero, ""
            elif type(value_two) == str:
                return value_zero.lower(), value_two.lower()
            else:
                return value_zero, value_two
        elif type(value_zero) == bool:
            if type(value_two) == decimal.Decimal:
                return value_zero, value_two
            elif value_two is None:
                return value_zero, False
            else:
                return value_zero, value_two
        else:
            if type(value_two) == decimal.Decimal:
                return decimal.Decimal(0), value_two
            elif type(value_two) == str:
                return "", value_two
            elif type(value_two) == bool:
                return False, value_two
            elif value_two is None:
                return True, True

    #@lru_cache
    def comp_types(self, value_zero, value_two):
        if type(value_zero) == bool:
            return True
        elif type(value_zero) == str:
            if type(value_two) == bool:
                return False
            else:
                return True
        else:
            return False
    
    @visit_children_decor
    def comp_expr(self, values):
        #print(values)
        big_op = values[1]
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        (values[0], values[2]) = self.comp_convert_values(values[0], values[2])

        if big_op == '=' or big_op == '==':
            if type(values[0]) != type(values[2]):
                return False
            elif values[0] == values[2]:
                return True
            else:
                return False
        elif big_op == '<>' or big_op == '!=':
            if type(values[0]) != type(values[2]):
                return True
            elif values[0] != values[2]:
                return True
            else:
                return False
        elif big_op == ">":
            if type(values[0]) != type(values[2]):
                return self.comp_types(values[0], values[2])
            elif values[0] > values[2]:
                return True
            else:
                return False
        elif big_op == "<":
            if type(values[0]) != type(values[2]):
                return not self.comp_types(values[0], values[2])
            elif values[0] < values[2]:
                return True
            else:
                return False
        elif big_op == ">=":
            if type(values[0]) != type(values[2]):
                return self.comp_types(values[0], values[2])
            elif values[0] >= values[2]:
                return True
            else:
                return False
        elif big_op == "<=":
            if type(values[0]) != type(values[2]):
                return not self.comp_types(values[0], values[2])
            elif values[0] <= values[2]:
                return True
            else:
                return False
        return
    
    @visit_children_decor
    def parens(self, values):
        '''
        Handles parentheses.
        '''
        return values[0]

    @visit_children_decor
    def unary_op(self, values):
        '''
        Handles unary operators.
        '''
        # self.check_if_error(values[1])
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        if values[0] == '+':
            return decimal.Decimal(values[1])

        # subtraction op
        return decimal.Decimal(-values[1])

    @visit_children_decor
    def error(self, values):
        '''
        Handles errors.
        '''
        error_dict = {
            "#ERROR!": {
                'type': CellErrorType.PARSE_ERROR,
                'detail': 'Formula cannot be parsed.'},
            "#CIRCREF!": {
                'type': CellErrorType.CIRCULAR_REFERENCE,
                'detail': 'Cell is part of circular reference.'},
            "#REF!": {
                'type': CellErrorType.BAD_REFERENCE,
                'detail': 'Invalid cell reference in formula. ' +
                          'Check sheet name and cell location.'},
            "#NAME?": {
                'type': CellErrorType.BAD_NAME,
                'detail': 'Function name in formula is unrecognized.'},
            "#VALUE!": {
                'type': CellErrorType.TYPE_ERROR,
                'detail': 'Incompatible types of values.'},
            "#DIV/0!": {
                'type': CellErrorType.DIVIDE_BY_ZERO,
                'detail': 'Cannot divide by zero.'}}
        raise CellError(error_dict[values[0].value.upper()]['type'], error_dict[values[0].value.upper()]['detail'])

    @visit_children_decor
    def string(self, values):
        '''
        Handles strings.
        '''
        return values[0][1:-1]
    
    @visit_children_decor
    def bool(self, values):
        values[0] = values[0].lower()
        if values[0] == 'true':
            return True
        else:
            return False
    
    @lru_cache
    def value_bool_converter(self, value):
        if value is None:
            return False
        if type(value) == bool:
            return value
        if type(value) == str:
            resp = self.check_str_bool(value)
            if type(resp) != bool:
                raise CellError(
                    CellErrorType.TYPE_ERROR,
                    'Incompatible types of values.')
            else:
                return resp
        elif type(value) == decimal.Decimal:
            if value == decimal.Decimal(0):
                return False
            else:
                return True
        else:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Incompatible types of values.')

    @visit_children_decor
    def and_func(self, values):
        values = values[1:]
        if len(values) < 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        for value in values:
            conv_value = self.value_bool_converter(value)
            if conv_value == False:
                return False
        return True

    @visit_children_decor
    def or_func(self, values):
        values = values[1:]
        if len(values) < 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        found_true = False
        for value in values:
            conv_value = self.value_bool_converter(value)
            if conv_value == True:
                found_true = True
        return found_true

    @visit_children_decor
    def not_func(self, values):
        values = values[1:]
        if len(values) != 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        self.check_if_errors(values)
        conv_value = self.value_bool_converter(values[0])
        return not conv_value

    @visit_children_decor
    def xor_func(self, values):
        values = values[1:]
        if len(values) < 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        self.check_if_errors(values)
        self.check_if_cell_range(values)
        ret_value = False
        for value in values:
            conv_value = self.value_bool_converter(value)
            if conv_value == True:
                ret_value = not ret_value
        return ret_value

    @visit_children_decor
    def exact_func(self, values):
        values = values[1:]
        
        self.check_if_cell_range(values)
        if len(values) != 2:
            raise CellError(CellErrorType.TYPE_ERROR, 'Wrong number of arguments.')
        if values[0] is None:
            values[0] = ''
        if values[1] is None:
            values[1] = ''
        if not isinstance(values[0], str):
            values[0] = self.convert_value_to_string(values[0])
        if not isinstance(values[1], str):
            values[1] = self.convert_value_to_string(values[1])
        self.check_if_errors(values)
        if values[0] == values[1]:
            return True
        return False
    
    def if_func(self, parent):
        if len(parent.children) < 3 or len(parent.children) > 4:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        #copy_tree = Tree(tree.data, deepcopy(tree.children, None))

        new_children = parent.children[0:2]
        condition = self.value_bool_converter(self.visit(parent.children[1]))

        if not isinstance(condition, bool):
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Conditional is not Valid.')
        
        if condition == True:
            value_tree = parent.children[2]
            new_children.append(value_tree)
            parent.children = new_children
            value = self.visit(value_tree)
            return value or decimal.Decimal(0)
        else:
            if len(parent.children) == 4:
                value_tree = parent.children[3]
                new_children.append(value_tree)
                parent.children = new_children
                value = self.visit(value_tree)
                return value or decimal.Decimal(0)
            else:
                return False

    def iferror_func(self, parent):
        if len(parent.children) < 2 or len(parent.children) > 3:
            raise CellError(CellErrorType.TYPE_ERROR, 'Wrong number of arguments.')
        
        #copy_tree = Tree(tree.data, deepcopy(tree.children, None))

        if scc_member:
            detail = 'Cell is part of circular reference.'
            raise CellError(CellErrorType.CIRCULAR_REFERENCE, detail)
        new_children = parent.children[0:2]
        try:
            condition_value = self.visit(parent.children[1])
            if not isinstance(condition_value, CellError):
                parent.children = new_children
                if condition_value is None:
                    return 0
                return condition_value
            else:
                if len(parent.children) == 3:
                    value_tree = parent.children[2]
                    new_children.append(value_tree)
                    parent.children = new_children
                    value = self.visit(value_tree)
                    return value
                else:
                    return ""

        except CellError:
            if len(parent.children) == 3:
                value_tree = parent.children[2]
                new_children.append(value_tree)
                parent.children = new_children
                value = self.visit(value_tree)
                return value
            else:
                return ""

    def choose_func(self, parent):
        if len(parent.children) < 3:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        new_children = parent.children[0:2]
        
        index_step = self.visit(parent.children[1])
        self.check_if_errors([index_step])
        index = int(self.convert_to_decimal(index_step))

        if index < 1 or index >= len(parent.children)-1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Index out of range.')
        
        new_children.append(parent.children[index+1])

        return self.visit(parent.children[index+1])

    #@visit_children_decor
    def isblank_func(self, parent):
        if len(parent.children) != 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        if scc_member:
            detail = 'Cell is part of circular reference.'
            raise CellError(CellErrorType.CIRCULAR_REFERENCE, detail)
        try:
            values = self.visit(parent.children[1])
            if values == None:
                return True
            return False
        except CellError:
            return False

    #@visit_children_decor
    def iserror_func(self, parent):
        if len(parent.children) != 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        if scc_member:
            detail = 'Cell is part of circular reference.'
            raise CellError(CellErrorType.CIRCULAR_REFERENCE, detail)
        try:
            value = self.visit(parent.children[1])
            self.check_if_errors([value])
            return False
        except (Exception, CellError):
            return True

    @visit_children_decor
    def version_func(self, values):
        values = values[1:]
        if len(values) > 0:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        return version

    def indirect_func(self, parent):
        if len(parent.children) != 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        prelim_value = parent.children[1]
        if prelim_value.data == 'cell' or prelim_value.data == 'cell_range':
            value = prelim_value
            new_tree = value
        else:
            value = self.visit(prelim_value)
            new_tree = use_parser.parse(f'={value}')
            parent.children[1] = new_tree
            calculated_refs.append(new_tree)

        ret_value = self.visit(new_tree)
        if ret_value is None:
            raise CellError(
                CellErrorType.BAD_REFERENCE,
                'Cannot parse input as cell reference.')

        return ret_value

    def parse_cell_ref(self, cell_ref):
        match = re.match(r"([a-z]+)([1-9][0-9]*)$", cell_ref, re.I)
        if not match:
            return False
            
        col, row = match.groups()
        return col, row
    
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
    
    # how do we make sure that a type error is raised if a cell range is returned in a case that should not accept one 
    @visit_children_decor
    def cell_range(self, parent):
        tree_arr = []
        
        if parent[0].type == "SHEET_NAME" or parent[0].type == "QUOTED_SHEET_NAME":
            sheet_name = parent[0]
            parent = parent[1:]
        else:
            sheet_name = None

        top_left, bot_right = self.find_top_left_bot_right_corners(parent[0], parent[1])
        top_left_col, top_left_row = self.parse_cell_ref(top_left)
        bot_right_col, bot_right_row = self.parse_cell_ref(bot_right)
        
        
        for row in range(int(top_left_row), int(bot_right_row) + 1):
            tree_row = []
            for col_num in range(self.col_to_num(top_left_col), self.col_to_num(bot_right_col) + 1):
                if sheet_name is None:
                    temp_tree = use_parser.parse(f'={self.num_to_col(col_num) + str(row)}')
                else:
                    temp_tree = use_parser.parse(f'={sheet_name}!{self.num_to_col(col_num) + str(row)}')
                tree_row.append(temp_tree)

            tree_arr.append(tree_row)
        return tree_arr
    
    def convert_val_to_decimal(self, value):
        if value is None:
            return None
        return self.convert_to_decimal(value)

    def cell_range_helper(self, tree_arr, conv_to_dec=False):
        value_arr = []
        error = None
        for row in tree_arr:
            value_row = []
            for cell in row:
                value = self.visit(cell)
                if isinstance(value, CellError):
                    if value.get_type() == CellErrorType.CIRCULAR_REFERENCE:
                        raise value
                    else:
                        error = value
                if conv_to_dec:
                    value_row.append(self.convert_to_decimal(value))
                else:
                    value_row.append(value)
                
            value_arr.append(value_row)
        if error:
            raise error
        return value_arr

    # lets make a cohesive list of cells then loop through the evaluated
    # cells for
    def min_max_sum_average_callable(self, parent, func):
        if len(parent.children) < 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        new_children = parent.children[0:1]
        values = []
        ret_value = None
        for child in parent.children[1:]:
            calc_child = self.visit(child)
            if type(calc_child) == list:
                value_arr = self.cell_range_helper(calc_child, conv_to_dec=True)
                #print(value_arr)
                for i in range(len(value_arr)):
                    for j in range(len(value_arr[0])):
                        if value_arr[i][j] is not None:
                            #print(value_arr[i][j])
                            values.append(value_arr[i][j])
                            if ret_value:
                                ret_value = func([ret_value, value_arr[i][j]])
                            else:
                                ret_value = value_arr[i][j]
                        new_children.append(calc_child[i][j])
            else:
                if calc_child is not None:
                    dec_child = self.convert_val_to_decimal(calc_child)
                    values.append(dec_child)
                    if ret_value:
                        ret_value = func([ret_value, dec_child])
                    else:
                        ret_value = dec_child
                
                new_children.append(child)
        parent.children = new_children

        if ret_value is None:
            ret_value = 0
        #print(ret_value)
        return ret_value, values
    
    def min_func(self, parent):
        ret_value, _ = self.min_max_sum_average_callable(parent, min)
        #print(ret_value)
        return ret_value

    def max_func(self, parent):
        ret_value, _ = self.min_max_sum_average_callable(parent, max)
        #print(ret_value)
        return ret_value

    def sum_func(self, parent):
        ret_value, _ = self.min_max_sum_average_callable(parent, sum)
        #print(ret_value)
        return ret_value

    def average_func(self, parent):
        #print('here')
        total_sum, values = self.min_max_sum_average_callable(parent, sum)
        #print('here')
        if len(values) == 0:
            raise CellError(CellErrorType.DIVIDE_BY_ZERO,
                            'Invalid cell range.')
        #print(total_sum, len(values))
        return total_sum / len(values) 
    
    def lookup_exact(self, values):
        #print(values)
        self.check_if_cell_range(values)
        if len(values) != 2:
            print(values)
            raise CellError(CellErrorType.TYPE_ERROR, 'Wrong number of arguments.')
        if values[0] is None:
            values[0] = ''
        if values[1] is None:
            values[1] = ''
        if not isinstance(values[0], str):
            values[0] = self.convert_value_to_string(values[0])
        if not isinstance(values[1], str):
            values[1] = self.convert_value_to_string(values[1])
        self.check_if_errors(values)
        if values[0] == values[1]:
            return True
        return False

    def hlookup_func(self, parent):
        if len(parent.children) != 4:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        new_children = parent.children[0:2]

        key = self.visit(parent.children[1])
        index = int(self.convert_val_to_decimal(self.visit(parent.children[3])))
        new_children.append(parent.children[3])
        column = None

        calc_child = self.visit(parent.children[2])
        if type(calc_child) == list:
            value_arr = self.cell_range_helper(calc_child, conv_to_dec=False)
            for i in [0]:
                for j in range(len(value_arr[i])):
                    new_children.append(calc_child[i][j])
                    
                    if self.lookup_exact([key, value_arr[i][j]]):
                        column = j
                        break
                    
                for k in range(j, len(value_arr[i])):
                    new_children.append(calc_child[i][k])

        else:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'No range provided.')
        
        parent.children = new_children
        if column is None:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        if index > len(value_arr) or index < 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Index out of range.')
        
        return value_arr[index-1][column]

    def vlookup_func(self, parent):
        if len(parent.children) != 4:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        new_children = parent.children[0:2]

        key = self.visit(parent.children[1])
        index = int(self.convert_val_to_decimal(self.visit(parent.children[3])))
        new_children.append(parent.children[3])
        row = None

        calc_child = self.visit(parent.children[2])
        if type(calc_child) == list:
            value_arr = self.cell_range_helper(calc_child, conv_to_dec=False)
            for i in [0]:
                for j in range(len(value_arr)):
                    new_children.append(calc_child[j][i])
                    if self.lookup_exact([key, value_arr[j][i]]):
                        row = j
                        break
                for k in range(j, len(value_arr[i])):
                    new_children.append(calc_child[k][i])

        else:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'No range provided.')
        
        parent.children = new_children
        if row is None:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        if index > len(value_arr[0]) or index < 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Index out of range.')
        
        return value_arr[row][index-1]
    
    def func(self, values):
        func_map = {'and': self.and_func, 'or': self.or_func, 'not': self.not_func,
                    'xor': self.xor_func, 'exact': self.exact_func,
                    'if': self.if_func, 'iferror': self.iferror_func,
                    'choose': self.choose_func, 'isblank': self.isblank_func,
                    'iserror': self.iserror_func, 'version': self.version_func,
                    'indirect': self.indirect_func, 'min': self.min_func,
                    'max': self.max_func, 'sum': self.sum_func,
                    'average': self.average_func, 'hlookup': self.hlookup_func,
                    'vlookup': self.vlookup_func
                    }

        self.contains_func = True
        func_name = values.children[0].lower()
        if func_name in func_map:
            return func_map[func_name](values)
        else:
            raise CellError(CellErrorType.BAD_NAME, 'Function name in formula is unrecognized.')
        
    


def parse_contents(parser, parsed_trees, sheet_name, contents, workbook, start_tree=None, in_scc=False):
    '''
    Parses the contents of a cell and returns a tuple of (cell's value, parsed
    tree).
    '''
    evaluator = FormulaEvaluator(sheet_name, workbook)
    global calculated_refs
    calculated_refs = []
    try:
        if contents in parsed_trees:
            old_tree = parsed_trees[contents]['tree']
            if parsed_trees[contents]['contains_func']:
                tree = Tree(old_tree.data, deepcopy(old_tree.children, None))
            else:
                tree = old_tree
        else:
            tree = parser.parse(contents)
            new_tree = Tree(tree.data, deepcopy(tree.children, None))
            #new_tree = tree
            parsed_trees[contents] = {'tree': new_tree, 'contains_func': False}
        try:
            global scc_member
            scc_member = in_scc
            
            global use_parser
            use_parser = parser
            #print(tree)
            value = evaluator.visit(tree)
            #print(value)
            if evaluator.contains_func:
                parsed_trees[contents]['contains_func'] = True
            
            if tree.data == 'cell' and value is None:
                value = decimal.Decimal(0)
            
            if isinstance(value, Tree):
                raise CellError(
                    CellErrorType.TYPE_ERROR,
                    'Cell range not processed.')
            
        except CellError as e:
            value = e
        except (ValueError, KeyError) as e:
            value = '#REF!'
            detail = 'Invalid cell reference in formula. ' + \
                    'Check sheet name and cell location.'
            value = CellError(CellErrorType.BAD_REFERENCE, detail, e)
        except (ZeroDivisionError) as e:
            value = '#DIV/0!'
            detail = 'Cannot divide by zero.'
            value = CellError(CellErrorType.DIVIDE_BY_ZERO, detail, e)
        except (TypeError) as e:
            detail = 'Incompatible types of values.'
            value = CellError(CellErrorType.TYPE_ERROR, detail, e)
    except (lark.LexError, lark.UnexpectedEOF) as e:
        value = '#ERROR!'
        detail = 'Formula cannot be parsed.'
        value = CellError(CellErrorType.PARSE_ERROR, detail, e)
        tree = None
    
    #print(tree)
    #print(value)
    return value, tree, calculated_refs
