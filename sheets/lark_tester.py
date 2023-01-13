import decimal
import lark
from lark.visitors import visit_children_decor

class FormulaEvaluator(lark.visitors.Interpreter):
    def find_values(self, value_list):
        #print(value_list)
        #print(value_list[0].type)
        #for i in value_list:
         #   print(i)
        return 5

    @visit_children_decor
    def add_expr(self, values):
        #print(values)
        if values[1] == '+':
            return values[0] + values[2]
        elif values[1] == '-':
            return values[0] - values[2]

    @visit_children_decor
    def mul_expr(self, values):
        if type(values[0]) == list:
            values[0] = decimal.Decimal(self.find_values(values[0]))
        if type(values[2]) == list:
            values[2] = decimal.Decimal(self.find_values(values[2]))
        if values[1] == '*':
            return values[0] * values[2]
        elif values[1] == '/':
            return values[0] / values[2]
    
    def cell(self, tree):
        print(tree)
        return 5

    def number(self, tree):
        #print(tree)
        return decimal.Decimal(tree.children[0])
    
    #@visit_children_decor
    def string(self, tree):
        #print(tree)
        return tree.children[0].value[1:-1]


parser = lark.Lark.open('sheets/formulas.lark', start = 'formula')
print(parser.rules)
evaluator = FormulaEvaluator()

tree = parser.parse('=123.456')
value = evaluator.visit(tree)
print(f'value = {value} (type is {type(value)})')

tree = parser.parse('=123.456 / Sheet1!A15 + 94-2')
value = evaluator.visit(tree)
print(f'value = {value} (type is {type(value)})')

tree = parser.parse('=A15')
print(tree)
value = evaluator.visit(tree)
print(f'value = {value} (type is {type(value)})')

tree = parser.parse('=Sheet1!A15')
value = evaluator.visit(tree)
print(f'value = {value} (type is {type(value)})')
# tarjans algorithm iteratively is required

# contents will be the raw string 
# value will be