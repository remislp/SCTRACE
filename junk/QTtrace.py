#! /usr/bin/python
"""
A simple GUI to display and process single channel record.
Depends on pyqt and matplotlib modules.
"""

import sys
import math
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except:
    raise ImportError("pyqt module is missing")

import numpy as np

from dcpyps import dcio
from dcqtgui import filter

class TraceGUI(QMainWindow):
    def __init__(self, parent=None):
        super(TraceGUI, self).__init__(parent)
        self.resize(1000, 700)     # width, height in px
        self.mainFrame = QWidget()
        self.setWindowTitle('pyPlotsamp')
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        self.painter =  QPainter()

        self.loaded = False
        self.filtered = False
        self.ffilter = None
        self.line_length = 5.0 # seconds
        self.page_lines = 5
        self.point_every = 50
        self.line_separ = 10.0 # pA
        self.pages = 1
        self.page = 1
        self.intervals = None
        self.amplitudes = None
        self.fc = 1000.0

        fileMenu = self.menuBar().addMenu('&File')
        fileSSDOpenAction = self.createAction("&Open SSD file", self.on_load_SSD,
            None, "ssdfileopen", "File Open")
        fileABFOpenAction = self.createAction("&Open ABF file", self.on_load_ABF,
            None, "abffileopen", "File Open")
        #fileIdealizedClampfitOpenAction = self.createAction(
        #    "&Open Clampfit idealised file", self.onClampfitIdealisedOpen,
        #    None, "clampfitfileopen", "File Open")
        fileSaveAsAction = self.createAction("&Save As...", self.on_safe_file,
            None, "filesaveas", "File Save As")
        self.addActions(fileMenu, (fileSSDOpenAction, fileABFOpenAction,
            #fileIdealizedClampfitOpenAction, 
            fileSaveAsAction))

        plotMenu = self.menuBar().addMenu('&Plot')
        nextPageAction = self.createAction("&Next page", self.onNextPage)
        prevPageAction = self.createAction("&Previous page", self.onPrevPage)
        printPageAction = self.createAction("&Print page", self.onPrint)
        plotOptionsAction = self.createAction("&Plot options", self.onPlotOptions)
        self.addActions(plotMenu, (nextPageAction,
            prevPageAction, #printPageAction, 
            plotOptionsAction))
            
        signalMenu = self.menuBar().addMenu('&Signal')
        filterGausAction = self.createAction("&Gaussian filter", self.onFilterGaus)
        #sliceTraceAction = self.createAction("&Slice trace", self.onSliceTrace)
        self.addActions(signalMenu, (filterGausAction, )) #, sliceTraceAction))

        helpMenu = self.menuBar().addMenu('&Help')
        helpAboutAction = self.createAction("&About", self.onHelpAbout)
        self.addActions(helpMenu, (helpAboutAction, None))

        #menu_action_file = menu.exec_(self.mapToGlobal(pos))

    def createAction(self, text, slot=None, shortcut=None, icon=None,
            tip=None, checkable=False, signal="triggered()"):
        """
        Create menu actions.
        """
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            #self.connect(action, SIGNAL(signal), slot)
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def addActions(self, target, actions):
        """
        Add actions to menu.
        """
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def on_load_SSD(self):
        try:
            self.onSSDFileOpen()
        except:
            pass

    def on_load_ABF(self):
        #try:
            self.onABFFileOpen()
        #except:
        #    pass

    def on_safe_file(self):
        try:
            self.onFileSaveAs()
        except:
            pass

    def onSSDFileOpen(self):
        """
        """

        self.filename, filt = QFileDialog.getOpenFileName(self,
            "Open Data File...", "", "Consam files (*.ssd *.SSD *.dat *.DAT)")
        self.h = dcio.ssd_read_header (self.filename)
        self.trace = dcio.ssd_read_data(self.filename, self.h)

        self.calfac = self.h['calfac']
        self.srate = self.h['srate']
        self.sample = 1 / self.h['srate']
        self.points_total = self.h['ilen'] / 2
        self.ffilter = self.h['filt']
        self.record_length = self.points_total * self.sample

        self.file_type = 'ssd'
        self.loaded = True
        self.page = 1
        self.update()

    def onABFFileOpen(self):
        """
        """

        self.filename, filt = QFileDialog.getOpenFileName(self,
            "Open Data File...", "", "Axon files (*.abf)")
        _time, self.trace = filter.open_abf(self.filename)
        self.sample = _time[1]
        self.srate = 1.0 / self.sample
        print('sample=', self.sample)
        self.points_total = len(self.trace)
        self.calfac = 1

        #self.h = dcio.abf_read_header(self.filename)
        #self.trace = dcio.abf_read_data(self.filename, self.h)
        #self.points_total = self.h['IActualAcqLength'] / self.h['nADCNumChannels']
        #self.srate = 1 / (self.h['fADCSampleInterval'] * self.h['nADCNumChannels'])
        #self.sample = self.h['fADCSampleInterval'] * self.h['nADCNumChannels'] / 1e6
        #self.calfac = (1 /
        #    #(6553.6
        #    ((self.h['IADCResolution'] / self.h['fADCRange']) * self.h['fTelegraphAdditGain'][self.h['nADCSamplingSeq'][0]] *
        #    self.h['fInstrumentScaleFactor'][self.h['nADCSamplingSeq'][0]]))
        #self.ffilter = float(self.h['fSignalLowpassFilter'][self.h['nADCSamplingSeq'][0]])

        self.file_type = 'abf'
        self.loaded = True
        self.page = 1
        self.update()
        
    def onClampfitIdealisedOpen(self):
        self.filename, filt = QFileDialog.getOpenFileName(self,
            "Open Data File...", "", "CSV files (*.csv)")
        self.record = np.genfromtxt(self.filename, skip_header=1, delimiter=',')
        self.intervals = self.record[:, 8] / 1000.0 # convert from ms to s
        self.amplitudes = self.record[:, 6]
        self.record_length = int(self.record[-1, 5] / 1000.0)
        
        self.file_type = 'csv'
        self.loaded = True
        self.page = 1
        self.pages = self.record_length / (self.page_lines * self.line_length)
        self.remainder = -1
        self.remainder_amplitude = 0.0
        self.remainder_length = self.line_length / 20.0
        self.update()

    def onFileSaveAs(self):
        """
        """

        self.out_filename, filt = QFileDialog.getSaveFileName(self,
            "Save File As...", "",
            "Consam file (*.ssd)")

        if self.file_type == 'ssd':
            if self.filtered:
                self.h['ilen'] = self.points_total * 2
                self.h['srate'] = self.srate
                self.h['filt'] = self.ffilter
                self.h['idt'] = self.sample * 1e6

            dcio.ssd_save(self.out_filename, self.h, self.trace)
        elif self.file_type == 'abf':
            h_conv = dcio.abf2ssd(self.h)
            dcio.ssd_save(self.out_filename, h_conv, self.trace)

    def onSliceTrace(self):
        """
        """

        dialog = SliceTraceDlg(self.points_total, self)
        if dialog.exec_():
            first, last = dialog.return_par()

        self.original_trace = self.trace
        self.original_points_total = self.points_total

        self.points_total = last - (first - 1)
        self.trace = np.zeros(self.points_total, 'h')
        self.trace = self.original_trace[first-1 : last]

        self.page = 1
        self.update()
            
    def onFilterGaus(self):
        """
        """
        
        dialog = FilterOptsDlg(self)
        if dialog.exec_():
            self.ffilter, fc = dialog.return_par()
        
        self.original_trace = self.trace
        self.original_ffilter = self.ffilter
        self.original_srate = self.srate
        self.original_sample = self.sample
        self.original_points_total = self.points_total

        trace_new, srate = filter.filter_trace(self.trace,
            fc, self.ffilter, self.srate)
        self.trace = trace_new.copy()
        self.srate = srate
        self.ffilter = fc
        self.sample = 1 / srate
        self.points_total = self.trace.shape[0]

        self.filtered = True
        self.page = 1
        self.update()

    def onPlotOptions(self):
        """
        """

        dialog = PlotPageDlg(self)
        if dialog.exec_():
            self.line_length, self.page_lines, self.point_every, self.line_separ = dialog.return_par()
        self.pages = self.record_length / (self.page_lines * self.line_length)
        self.page = 1
        self.update()
        
    def onNextPage(self):
        """
        """
       
        if self.page < self.pages:
            self.page += 1
            self.update()

    def onPrevPage(self):
        """
        """
        
        if self.page > 1:
            self.page -= 1
            self.update()

    def onPrint(self):
        """
        """

        printer=QPrinter(QPrinter.HighResolution)
        printer.setOrientation(QPrinter.Landscape)
        printDialog=QPrintDialog(printer)
        if (printDialog.exec_() == QDialog.Accepted):
            self.painter.begin(printer)
            self.drawSCTrace(self.painter)
            self.painter.end()

    def onHelpAbout(self):
        """
        """

        pass

    def paintEvent(self, event):
        """
        """

        if self.loaded:
            self.painter.begin(self)
            if self.file_type == 'ssd' or self.file_type == 'abf':
                self.drawSCTrace(self.painter)
            elif self.file_type == 'csv':
                self.drawIdealisedTrace(self.painter)
            self.painter.end()

    def drawIdealisedTrace(self, event):
        """
        """
        
        
        average = np.average(self.amplitudes[:2])
        yStartDbl = float((self.page_lines +1) * self.line_separ)
        page_str = (self.filename + "; Page " + str(self.page) + " of " +
            str(self.pages))
        point_str = ("Seconds/line: {0:.3f}; line separation (pA): {1:.3f}".
            format(self.line_length, self.line_separ))
        self.painter.drawText(100, 50, page_str)
        self.painter.drawText(100, 650, point_str)

        for j in range(self.page_lines):
            
            xDbl1 = 0
            yDbl1 = (self.remainder_amplitude - average) + yStartDbl - (j+1)*self.line_separ
            line_end = False
            running_length = self.remainder_length
            while (not line_end) and (self.remainder < len(self.record)-1):
                
                if (running_length < self.line_length):
                    xDbl2 = running_length
                    yDbl2 = float((self.remainder_amplitude - average) + yStartDbl - (j+1)*self.line_separ)
                    self.draw_line(xDbl1, yDbl1, xDbl2, yDbl2)
                    
                    self.remainder += 1
                    
                    if math.isnan(self.intervals[self.remainder]):
                        self.remainder_amplitude = 0.0
                        self.remainder_length = 0.5
                        #self.remainder_length = self.record[self.remainder + 1, 4] - self.record[self.remainder - 1, 5]
                    else:
                        self.remainder_length = self.intervals[self.remainder]
                        self.remainder_amplitude = self.amplitudes[self.remainder]
                    running_length += self.remainder_length
                    
                    xDbl1 = xDbl2
                    yDbl1 = float((self.remainder_amplitude - average) + yStartDbl - (j+1)*self.line_separ)
                    self.draw_line(xDbl1, yDbl2, xDbl1, yDbl1)
                    
                else:
                    xDbl2 = self.line_length
                    yDbl2 = float((self.remainder_amplitude - average) + yStartDbl - (j+1)*self.line_separ)
                    self.draw_line(xDbl1, yDbl1, xDbl2, yDbl2)
                    line_end = True
                    self.remainder_length = running_length - self.line_length
                        
                
                
                
               

    def draw_line(self, xDbl1, yDbl1, xDbl2, yDbl2):
        
        xMinPix = int(self.width() * 5 / 100)
        xMaxPix = int(self.width() * 90 / 100)
        yMaxPix = int(self.height() * 10 / 100)
        yMinPix = int(self.height() * 90 / 100)
        
        xMinDbl = float(0)
        xMaxDbl = float(self.line_length)
        yMinDbl = float(0)
        yMaxDbl = float(self.page_lines + 2) * self.line_separ
        

        xScaleDbl = float(xMaxPix - xMinPix) / float(xMaxDbl - xMinDbl)
        yScaleDbl = float(yMaxPix - yMinPix) / float(yMaxDbl - yMinDbl)

        xPix1 = xMinPix + int((xMinDbl) * xScaleDbl)
        yPix1 = yMinPix + int((yMinDbl) * yScaleDbl)
        xPix2 = xMinPix + int((xMaxDbl) * xScaleDbl)
        yPix2 = yMinPix + int((yMaxDbl) * yScaleDbl)
        
        xPix1 = xMinPix + int((xDbl1 - xMinDbl) * xScaleDbl)
        yPix1 = yMinPix + int((yDbl1 - yMinDbl) * yScaleDbl)
        xPix2 = xMinPix + int((xDbl2 - xMinDbl) * xScaleDbl)
        yPix2 = yMinPix + int((yDbl2 - yMinDbl) * yScaleDbl)
        self.painter.drawLine(xPix1, yPix1, xPix2, yPix2)

    def drawSCTrace(self, event):
        """
        """

        line_points = int(self.line_length / self.sample + 1)
        page_points = line_points * self.page_lines
        line_points_draw = int(line_points / self.point_every)
        self.pages = self.points_total / page_points
        average = np.average(self.trace[:line_points])

        page_str = (self.filename + "; Page " + str(self.page) + " of " +
            str(int(self.pages)))
        point_str = ("Points " + str(page_points * (self.page - 1) + 1) +
            " to " + str(page_points * self.page) + " every " +
            str(self.point_every) + " point(s); seconds/line: " +
            str(self.line_length) + "; line separation (pA): " + str(self.line_separ))
        self.painter.drawText(100, 50, page_str)
        self.painter.drawText(100, 650, point_str)

        xMinPix = int(self.width() * 5 / 100)
        xMaxPix = int(self.width() * 90 / 100)
        yMaxPix = int(self.height() * 10 / 100)
        yMinPix = int(self.height() * 90 / 100)

        xMinDbl = float(0)
        xMaxDbl = float(self.line_length)
        yMinDbl = float(0)
        yMaxDbl = float(self.page_lines + 2) * self.line_separ
        yStartDbl = float((self.page_lines +1) * self.line_separ)

        xScaleDbl = float(xMaxPix - xMinPix) / float(xMaxDbl - xMinDbl)
        yScaleDbl = float(yMaxPix - yMinPix) / float(yMaxDbl - yMinDbl)

        xPix1 = xMinPix + int((xMinDbl) * xScaleDbl)
        yPix1 = yMinPix + int((yMinDbl) * yScaleDbl)
        xPix2 = xMinPix + int((xMaxDbl) * xScaleDbl)
        yPix2 = yMinPix + int((yMaxDbl) * yScaleDbl)

        for j in range(self.page_lines):
            xDbl1 = 0
            yDbl1 = (self.trace[0 + page_points*(self.page-1) + line_points * j] - average) * self.calfac + yStartDbl - (j+1)*self.line_separ
            for i in range (line_points_draw):

                xDbl2 = float((i+1) * self.sample * self.point_every)
                yDbl2 = float((self.trace[0 + page_points*(self.page-1) + line_points * j + (i+1)*self.point_every -1] - average) * self.calfac + yStartDbl - (j+1)*self.line_separ)
                xPix1 = xMinPix + int((xDbl1 - xMinDbl) * xScaleDbl)
                yPix1 = yMinPix + int((yDbl1 - yMinDbl) * yScaleDbl)
                xPix2 = xMinPix + int((xDbl2 - xMinDbl) * xScaleDbl)
                yPix2 = yMinPix + int((yDbl2 - yMinDbl) * yScaleDbl)
                self.painter.drawLine(xPix1, yPix1, xPix2, yPix2)
                xDbl1 = xDbl2
                yDbl1 = yDbl2


