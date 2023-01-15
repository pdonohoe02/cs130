import decimal

import lark
from lark import UnexpectedInput, LexError
from lark.visitors import visit_children_decor

import sys
sys.path.append(".")
from cellerror import CellErrorType
#from workbook import get_cell_calculation_value

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

    @visit_children_decor
    def cell(self, values):
        if values[0].type == 'SHEET_NAME':
            return self.workbook.get_cell_calculation_value(values[0].value, values[1].value)
        else:
            return self.workbook.get_cell_calculation_value(self.sheet_name, values[0].value)

    @visit_children_decor
    def add_expr(self, values):
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
        if values[1] == '+':
            return values[0] + values[2]
        elif values[1] == '-':
            return values[0] - values[2]

    @visit_children_decor
    def mul_expr(self, values):
        values[0], values[2] = self.convert_none_to_zero(values[0], values[2])
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
        return values[0].value

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
    parser = lark.Lark.open('sheets/formulas.lark', start = 'formula')
    evaluator = FormulaEvaluator(sheet_name, workbook)
    try:
        tree = parser.parse(contents)
        #print(tree)
        value = evaluator.visit(tree)
        value_type = type(value)
    except lark.LexError as e:
        #if e.expected == ['EQUAL']:
        #    print(e)
        value = '#ERROR!'
        value_type = CellErrorType.PARSE_ERROR
    except (ValueError, KeyError):
        value = '#REF!'
        value_type = CellErrorType.BAD_REFERENCE
    except (ZeroDivisionError):
        value = '#DIV/0!'
        value_type = CellErrorType.DIVIDE_BY_ZERO
    # catch errors from multiplying strings
    except (lark.UnexpectedEOF) as e:
        if e.expected == ['BANG']:
            value = '#VALUE!'
            value_type = CellErrorType.TYPE_ERROR
        else:
            value = '#ERROR!'
            value_type = CellErrorType.PARSE_ERROR
    return value, value_type

