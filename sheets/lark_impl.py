'''
This file contains the lark parser for formulas.
'''
import re
import decimal

import lark
from lark.visitors import visit_children_decor

from cellerror import CellErrorType, CellError


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
                raise CellError(CellErrorType.TYPE_ERROR, 'Incompatible types of values.')
        return value

    @visit_children_decor
    def cell(self, values):
        '''
        Handles single cell references in formulas.
        '''
        try:
            if values[0].type == 'SHEET_NAME':
                cell_value = self.workbook.get_cell_value(
                    values[0].value, values[1].value.lower())
            elif values[0].type == 'QUOTED_SHEET_NAME':
                cell_value = self.workbook.get_cell_value(
                    values[0].value[1:-1], values[1].value.lower())
            else:
                cell_value = self.workbook.get_cell_value(
                    self.sheet_name, values[0].value.lower())
            return cell_value
        except (ValueError, KeyError) as e:
            detail = 'Invalid cell reference in formula. ' + \
                     'Check sheet name and cell location.'
            return CellError(CellErrorType.BAD_REFERENCE, detail, e)
        

    def check_if_error(self, value0, value1=None):
        if ((isinstance(value0, CellError) and  
             value0.get_type() == CellErrorType.PARSE_ERROR) or 
             (isinstance(value1, CellError) and 
             value1.get_type() == CellErrorType.PARSE_ERROR)):
            raise CellError(CellErrorType.PARSE_ERROR, 'Formula cannot be parsed.')
        elif ((isinstance(value0, CellError) and  
             value0.get_type() == CellErrorType.CIRCULAR_REFERENCE) or 
             (isinstance(value1, CellError) and 
             value1.get_type() == CellErrorType.CIRCULAR_REFERENCE)):
              raise CellError(CellErrorType.CIRCULAR_REFERENCE, 'Cell is part of circular reference.')
        elif isinstance(value0, CellError):
            raise value0
        elif isinstance(value1, CellError):
            raise value1

    @visit_children_decor
    def add_expr(self, values):
        '''
        Handles addition and subtraction.
        '''
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        self.check_if_error(values[0], values[2])
        values[0] = self.convert_to_decimal(values[0])
        values[2] = self.convert_to_decimal(values[2])
        if values[1] == '+':
            return values[0] + values[2]
        elif values[1] == '-':
            return values[0] - values[2]

    @visit_children_decor
    def mul_expr(self, values):
        '''
        Handles multiplication and division.
        '''
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        self.check_if_error(values[0], values[2])
        values[0] = self.convert_to_decimal(values[0])
        values[2] = self.convert_to_decimal(values[2])
        if values[1] == '*':
            return values[0] * values[2]
        elif values[1] == '/':
            if values[2] == 0:
                raise ZeroDivisionError
            return values[0] / values[2]

    @visit_children_decor
    def number(self, values):
        '''
        Handles numbers.
        '''
        return decimal.Decimal(values[0])

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
            values[0] = str(values[0])
        if not isinstance(values[1], str):
            values[1] = str(values[1])
        self.check_if_error(values[0], values[1])
        return values[0] + values[1]

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
        self.check_if_error(values[1])
        if values[0] == '+':
            return decimal.Decimal(values[1])
        elif values[0] == '-':
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
                'detail': 'Invalid cell reference in formula. ' + \
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
        raise CellError(error_dict[values[0].value.upper(
        )]['type'], error_dict[values[0].value.upper()]['detail'])

    @visit_children_decor
    def string(self, values):
        '''
        Handles strings.
        '''
        return values[0][1:-1]


def parse_contents(sheet_name, contents, workbook):
    '''
    Parses the contents of a cell and returns a tuple of (cell's value, parsed
    tree).
    '''
    parser = lark.Lark.open('sheets/formulas.lark', start='formula')
    evaluator = FormulaEvaluator(sheet_name, workbook)
    tree = None
    try:
        tree = parser.parse(contents)
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

        value = CellError(CellErrorType.PARSE_ERROR, detail, e)

    return value, tree
