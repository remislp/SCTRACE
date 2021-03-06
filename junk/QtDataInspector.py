#! /usr/bin/env python
"""
ClusterInspector- load idealised single channel records and inspect 
clusters/bursts.
"""
import sys
import os
from math import log10, pow
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import numpy as np

from dcpyps import dcio
from dcpyps import dataset
from scalcs import scplotlib as scpl
#from dcpyps import scplotlib as scpl
from dcpyps.reports import ClusterReportHTML

class DataInspector(QMainWindow):
    def __init__(self, parent=None):
        super(DataInspector, self).__init__(parent)
        self.resize(900, 600)     # wide, high in px
        self.mainFrame = QWidget()
        self.setWindowTitle("DC_PyPs: DataInspector- load idealised " +
            "single channel records and inspect clusters/bursts.")
        area = DockArea()
        self.setCentralWidget(area)

        self.path = None
        self.recs = []
        self.curr_rec = -1
        self.curr_burst = -1
        
#        d1 = Dock("Dock1", size=(1, 1))
        d1 = PatchInspector(self)
        area.addDock(d1, 'left')
        self.d2 = BurstPlots(self)
        area.addDock(self.d2, 'right')

    def update(self):
        self.d2.update()
    def clear(self):
        self.recs = []
        self.d2.clear()

class BurstPlots(Dock):
    def __init__(self, parent):
        super(BurstPlots, self).__init__(parent)
        self.parent = parent
        self.min_op = 2
        
        self.plt1 = pg.PlotWidget()
        self.plt2 = pg.PlotWidget()
        self.plt3 = pg.PlotWidget()
        self.plt4 = pg.PlotWidget()
        self.spB1 = pg.SpinBox(value=self.min_op, step=1, bounds=(2,100))
        self.spB1.sigValueChanged.connect(self.spinBox1Changed)

        self.exportBtn1 = QPushButton('Export Popen distribution to TXT')
        self.exportBtn1.clicked.connect(self.export1)
        self.exportBtn3 = QPushButton('Export MOP v Popen to TXT')
        self.exportBtn3.clicked.connect(self.export3)

        
        w2 = pg.LayoutWidget()
        w2.addWidget(QLabel('Use clusters with number of openings more than:'), row=0, col=0, colspan=3)
        w2.addWidget(self.spB1, row=0, col=3)
        w2.addWidget(self.plt1, row=1, col=0, colspan=4)
        w2.addWidget(self.exportBtn1, row=2, col=3)
        w2.addWidget(self.plt2, row=3, col=0, colspan=4)
        w2.addWidget(self.plt3, row=4, col=0, colspan=4)
        w2.addWidget(self.exportBtn3, row=5, col=3)
        w2.addWidget(self.plt4, row=6, col=0, colspan=4)

        self.addWidget(w2)
        
    def update(self):

        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt4.clear()

        self.all_popen = dataset.all_popen(self.parent.recs, self.min_op)
        self.opav = dataset.opav(self.parent.recs, self.min_op)            
        self.y1,self.x1 = np.histogram(np.array(self.all_popen)) #, bins=np.linspace(-3, 8, 40))
        hist = pg.PlotCurveItem(self.x1, self.y1, stepMode=True, fillLevel=0, brush=(0, 0, 255, 80))
        self.plt1.addItem(hist)
        self.plt1.setXRange(0, 1) #, padding=None, update=True)
        self.plt1.setLabel('bottom', "Popen")
        self.plt1.setLabel('left', "Count #")
        self.plt1.setTitle("Mean Popen= {0:.3f}; # of clusters= {1:d}".
            format(np.average(np.array(self.all_popen)), len(self.all_popen)))
        
        y,x = np.histogram(np.array(self.opav)) #, bins=np.linspace(-3, 8, 40))
        hist = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 80))
        self.plt2.addItem(hist)
        self.plt2.setLabel('bottom', "Opening mean length", units='s')
        self.plt2.setLabel('left', "Count #")
        
        self.plt3.plot(np.array(self.all_popen), np.array(self.opav)*1000,  pen=None, symbol='o', symbolPen='b', symbolSize=5, symbolBrush='b')
        self.plt3.setLabel('left', "Opening mean length", units='ms')
        self.plt3.setLabel('bottom', "Popen")
        self.plt3.setXRange(0, 1)

        #self.plt9.plot(np.array(all_popen), np.array(all_mean_ampl),  pen=None, symbol='o', symbolPen='b', symbolSize=5, symbolBrush='b')
        self.plt4.setLabel('left', "Mean amplitude", units='pA')
        self.plt4.setLabel('bottom', "Popen")
        self.plt4.setXRange(0, 1)

    def export1(self):
        fname = QFileDialog.getSaveFileName(self,
                "Save as TXT file...", self.parent.path, ".txt",
                "TXT files (*.txt)")
        fout = open(fname,'w')
        for i in range(len(self.x1)):
            fout.write('{0:.6e}\t'.format(self.x1[i]))
            fout.write('{0:.6e}\t'.format(self.y1[i]))
            fout.write('\n')
        fout.close()

    def export3(self):
        fname = QFileDialog.getSaveFileName(self,
                "Save as TXT file...", self.parent.path, ".txt",
                "TXT files (*.txt)")
        fout = open(fname,'w')
        for i in range(len(self.all_popen)):
            fout.write('{0:.6e}\t'.format(self.all_popen[i]))
            fout.write('{0:.6e}\t'.format(self.opav[i]))
            fout.write('\n')
        fout.close()

    def spinBox1Changed(self):
        val = self.spB1.value()
        self.min_op = val
        self.update()

    def clear(self):
        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt4.clear()


