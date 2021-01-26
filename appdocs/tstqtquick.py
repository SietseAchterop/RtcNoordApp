# some stuff we need anyway
import sys, os, math, time, csv, yaml, shlex
import locale
from pathlib import Path
import numpy as np
import scipy
import matplotlib.pyplot as plt

# the pyqt stuff
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# if not available, install from package manager or via pip

def runQML():
    app =QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    app.setWindowIcon(QIcon("icon.png"))
    engine.load('main.qml')

    if not engine.rootObjects():
        return -1
    return app.exec_()

if __name__ == "__main__":
    sys.exit(runQML())
