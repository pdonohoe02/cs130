'''
This file contains the lark parser for formulas.
'''
import re
import decimal

import lark
from lark import Tree
from lark.visitors import visit_children_decor
from functools import lru_cache

from cellerror import CellErrorType, CellError
from version import version


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

    # def check_if_error(self, value0, value1=None):
    #     if ((isinstance(value0, CellError) and value0.get_type() == CellErrorType.PARSE_ERROR) or
    #         (isinstance(value1, CellError) and value1.get_type() == CellErrorType.PARSE_ERROR)):
    #         raise CellError(CellErrorType.PARSE_ERROR,
    #                         'Formula cannot be parsed.')
    #     if ((isinstance(value0, CellError) and value0.get_type() == CellErrorType.CIRCULAR_REFERENCE) or
    #           (isinstance(value1, CellError) and value1.get_type() == CellErrorType.CIRCULAR_REFERENCE)):
    #         raise CellError(CellErrorType.CIRCULAR_REFERENCE,
    #                         'Cell is part of circular reference.')
    #     if isinstance(value0, CellError):
    #         raise value0
    #     if isinstance(value1, CellError):
    #         raise value1
    
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

    @visit_children_decor
    def add_expr(self, values):
        '''
        Handles addition and subtraction.
        '''
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        # self.check_if_error(values[0], values[2])
        self.check_if_errors(values)
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
        values[0] = self.convert_to_decimal(values[0])
        values[2] = self.convert_to_decimal(values[2])
        if values[1] == '*':
            return values[0] * values[2]

        # division expression
        if values[2] == 0:
            raise ZeroDivisionError
        return values[0] / values[2]

    @visit_children_decor
    def number(self, values):
        '''
        Handles numbers.
        '''
        return decimal.Decimal(values[0])
    
    def convert_value_to_string(self, value):
        if isinstance(value, bool):
            if value == True:
                value = 'TRUE'
            else:
                value = 'FALSE'
        else:
            value = str(value)
        return value
    
    @visit_children_decor
    def concat_expr(self, values):
        '''
        Handles string concatenation.
        '''
        if values[0] is None:
            values[0] = ''
        if values[1] is None:
            values[1] = ''
        if not isinstance(values[0], str):
            values[0] = self.convert_value_to_string(values[0])
        if not isinstance(values[1], str):
            values[1] = self.convert_value_to_string(values[1])
        # self.check_if_error(values[0], values[1])
        self.check_if_errors(values)
        return values[0] + values[1]

    def check_str_bool(self, value):
        value = str(value)
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        else:
            return value.lower()

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
        big_op = values[1]
        self.check_if_errors(values)
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

    def and_func(self, values):
        print('add')
        self.check_if_errors(values)
        for value in values:
            conv_value = self.value_bool_converter(value)
            if conv_value == False:
                return False
        return True

    def or_func(self, values):
        print('or')
        self.check_if_errors(values)
        found_true = False
        for value in values:
            conv_value = self.value_bool_converter(value)
            if conv_value == True:
                found_true = True
        return found_true

    def not_func(self, values):
        print('not')
        if len(values) > 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        self.check_if_errors(values)
        conv_value = self.value_bool_converter(values[0])
        return not conv_value

    def xor_func(self, values):
        print('xor')
        self.check_if_errors(values)
        ret_value = False
        for value in values:
            conv_value = self.value_bool_converter(value)
            if conv_value == True:
                ret_value = not ret_value
        return ret_value

    def exact_func(self, values):
        print('exact')
        ret_value = False
        if len(values) != 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        if values[0] is None:
            values[0] = ''
        if values[1] is None:
            values[1] = ''
        if not isinstance(values[0], str):
            values[0] = self.convert_value_to_string(values[0])
        if not isinstance(values[1], str):
            values[1] = self.convert_value_to_string(values[1])
        # self.check_if_error(values[0], values[1])
        self.check_if_errors(values)
        
    @visit_children_decor
    def get_values(self, values):
        return values
    
    def if_func(self, parent):
        print('if')
        
        if len(parent.children)-1 < 2 or len(parent.children)-1 > 3:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        new_children = parent.children[0:2]
        values = self.get_values(parent)[1:]
        if not isinstance(values[0], bool):
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Conditional is not Valid.')
        self.check_if_errors(values)
        if values[0] == True:
            new_children.append(parent.children[2])
            parent.children = new_children
            return values[1] or decimal.Decimal(0)
        else:
            if len(values) == 3:
                new_children.append(parent.children[3])
                parent.children = new_children
                return values[2] or decimal.Decimal(0)
            else:
                return False

    def iferror_func(self, values):
        print('iferror')
        if len(values) < 1 or len(values) > 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        if not isinstance(values[0], CellError):
            return values[0]
        elif len(values) == 2:
            return values[1]
        else:
            return ""

    def choose_func(self, values):
        print('choose')
        if len(values) < 2:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        index = values[0]
        if index < 1 or index >= len(values):
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Index out of range.')
        
        self.check_if_errors(values[index])
        return values[index]

    def isblank_func(self, values):
        print('isblank')
        self.check_if_errors(values)
        if len(values) != 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        if values[0] == None:
            return True
        return False

    def iserror_func(self, values):
        if len(values) != 1:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        
        if not isinstance(values[0], CellError):
            return False
        return True

    def version_func(self, values):
        print("version")
        if len(values) > 0:
            raise CellError(
                CellErrorType.TYPE_ERROR,
                'Wrong number of arguments.')
        return version

    def isdirect_func(self, values):
        print('isdirect')
        self.check_if_errors(values)

    #@visit_children_decor
    def func(self, values):
        func_map = {'and': self.and_func, 'or': self.or_func, 'not': self.not_func,
                    'xor': self.xor_func, 'exact': self.exact_func,
                    'if': self.if_func, 'iferror': self.iferror_func,
                    'choose': self.choose_func, 'isblank': self.isblank_func,
                    'iserror': self.iserror_func, 'version': self.version_func,
                    }
        #print(values.children)
        #values.children = values.children[0:1]
        #print(values.children)
        #print(values)
        #values = values[0:1]
        #print(values)
        func_name = values.children[0].lower()
        #func_name = values[0].lower()
        if func_name in func_map:
            
            return func_map[func_name](values)
        else:
            raise CellError(CellErrorType.BAD_NAME, 'Function name in formula is unrecognized.')


def parse_contents(parser, parsed_trees, sheet_name, contents, workbook, start_tree=None):
    '''
    Parses the contents of a cell and returns a tuple of (cell's value, parsed
    tree).
    '''
    evaluator = FormulaEvaluator(sheet_name, workbook)
    try:
        if contents in parsed_trees:
            start_tree = parsed_trees[contents]
        else:
            start_tree = parser.parse(contents)
            parsed_trees[contents] = start_tree
    
        global tree
        tree = start_tree
        try:
            value = evaluator.visit(tree)
            if tree.data == 'cell' and value is None:
                value = decimal.Decimal(0)
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
        #print(e)
        value = CellError(CellErrorType.PARSE_ERROR, detail, e)
        tree = None

    #print(value, tree)
    return value, tree
