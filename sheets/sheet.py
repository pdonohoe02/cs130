import re
from queue import PriorityQueue


class Sheet:
    def __init__(self):
        # maps cell location to a dictionary with value and contents keys
        self.cells = {}
        self.dependent_cells = {}
        self.extent_row = PriorityQueue()
        self.extent_col = PriorityQueue()

    def set_cell_value(self, cell_location: str, refined_contents: str, value,
                       dependent_cells=None):
        if value is None and cell_location.lower() in self.cells:
            del self.cells[cell_location.lower()]
            return
        if dependent_cells:
            self.dependent_cells[cell_location.lower()] = dependent_cells
        self.cells[cell_location.lower()] = {
            'contents': refined_contents, 'value': value}

        match = re.match(r"([a-z]+)([0-9]+)", cell_location, re.I)
        col, row = match.groups()
        self.extent_col.put((-(ord(col.lower()) - 96), cell_location.lower()))
        self.extent_row.put((-int(row), cell_location.lower()))

    def get_dependent_cells(self, cell_location: str):
        if cell_location.lower() not in self.dependent_cells:
            return None
        return self.dependent_cells[cell_location.lower()]

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
        return_row = 0
        return_col = 0

        while not self.extent_row.empty():
            temp_row, temp_cell = self.extent_row.queue[0]
            if temp_cell in self.cells:
                return_row = -temp_row
                break
            else:
                self.extent_row.get()

        while not self.extent_col.empty():
            temp_col, temp_cell = self.extent_col.queue[0]
            if temp_cell in self.cells:
                return_col = -temp_col
                break
            else:
                self.extent_col.get()
                
        # returns tuple of the size of the sheet
        return return_col, return_row