class PatchInspector(Dock):
    def __init__(self, parent):
        super(PatchInspector, self).__init__(parent)
        self.parent = parent
        #self.title = "Patch Inspector"
        #self.resize=(1, 1)
        
        self.ma_period1 = 10
        self.ma_period2 = 2
        self.tres_all = Qt.Unchecked
        self.tcrit_all = Qt.Unchecked

        self.textBox = QTextBrowser()
        self.spB4 = pg.SpinBox(value=parent.curr_rec+1, step=1)
        self.spB4.sigValueChanged.connect(self.spinBox4Changed)

        self.loadBtn = QPushButton('Load idealised record(s)')
        self.removeBtn = QPushButton('Remove current record')
        self.saveBtn = QPushButton('Save current session')
        self.clearBtn = QPushButton('Delete all records')
        self.loadBtn.clicked.connect(self.load)
        self.removeBtn.clicked.connect(self.remove)
        self.removeBtn.setEnabled(False)
        self.saveBtn.setEnabled(False)
        self.clearBtn.setEnabled(False)
        self.clearBtn.clicked.connect(self.clear)

        self.spB1 = pg.SpinBox(suffix='s', siPrefix=True, step=1e-6, bounds=(1e-6,1e-3))
        self.spB1.sigValueChanged.connect(self.spinBox1Changed)
        self.ckB1 = QCheckBox('Impose to all loaded patches?', self)
        self.ckB1.setCheckState(self.tres_all)
        self.ckB1.stateChanged.connect(self.checkBox1Changed)

        self.spB2 = pg.SpinBox(suffix='s', siPrefix=True, step=1e-6, bounds=(1e-5,1))
        self.spB2.sigValueChanged.connect(self.spinBox2Changed)
        self.ckB2 = QCheckBox('Impose to all loaded patches?', self)
        self.ckB2.setCheckState(self.tcrit_all)
        self.ckB2.stateChanged.connect(self.checkBox2Changed)

        self.plt1 = pg.PlotWidget()
        self.plt2 = pg.PlotWidget()
        self.plt3 = pg.PlotWidget()
        self.plt3.setTitle("Stability plots: open periods- red, shut periods- green, Popen- blue")

        self.plt4 = pg.PlotWidget()
        self.plt5 = pg.PlotWidget()
        self.spB3 = pg.SpinBox(value=self.ma_period1, step=1, bounds=(1,100))
        self.spB3.sigValueChanged.connect(self.spinBox3Changed)

        w1 = pg.LayoutWidget()

        w1.addWidget(self.loadBtn, row=0, col=0)
        w1.addWidget(self.removeBtn, row=0, col=1)
        w1.addWidget(self.saveBtn, row=0, col=2)
        w1.addWidget(self.clearBtn, row=0, col=3)

        w1.addWidget(self.textBox, row=1, col=0, colspan=4)

        w1.addWidget(QLabel('Displaying patch '), row=2, col=0)
        w1.addWidget(self.spB4, row=2, col=1)
        self.label1 = QLabel(' out of {0:d}'.format(len(parent.recs)))
        w1.addWidget(self.label1, row=2, col=2)
        self.spB4.setMaximum(len(parent.recs))
        self.spB4.setMinimum(0)

        w1.addWidget(self.plt1, row=3, col=0, colspan=2)
        w1.addWidget(self.plt2, row=3, col=2, colspan=2)
        w1.addWidget(QLabel('tres:'), row=4, col=0)
        w1.addWidget(self.spB1, row=4, col=1)
        w1.addWidget(self.ckB1, row=4, col=2, colspan=2)

        w1.addWidget(QLabel('tcrit:'), row=5, col=0)
        w1.addWidget(self.spB2, row=5, col=1)
        w1.addWidget(self.ckB2, row=5, col=2, colspan=2)

        w1.addWidget(self.plt3, row=6, col=0, colspan=4)
        w1.addWidget(QLabel('Moving average period for all record:'), row=7, col=0, colspan=2)
        w1.addWidget(self.spB3, row=7, col=2)

        # Single cluster Popen stability plot
        self.plt6 = pg.PlotWidget()
        self.spB5 = pg.SpinBox(value=self.ma_period2, step=1, bounds=(1,100))
        self.spB5.sigValueChanged.connect(self.spinBox5Changed)
        self.spB6 = pg.SpinBox(value=self.parent.curr_burst+1, step=1) # , bounds=(1,100))
        self.spB6.sigValueChanged.connect(self.spinBox6Changed)
        self.exportBtn1 = QPushButton('Export current burst to TXT')
        self.exportBtn1.clicked.connect(self.export1)
        w1.addWidget(self.plt6, row=8, col=0, colspan=4)
        w1.addWidget(QLabel('Moving average period for a single burst:'), row=9, col=0)
        w1.addWidget(self.spB5, row=9, col=1)
        w1.addWidget(QLabel('Burst #:'), row=9, col=2)
        w1.addWidget(self.spB6, row=9, col=3)
        w1.addWidget(self.exportBtn1, row=10, col=3)

        self.addWidget(w1)

    def update(self):

        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt6.clear()

        self.label1.setText(' out of {0:d}'.format(len(self.parent.recs)))
        self.spB4.setMaximum(len(self.parent.recs))
        self.spB4.setValue(self.parent.curr_rec+1)
        if self.parent.recs:
            self.spB4.setMinimum(1)

        ox, oy, dx = dataset.prepare_hist(np.array(self.parent.recs[self.parent.curr_rec].opint),
            self.parent.recs[self.parent.curr_rec].tres)
        self.plt1.plot(ox, oy, stepMode=True, fillLevel=0,
            brush=(0, 0, 255, 80))
        self.tresLine1 = pg.InfiniteLine(angle=90, movable=True, pen='r')
        self.tresLine1.setValue(log10(self.parent.recs[self.parent.curr_rec].tres))
        self.tresLine1.sigPositionChangeFinished.connect(self.tresLine1Changed)
        self.plt1.addItem(self.tresLine1)
        self.plt1.setLogMode(x=True, y=False)
        self.plt1.setLabel('bottom', "Open periods", units='s')
        self.plt1.setLabel('left', "Count #")

        sx, sy, dx = dataset.prepare_hist(np.array(self.parent.recs[self.parent.curr_rec].shint),
            self.parent.recs[self.parent.curr_rec].tres)
        self.plt2.plot(sx, sy, stepMode=True, fillLevel=0,
            brush=(0, 0, 255, 80))
        self.tresLine2 = pg.InfiniteLine(angle=90, movable=True, pen='r')
        self.tresLine2.setValue(log10(self.parent.recs[self.parent.curr_rec].tres))
        self.tcritLine = pg.InfiniteLine(angle=90, movable=True, pen='y')
        self.tcritLine.setValue(log10(self.parent.recs[self.parent.curr_rec].tcrit))
        self.tresLine2.sigPositionChangeFinished.connect(self.tresLine2Changed)
        self.tcritLine.sigPositionChangeFinished.connect(self.tcritLineChanged)
        self.plt2.addItem(self.tresLine2)
        self.plt2.addItem(self.tcritLine)
        self.plt2.setLogMode(x=True, y=False)
        self.plt2.setLabel('bottom', "Shut periods",  units='s') #, units='ms')
        self.plt2.setLabel('left', "Count #")
        self.spB1.setValue(self.parent.recs[self.parent.curr_rec].tres)
        self.spB2.setValue(self.parent.recs[self.parent.curr_rec].tcrit)
        self.spB3.setValue(self.ma_period1)

        opma = dataset.moving_average(self.parent.recs[self.parent.curr_rec].opint, self.ma_period1)
        shma = dataset.moving_average(self.parent.recs[self.parent.curr_rec].shint, self.ma_period1)
        poma = opma / (opma + shma)
        x = np.linspace(0, np.prod(opma.shape), num=np.prod(opma.shape)+1, endpoint=True)
        self.plt3.plot(x, opma, stepMode=True,pen='r', name='Open periods')
        self.plt3.plot(x, poma, stepMode=True,pen='b', name='Popen')
        self.plt3.plot(x, shma, stepMode=True,pen='g', name='Shut periods')
        self.plt3.setLabel('bottom', "Interval #")
        self.plt3.setLogMode(x=False, y=True)
        self.tcritLine2 = pg.InfiniteLine(angle=0, movable=False, pen='y')
        self.tcritLine2.setValue(log10(self.parent.recs[self.parent.curr_rec].tcrit))
        self.plt3.addItem(self.tcritLine2)
        
        clusters = self.parent.recs[self.parent.curr_rec].bursts.get_long(2)
        cluster_num = clusters.count()
        all_op_list = clusters.get_op_lists()
        all_sh_list = clusters.get_sh_lists()
        if self.ma_period2 < clusters.bursts[self.parent.curr_burst].get_openings_number() - 1:
            copma = dataset.moving_average(all_op_list[self.parent.curr_burst][:-1], self.ma_period2)
            cshma = dataset.moving_average(all_sh_list[self.parent.curr_burst], self.ma_period2)
            self.cpoma = copma / (copma + cshma)
            x = np.linspace(0, np.prod(self.cpoma.shape), 
                num=np.prod(self.cpoma.shape)+1, endpoint=True)
            self.plt6.plot(x, self.cpoma, stepMode=True,pen='g')
        else:
            pass
        self.plt6.setLabel('left', "Popen")
        self.plt6.setLabel('bottom', "Interval #")
        self.plt6.setYRange(0, 1)
        self.plt6.setTitle("Single burst stability plot; Popen= {0:.3f}; # of open periods= {1:d}".
            format(clusters.bursts[self.parent.curr_burst].get_popen1(),
            clusters.bursts[self.parent.curr_burst].get_openings_number()))

        self.spB5.setValue(self.ma_period2)
        self.spB6.setValue(self.parent.curr_burst+1)
        self.spB6.setMaximum(cluster_num)
        self.spB6.setMinimum(1)

        self.parent.update()

    def export1(self):
        fname = QFileDialog.getSaveFileName(self,
                "Save as TXT file...", self.parent.path, ".txt",
                "TXT files (*.txt)")
        fout = open(fname,'w')
        for i in range(len(self.cpoma)):
            fout.write('{0:.6e}\n'.format(self.cpoma[i]))
        fout.close()

    def update_tres(self, tres):
        if self.tres_all:
            for rec in self.parent.recs:
                rec.tres = tres
            #self.parent.curr_rec = 0
        else:
            self.parent.recs[self.parent.curr_rec].tres = tres
        self.parent.curr_burst = 0
        self.update()
    def update_tcrit(self, tcrit):
        if self.tcrit_all:
            for rec in self.parent.recs:
                rec.tcrit = tcrit
            #self.parent.curr_rec = 0
        else:
            self.parent.recs[self.parent.curr_rec].tcrit = tcrit
        self.parent.curr_burst = 0
        self.update()

    def tresLine1Changed(self):
        val = self.tresLine1.value()
        self.update_tres(pow(10, val))
    def tresLine2Changed(self):
        val = self.tresLine2.value()
        self.update_tres(pow(10, val))
    def tcritLineChanged(self):
        val = self.tcritLine.value()
        self.update_tcrit(pow(10, val))

    def spinBox1Changed(self):
        tres = self.spB1.value()
        self.update_tres(tres)
    def spinBox2Changed(self):
        tcrit = self.spB2.value()
        self.update_tcrit(tcrit)
    def spinBox3Changed(self):
        val = self.spB3.value()
        self.ma_period1 = val
        self.update()
    def spinBox4Changed(self):
        val = self.spB4.value()
        self.parent.curr_rec = int(val-1)
        self.parent.curr_burst = 0
        self.update()
    def spinBox5Changed(self):
        val = self.spB5.value()
        self.ma_period2 = val
        self.update()
    def spinBox6Changed(self):
        val = self.spB6.value()
        self.parent.curr_burst = int(val-1)
        self.update()

    def checkBox1Changed(self):
        if self.ckB1.checkState() > 0:
            self.tres_all = True
        else:
            self.tres_all = False
        self.update_tres(self.spB1.value())
    def checkBox2Changed(self):
        if self.ckB2.checkState() > 0:
            self.tcrit_all = True
        else:
            self.tcrit_all = False
        self.update_tcrit(self.spB2.value())

    def load(self):
        filelist = QFileDialog.getOpenFileNames(self.parent,
            "Open CSV file(s) (Clampfit idealised data saved in EXCEL csv file)...",
            self.parent.path, "CSV file  (*.csv);;SCN files (*.scn *.SCN)")
        for filename in filelist:
            self.parent.path, fname = os.path.split(filename)
            if fname.split(".")[1] == "csv":
                fscname = dcio.convert_clampfit_to_scn(filename)
                self.textBox.append('Converted to SCAN file: '+fscname) #+'\n')
            elif fname.split(".")[1] == "scn" or fname.split(".")[1] == "SCN":
                fscname = filename
                self.textBox.append('Loaded SCAN file: '+fscname) #+'\n')
            self.parent.recs.append(dataset.SCRecord([fscname]))
        
        self.parent.curr_rec = 0
        self.update()
        self.parent.update()
        self.clearBtn.setEnabled(True)
#        self.saveBtn.setEnabled(True)
        self.removeBtn.setEnabled(True)
        
    def save(self):
        pass
    def remove(self):
        self.parent.recs.pop(self.parent.curr_rec)
        self.parent.curr_rec = len(self.parent.recs) - 1
        self.update()
    def clear(self):
        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt6.clear()
        
        self.textBox.clear()
        self.clearBtn.setEnabled(False)
        self.saveBtn.setEnabled(False)
        self.removeBtn.setEnabled(False)
        self.parent.clear()


if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    form = DataInspector()
    form.show()
    app.exec_()