#! /usr/bin/env python
"""
TraceInspectorGUI- load raw single-channel record for inspection and 
processing.
"""
import sys
from PyQt5.QtWidgets import *
#from PyQt5.QtCore import *

from sctrace.QtTraceInspector import TraceInspector

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    form = TraceInspector()
    form.show()
    app.exec_()