class PlotPageDlg(QDialog):
    """
    Dialog to input page plotting parameters.
    """
    def __init__(self, parent=None):
        super(PlotPageDlg, self).__init__(parent)

        self.line_length = 5 # seconds
        self.page_lines = 5
        self.point_every = 50
        self.line_separ = 10 # pA

        layoutMain = QVBoxLayout()
        layoutMain.addWidget(QLabel('Plot layout options'))

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Seconds per line:"))
        self.lengthEdit = QLineEdit(str(self.line_length))
        self.lengthEdit.setMaxLength(10)
        self.lengthEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.lengthEdit)
        layoutMain.addLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Number of lines per page:"))
        self.linesEdit = QLineEdit(str(self.page_lines))
        self.linesEdit.setMaxLength(10)
        self.linesEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.linesEdit)
        layoutMain.addLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Draw every nth point:"))
        self.everyEdit = QLineEdit(str(self.point_every))
        self.everyEdit.setMaxLength(10)
        self.everyEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.everyEdit)
        layoutMain.addLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("pA between lines:"))
        self.separEdit = QLineEdit(str(self.line_separ))
        self.separEdit.setMaxLength(10)
        self.separEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.separEdit)
        layoutMain.addLayout(layout)
        layoutMain.addWidget(ok_cancel_button(self))

        self.setLayout(layoutMain)
        self.setWindowTitle("Plot layout options...")

    def on_par_changed(self):
        """
        """

        self.line_length = int(self.lengthEdit.text())
        self.page_lines = int(self.linesEdit.text())
        self.point_every = int(self.everyEdit.text())
        self.line_separ = int(self.separEdit.text())

    def return_par(self):
        """
        Return parameters on exit.
        """
        return self.line_length, self.page_lines, self.point_every, self.line_separ
    
