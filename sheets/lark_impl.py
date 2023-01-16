import re
import decimal

import lark
from lark import UnexpectedInput, LexError
from lark.visitors import visit_children_decor

# import sys
# sys.path.append(".")
from cellerror import CellErrorType, CellError
# from workbook import get_cell_calculation_value
# fix type_error


class FormulaEvaluator(lark.visitors.Interpreter):
    def __init__(self, sheet_name, workbook):
        self.workbook = workbook
        self.sheet_name = sheet_name

    def convert_none_to_zero(self, value_zero, value_two):
        if value_zero is None:
            value_zero = 0
        if value_two is None:
            value_two = 0
        return value_zero, value_two

    def is_string_float(self, val):
        return re.match(r'^-?\d+(?:\.\d+)$', val) is not None

    def convert_to_decimal(self, value):
        if isinstance(value, str):
            value = value.strip()
            if self.is_string_float(value):
                # string is a float
                value = decimal.Decimal(value)
            elif value.isdigit():
                # string is an int
                value = decimal.Decimal(value)
        return value

    @visit_children_decor
    def cell(self, values):
        if values[0].type == 'SHEET_NAME':
            cell_value = self.workbook.get_cell_value(
                values[0].value, values[1].value)
        else:
            cell_value = self.workbook.get_cell_value(
                self.sheet_name, values[0].value)
        if isinstance(cell_value, CellError):
            raise cell_value
        return cell_value

    @visit_children_decor
    def add_expr(self, values):
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        values[0] = self.convert_to_decimal(values[0])
        values[2] = self.convert_to_decimal(values[2])

        if values[1] == '+':
            return values[0] + values[2]
        elif values[1] == '-':
            return values[0] - values[2]

    @visit_children_decor
    def mul_expr(self, values):
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
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
        return decimal.Decimal(values[0])

    @visit_children_decor
    def concat_expr(self, values):
        if values[0] is None:
            values[0] = ''
        if values[1] is None:
            values[1] = ''
        if not isinstance(values[0], str):
            values[0] = str(values[0])
        if not isinstance(values[1], str):
            values[1] = str(values[1])
        return values[0] + values[1]

    @visit_children_decor
    def parens(self, values):
        return values[0]

    @visit_children_decor
    def unary_op(self, values):
        if values[0] == '+':
            return decimal.Decimal(values[1])
        elif values[0] == '-':
            return decimal.Decimal(-values[1])

    @visit_children_decor
    def error(self, values):
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
        return CellError(error_dict[values[0].value.upper()]['type'], error_dict[values[0].value.upper()]['detail'])

    @visit_children_decor
    def string(self, values):
        return values[0][1:-1]


def parse_contents(sheet_name, contents, workbook):
    '''
    inputs:
    contents: what you want to parse
    outputs:
    value, type(value)
    '''
    parser = lark.Lark.open('sheets/formulas.lark', start='formula')
    evaluator = FormulaEvaluator(sheet_name, workbook)
    try:
        tree = parser.parse(contents)
        value = evaluator.visit(tree)
    except CellError as e:
        value = e
    except (lark.LexError, lark.UnexpectedEOF) as e:
        # if e.expected == ['EQUAL']:
        #    print(e)
        value = '#ERROR!'
        detail = 'Formula cannot be parsed.'
        value = CellError(CellErrorType.PARSE_ERROR, detail, e)
    except (ValueError, KeyError) as e:
        value = '#REF!'
        detail = 'Invalid cell reference in formula. Check sheet name and cell location.'
        value = CellError(CellErrorType.BAD_REFERENCE, detail, e)
    except (ZeroDivisionError) as e:
        value = '#DIV/0!'
        detail = 'Cannot divide by zero.'
        value = CellError(CellErrorType.DIVIDE_BY_ZERO, detail, e)
    except (TypeError) as e:
        detail = 'Incompatible types of values.'
        value = CellError(CellErrorType.TYPE_ERROR, detail, e)
    # catch errors from multiplying strings
    # except (lark.UnexpectedEOF) as e:
    #     # if e.expected == ['BANG']:
    #     #     value = '#VALUE!'
    #     #     detail = 'Incompatible types of values.'
    #     #     value = CellError(CellErrorType.TYPE_ERROR, detail, e)
    #     # else:
    #     value = '#ERROR!'
    #     detail = 'Formula cannot be parsed.'
    #     value = CellError(CellErrorType.PARSE_ERROR, detail, e)
    return value
