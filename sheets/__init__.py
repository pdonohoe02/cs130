version = '1.0'
__all__ = ['Workbook', 'CellError', 'CellErrorType']

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from workbook import Workbook
from cellerror import CellError, CellErrorType