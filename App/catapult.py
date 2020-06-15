
import os, sys, csv, time
from stat import S_IREAD, S_IRGRP, S_IROTH
from pathlib import Path, PureWindowsPath, PurePosixPath
import numpy as np
from scipy import signal

import globalData as gd

import utils


import matplotlib.pyplot as plt


def catapult():
    """Look for catapult data and use it in the distance column."""

    # not needed
    if not gd.sessionInfo['noDistance']:
        return
    # no catapult file
    path = utils.csvsDir() / (gd.config['Session'] + '_cat.csv')
    if not path.is_file():
        return

    t = time.time()
    print(f'create data from catapult file')
    
    # which dialect
    fd = Path.open(path, newline='')
    dialect = csv.Sniffer().sniff(fd.read(20000))
    fd.seek(0)
    reader = csv.reader(fd, dialect)    

    # skip headers
    #   always 7?
    for i in range(7+1):
        header = next(reader)
    # the last one is the actual header
    lenheader = len(header)

    # read Forward, Vel(100hz), Odometer from catapult-csv file
    catdata = []
    forward = []
    find = header.index(' Forward')
    vel100 = []
    velind = header.index(' Vel(100hz)')
    odometer = []
    odoind = header.index(' Odometer')
    for line, row in enumerate(reader):
        for i in range(lenheader):
            forward.append(float(row[find]))
            vel100.append(float(row[velind]))
            odometer.append(float(row[odoind]))
        catdata.append(row)

    # to numpy
    catacc100 = np.asarray(forward) * 9.81
    vel100 = np.asarray(vel100)
    odo100 = np.asarray(odometer)

    # resample to 50Hz
    catacc50 = signal.decimate(catacc100, 2)
    vel50 = signal.decimate(vel100, 2)
    odo50 = signal.decimate(odo100, 2)

    peachacc = gd.dataObject[:, gd.sessionInfo['Header'].index('Accel')]
    (plength,) = peachacc.shape
    
    # correlatie
    corrarr = np.correlate(peachacc, catacc50, "full")
    # plt.plot(corrarr)
    # plt.show()
    # return

    shift = np.argmax(corrarr)
    print(f'shift  {shift}, time  {(time.time() - t):.1f} seconds.')

    # for now
    plt.plot(catacc50[shift: shift+plength])
    plt.plot(peachacc)
    plt.show()

    # if correct, put values in distance column
    # set gd.noDistance to True

    return
