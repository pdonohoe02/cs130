import os
import sys
version = '1.0.1'
__all__ = ['Workbook', 'CellError', 'CellErrorType']

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from cellerror import CellError, CellErrorType
from workbook import Workbook
