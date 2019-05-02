# -*- coding: utf-8 -*-
"""
Created on Thursday Aug 2 10:43:02 2018

@author: Remis Lape
"""

import os
import sys
import struct
import datetime
from array import array
import numpy as np

from pylab import *

def ssd_read_header (filename, verbose=False):
    """
    Read the header of a Consam file.
    """
    
    floats = array ('f')
    ints = array('i')
    shorts = array ('h')
    h = {}
    f = open(filename, 'rb')
    
#    if verb: 
#        print("Full header from CONSAM file %s is as follows:" + filename)
#    else:
#        print("Highlights of CONSAM header from %s" + filename)
        
    shorts.fromfile(f,1)
    h['version'] = shorts.pop()
    if verbose: print("Version:", h['version']) # iver =1002 is new, =1001 is old

    h['title'] = f.read(70)
#    print "Title:", h['title']

    h['date'] = f.read(11)
    if verbose: print ("Acquisition date:", h['date'])

    h['time'] = f.read(8)
    if verbose: print ("Acquisition time:", time)
 
    shorts.fromfile(f,1)
    h['idt'] = shorts.pop()
    if verbose: print ("idt:", idt)
 
    ints.fromfile(f,1)
    h['ioff'] = ints.pop()
    if verbose: print ("ioff:", ioff)

    ints.fromfile(f,1)
    h['ilen'] = ints.pop()
    if verbose:
        print ("ilen:", ilen)
        print ('Attention! ilen gives length in bites, so- number of points is half of ilen')

    shorts.fromfile(f,1)
    h['inc'] = shorts.pop()
#    if verb: print "inc:", inc

    shorts.fromfile(f,1)
    h['id1'] = shorts.pop()
#    if verb: print "id1:", id1

    shorts.fromfile(f,1)
    h['id2'] = shorts.pop()
#    if verb: print "id2:", id2

    h['cs'] = f.read(3)
#    if verb: print "cs:", cs

    floats.fromfile(f,1)
    h['calfac'] = floats.pop()
#    print "calfac:", calfac

    floats.fromfile(f,1)
    h['srate'] = floats.pop()
#    print "Sample frequency: %i Hz" %int (srate)

    floats.fromfile(f,1)
    h['filt'] =floats.pop()
#    print "Filter frequency: %i Hz" %int (filt)

    floats.fromfile(f,1)
    h['filt1'] = floats.pop()
    floats.fromfile(f,1)
    h['calfac1'] = floats.pop()
    h['expdate'] = f.read(11)
    h['defname'] = f.read(6)
    h['tapeID'] = f.read(24)
    ints.fromfile(f,1)
    h['ipatch'] = ints.pop()
    ints.fromfile(f,1)
    h['npatch'] = ints.pop()
    floats.fromfile(f,1)
    h['Emem'] = floats.pop()
    floats.fromfile(f,1)
    h['temp'] = floats.pop()

    f.close()
    return h

def ssd_read_data(filename, h):
    """
    Read data from Consam ssd or dat file.
    """

    fid = open(filename, 'rb')
    fid.seek(h['ioff'])
    trace = np.fromfile(fid, 'h') * h['calfac']
    fid.close()

    return trace

