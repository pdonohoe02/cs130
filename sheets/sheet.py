import re

class Sheet:
    def __init__(self):
        # maps cell location to a dictionary with value and contents keys
        self.cells = {}
        self.dependent_cells = {}
        self.extent = [0,0]

    def set_cell_value(self, cell_location: str, refined_contents: str, value, calculation_value, dependent_cells=None):
        if dependent_cells:
            self.dependent_cells[cell_location.lower()] = dependent_cells
        self.cells[cell_location.lower()] = {'contents': refined_contents, 'value': value, 'calculation_value': calculation_value}
        # match = re.match(r"([a-z]+)([0-9]+)", cell_location, re.I)
        # if not match:
        #     return False
        
        # row, col = match.groups()

    def get_dependent_cells(self, cell_location: str):
        if cell_location.lower() not in self.dependent_cells:
            return None
        return self.dependent_cells[cell_location.lower()]

    def get_calculation_value(self, cell_location: str):
        if cell_location in self.cells:
            return self.cells[cell_location.lower()]['calculation_value']
        return None

    def get_cell_contents(self, cell_location: str):
        if cell_location.lower() in self.cells:
            return self.cells[cell_location.lower()]['contents']
        else:
            return None

    def get_cell_value(self, cell_location: str):
        if cell_location.lower() in self.cells:
            return self.cells[cell_location.lower()]['value']
        else:
            return None
        

    def get_extent(self):
        # returns tuple of the size of the sheet
        return self.extent