class FilterOptsDlg(QDialog):
    """
    Dialog to input filter options.
    """
    def __init__(self, parent=None):
        super(FilterOptsDlg, self).__init__(parent)
        
        self.ffilter = None
        self.filter = 1000 # Hz

        layoutMain = QVBoxLayout()
        layoutMain.addWidget(QLabel('Filter options:'))

        layout = QHBoxLayout()

        layout.addWidget(QLabel("Trace is already filtered at final fc (Hz):"))
        self.ffilterEdit = QLineEdit(str(self.ffilter))
        self.ffilterEdit.setMaxLength(10)
        self.ffilterEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.ffilterEdit)
        layout.addWidget(QLabel("Filter with Gaussian filter to have final fc (Hz):"))
        self.filterEdit = QLineEdit(str(self.filter))
        self.filterEdit.setMaxLength(10)
        self.filterEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.filterEdit)
        layoutMain.addLayout(layout)
        layoutMain.addWidget(ok_cancel_button(self))

        self.setLayout(layoutMain)
        self.setWindowTitle("Filter options...")

    def on_par_changed(self):
        """
        """
        self.ffilter = int(self.ffilterEdit.text())
        self.filter = int(self.filterEdit.text())

    def return_par(self):
        """
        Return parameters on exit.
        """
        return self.ffilter, self.filter

