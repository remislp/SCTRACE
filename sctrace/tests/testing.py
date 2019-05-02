import os
import numpy as np
from pylab import *


in_file = 'tmp.csv'
filename, file_extension = os.path.splitext(in_file)
out_file = filename + ".ssd"

record = np.transpose(np.genfromtxt(in_file, delimiter=','))

dt = record[0 , 1] - record[0 , 0]
print("dt= ", dt)
ffilter = 1000 # filter frequency in Hz
npoints = len(record[1])
print("number of points= ", npoints)

trace1 = record[1] * 1000
trace1.astype('int16').tofile("temp.ssd")
#trace2 = np.fromfile("temp.ssd")


fid = open("temp.ssd", 'rb')
fid.seek(512)
#fid.seek(h['ioff'])
trace2 = np.fromfile(fid, 'h')
fid.close()


plot(trace2/1000)
xlabel('#')
ylabel('Y')
grid(True)
show()