def ssd_save(filename, head, data):
    """
    Sava data into Consam ssd format file.
    """
    
    fout = open(filename, 'wb')
    
    fout.write(struct.pack('h', 1002))  # version=1002

    k = len(head['title'])  # title size 70 characters
    if k < 70:
        for i in range(k, 70):
            head['title'] += '.'
    elif k > 70:
        head['title'] = head['title'][0:70]
    fout.write(str.encode(head['title']))

    k = len(head['date'])  # date size 11 characters. Format 00-ooo-0000
    if k < 11:
        for i in range(k, 11):
            head['date'] += "."
    elif k > 11:
        head['date'] = head['date'][0:11]
    fout.write(str.encode(head['date']))
    
    k = len(head['time'])  # time size 8 characters. Format 00-00-00
    if k < 8:
        for i in range(k, 8):
            head['time'] += "."
    elif k > 8:
        head['time'] = head['time'][0:8]
    fout.write(str.encode(head['time']))

    fout.write(struct.pack('h', int(head['idt'])))
    fout.write(struct.pack('i', head['ioff']))
    fout.write(struct.pack('i', head['ilen']))
    fout.write(struct.pack('h', head['inc']))
    fout.write(struct.pack('h', head['id1']))
    fout.write(struct.pack('h', head['id2']))

    k = len(head['cs'])  # cs size 3 characters. Format abc
    if k < 3:
        for i in range(k, 3):
            head['cs'] += "."
    elif k > 3:
        head['cs'] = head['cs'][0:3]
    fout.write(str.encode(head['cs']))

    fout.write(struct.pack('f', head['calfac']))
    fout.write(struct.pack('f', head['srate']))  # Sample frequency in Hz
    fout.write(struct.pack('f', head['filt']))  # Filter frequency in Hz
    fout.write(struct.pack('f', head['filt1']))
    fout.write(struct.pack('f', head['calfac1']))

    k = len(head['expdate'])  # date size 11 characters. Format 00-ooo-0000
    if k < 11:
        for i in range(k, 11):
            head['expdate'] += "."
    elif k > 11:
        head['expdate'] = head['expdate'][0:11]
    fout.write(str.encode(head['expdate']))

    k = len(head['defname'])  # date size 11 characters. Format 00-ooo-0000
    if k < 6:
        for i in range(k, 6):
            head['defname'] += "."
    elif k > 6:
        head['defname'] = head['defname'][0:6]
    fout.write(str.encode(head['defname']))

    k = len(head['tapeID'])  # date size 11 characters. Format 00-ooo-0000
    if k < 24:
        for i in range(k, 24):
            head['tapeID'] += "."
    elif k > 24:
        head['tapeID'] = head['tapeID'][0:24]
    fout.write(str.encode(head['tapeID']))

    fout.write(struct.pack('i', head['ipatch']))
    fout.write(struct.pack('i', head['npatch']))
    fout.write(struct.pack('f', head['Emem']))
    fout.write(struct.pack('f', head['temp']))

    fout.seek(512)
    _data = data * 6553.6
    _data.astype('int16').tofile(fout)

    fout.close()


def ssd_generic_header(dt, ffilter, npoints, gain):
    ssd_h = {}
    now = datetime.datetime.now()

    ssd_h['version'] = np.int16(1002)
    ssd_h['title'] = "Converted from column"

    ssd_h['date'] = now.strftime("%d-%b-%Y")
    ssd_h['time'] = now.strftime("%H-%M-%S")

    ssd_h['idt'] = dt
    ssd_h['ioff'] = int(512)
    ssd_h['ilen'] = npoints
    ssd_h['inc'] = np.int16(1)
    ssd_h['id1'] = np.int16(0)
    ssd_h['id2'] = np.int16(0)

    ssd_h['cs'] = "H"

    ssd_h['calfac'] = float(1.0 / (gain * 6553.6))
    ssd_h['srate'] = float(1e6 / dt)
    ssd_h['filt'] = ffilter
    ssd_h['filt1'] = float(0.0)
    ssd_h['calfac1'] = float(0.0)

    ssd_h['expdate'] = now.strftime("%d-%b-%Y")
    ssd_h['defname'] = "Converted"
    ssd_h['tapeID'] = "Converted"

    ssd_h['ipatch'] = int(3)
    ssd_h['npatch'] = int(1)
    ssd_h['Emem'] = float(0.0)
    ssd_h['temp'] = float(0.0)
    return ssd_h

if __name__ == "__main__":
    
    in_file = 'tmp.csv'
    filename, file_extension = os.path.splitext(in_file)
    out_file = filename + ".ssd"
    
    record = np.transpose(np.genfromtxt(in_file, delimiter=','))
    dt = record[0 , 1] - record[0 , 0]
    print("dt= ", dt)
    ffilter = 1000 # filter frequency in Hz
    npoints = len(record[1])
    print("number of points= ", npoints)
    
    gain = 1
    ssd_head = ssd_generic_header(dt, ffilter, npoints, gain)
    
    ssd_save(out_file, ssd_head, record[1]*gain)
    print ('Saved SSD file: ', out_file)
    
    
    #ssd_head2 = ssd_read_header(out_file, verbose=True)
    trace = ssd_read_data(out_file, ssd_head)
    calfac = float(1.0 / (gain * 6553.6))

    #plot(record[1] * 1000)
    plot(record[1], trace * calfac)
    xlabel('#')
    ylabel('Y')
    grid(True)
    show()
    
    