class SliceTraceDlg(QDialog):
    """
    Dialog to input trace slice limits.
    """
    def __init__(self, allpoints, parent=None):
        super(SliceTraceDlg, self).__init__(parent)

        self.first = 1
        self.last = allpoints

        layoutMain = QVBoxLayout()
        layoutMain.addWidget(QLabel('Slice trace:'))

        # First and last data points to be used
        layout = QHBoxLayout()
        layout.addWidget(QLabel("First "))
        self.firstEdit = QLineEdit(str(self.first))
        self.firstEdit.setMaxLength(100)
        self.firstEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.firstEdit)
        layout.addWidget(QLabel(" and last "))
        self.lastEdit = QLineEdit(str(int(self.last)))
        self.lastEdit.setMaxLength(100)
        self.lastEdit.editingFinished.connect(self.on_par_changed)
        layout.addWidget(self.lastEdit)
        layout.addWidget(QLabel(" data points to be used."))
        layoutMain.addLayout(layout)
        layoutMain.addWidget(ok_cancel_button(self))

        self.setLayout(layoutMain)
        self.setWindowTitle("Trace slice...")

    def on_par_changed(self):
        """
        """
        self.first = int(self.firstEdit.text())
        self.last = int(self.lastEdit.text())

    def return_par(self):
        """
        Return parameters on exit.
        """
        return self.first, self.last

def ok_cancel_button(parent):
    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
    buttonBox.button(QDialogButtonBox.Ok).setDefault(True)
    buttonBox.accepted.connect(parent.accept)
    buttonBox.rejected.connect(parent.reject)
    # Following is for pyqt4
    #self.connect(buttonBox, SIGNAL("accepted()"),
    #     self, SLOT("accept()"))
    #self.connect(buttonBox, SIGNAL("rejected()"),
    #     self, SLOT("reject()"))
    return buttonBox


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = TraceGUI()
    form.show()
    app.exec_()