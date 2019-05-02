#! /usr/bin/python

__author__ = "Remis Lape"
__date__ = "$03-Aug-2018 09:41:19$"

import os
import sys
import argparse
import struct
import datetime
import numpy as np

def create_parser():
    parser = argparse.ArgumentParser(
        description='DCCONVERTER: csv2ssd script converts two column csv file ' +
                    'into CONSAM ssd format file')
    parser.add_argument('-file', action='store', nargs=1, dest='filename',
                        help='two column csv format input file')
    parser.add_argument('-gain', action='store', dest='gain',
                        default=1.0, type=float,
                        help='V/pA gain factor; default- 1.0; float')
    parser.add_argument('-sampling', action='store', dest='sampling',
                        default=1.0, type=float,
                        help='sampling interval in seconds; default- 1.0; float')
    parser.add_argument('-filter', action='store', dest='filter',
                        default=1.0, type=float,
                        help='filter frequency in Hz; default- 1.0; float')                    
    return parser

def process_args(args):
    if args.filename: in_file = args.filename[0]
    if args.gain: gain = args.gain
    if args.sampling: dt = args.sampling
    if args.filter: filter = args.filter
    return in_file, gain, dt, filter

def ssd_generic_header(gain, dt, filter, npoints):
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
    ssd_h['filt'] = filter
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

def ssd_save(filename, head, data):
    """
    Sava data into Consam ssd format file.
    """
    fout = open(filename, 'wb')
    fout.write(struct.pack('h', 1002))  # version=1002
    title = head['title'] + '.' * 70  # title size 70 characters
    fout.write(str.encode(title[:70]))
    date = head['date'] + '.' * 11  # date size 11 characters. Format 00-ooo-0000
    fout.write(str.encode(date[:11]))
    time = head['time'] + '.' * 8  # time size 8 characters. Format 00-00-00
    fout.write(str.encode(time[:8]))
    fout.write(struct.pack('h', int(head['idt'])))
    fout.write(struct.pack('i', head['ioff']))
    fout.write(struct.pack('i', head['ilen']))
    fout.write(struct.pack('h', head['inc']))
    fout.write(struct.pack('h', head['id1']))
    fout.write(struct.pack('h', head['id2']))
    cs = head['cs'] + '.' * 3  # cs size 3 characters. Format abc
    fout.write(str.encode(cs[:3]))
    fout.write(struct.pack('f', head['calfac']))
    fout.write(struct.pack('f', head['srate']))  # Sample frequency in Hz
    fout.write(struct.pack('f', head['filt']))  # Filter frequency in Hz
    fout.write(struct.pack('f', head['filt1']))
    fout.write(struct.pack('f', head['calfac1']))
    expdate = head['expdate'] + '.' * 11  # date size 11 characters. Format 00-ooo-0000
    fout.write(str.encode(expdate[:11]))
    defname = head['defname'] + '.' * 6  # size 6 characters
    fout.write(str.encode(defname[:6]))
    tapeID = head['tapeID'] + '.' * 24  # size 24 characters 
    fout.write(str.encode(tapeID[:24]))
    fout.write(struct.pack('i', head['ipatch']))
    fout.write(struct.pack('i', head['npatch']))
    fout.write(struct.pack('f', head['Emem']))
    fout.write(struct.pack('f', head['temp']))
    fout.seek(512)
    _data = data * 6553.6
    _data.astype('int16').tofile(fout)
    fout.close()


if __name__ == "__main__":
    parser = create_parser()
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    in_file, gain, dt, filter = process_args(args)
    print ('Converting file: ', in_file)
    filename, file_extension = os.path.splitext(in_file)
    out_file = filename + ".ssd"    
    record = np.transpose(np.genfromtxt(in_file, delimiter=','))
    ssd_head = ssd_generic_header(gain, dt, filter, len(record[1]))
    ssd_save(out_file, ssd_head, record[1]*gain)
    print ('Saved SSD file: ', out_file)
