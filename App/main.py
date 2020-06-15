"""First version of the RTCnoord application

Used to process and use the Powerline logger data.
Input is the csv_data that can be extracted from the Powerline software.

This program is a Qt program with a custom backend for use with QtQuick.
Matplotlib is used for the graphs.

"""

import sys, os, math, time, csv, yaml, shlex
import locale
from pathlib import Path

import numpy as np

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType

# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt

app_Path= Path(__file__).parent.absolute() / '..'
be = app_Path  / 'QtQuickBackend'
sys.path.append(str(be))
from backend_qtquick5 import FigureCanvasQTAggToolbar, MatplotlibIconProvider

import globalData as gd

from formpieces import FormPieces
from guirest import *
from utils import *
from profil import *

from report import make_pdf_report

def interactive(session=None):
    """For interactive use in python.

    This function creates the global variables associated with the currently selected session.
    To use this software from the python prompt do the following:

    import globalData as gd
    import main
    main.interactive()

    Now the global data can be used for experiments and development.

    gd.sessionInfo
    import matplotlib.pyplot as plt

    plt.plot(gd.dataObject[:, 2])
    plt.plot(gd.norm_arrays[1, :, 17])

"""

    gd.config = startup()
    gd.globals = readGlobals()
    gd.sessionInfo = selectSession()

    if session is not None:
        gd.config['Session'] = session

    # if data cached, use that.
    file = Path.home() / gd.config['BaseDir'] / 'caches' / (gd.config['Session'] + '.npy')
    try:
        fd = Path.open(file, 'r')
        fd.close()
        gd.dataObject = np.load(file)
    except IOError:
        # first time, when there is no cache yet
        makecache(file)

    # print(gd.sessionInfo)
    pcs = gd.sessionInfo['Pieces']
    p = prof_pieces(pcs)
    if p == []:
        # print(f'Error profiling, number of pieces {len(pcs)}')
        gd.profile_available = False
        self.del_all()
        if gd.profile_available:
            gd.boatPlots.del_all()
        return False

    gd.out = profile(p)


def main():
    """The main entry point when used as a regular app

    It assumes a session is selected. When not, a dummy session None is used.
    A real session can be selected from the menu.
      Either an existing session or a new one using a csv-file.

    """

    gd.config = startup()
    # always start without secondary session
    gd.config['Session2'] = None
    gd.globals = readGlobals()

    # sys_argv = sys.argv
    # sys_argv += ['--style', 'material']
    app = QGuiApplication(sys.argv)
    
    locale.setlocale(locale.LC_NUMERIC, "C");

    # needed for filedialog
    app.setOrganizationName(gd.orgname)
    app.setOrganizationDomain(gd.orgdomain)
    app.setApplicationName(gd.appname)

    qmlRegisterType(FigureCanvasQTAggToolbar, "Backend", 1, 0, "FigureToolbar")
    imgProvider = MatplotlibIconProvider()

    engine = QQmlApplicationEngine(parent=app)
    engine.addImageProvider("mplIcons", imgProvider)
    gd.context = engine.rootContext()

    # Setup pieces
    gd.data_model = DataSensorsModel()
    gd.context.setContextProperty("sensorModel", gd.data_model)
    gd.mainPieces = FormPieces(data=gd.data_model)
    gd.context.setContextProperty("draw_mpl", gd.mainPieces)
    # model to create pieces
    gd.data_model2 = DataPiecesModel()
    gd.context.setContextProperty("makePiecesModel", gd.data_model2)
        
    # View piece
    gd.data_model3 = DataSensorsModel()
    gd.context.setContextProperty("sensorModel3", gd.data_model3)
    # model for secondary session
    gd.data_model4 = DataSensorsModel()
    gd.context.setContextProperty("sensorModel4", gd.data_model4)
    gd.mainView = FormView(data=gd.data_model3, data2=gd.data_model4)
    gd.context.setContextProperty("piece_mpl", gd.mainView)
    gd.data_model5 = DataPiecesModel()
    gd.context.setContextProperty("viewPiecesModel", gd.data_model5)
        
    # Boat
    gd.boattablemodel = BoatTableModel()
    gd.context.setContextProperty("boatTableModel", gd.boattablemodel)
    gd.boatPlots = BoatForm()
    gd.context.setContextProperty("boat_mpl", gd.boatPlots)

    # Crew
    gd.crewPlots = CrewForm()
    gd.context.setContextProperty("crew_mpl", gd.crewPlots)

    # Create rower tables and plots for potentially eight rowers
    for i in range(8):
        gd.rowertablemodel[i] = RowerTableModel(i)
        gd.context.setContextProperty("rowerTableModel"+str(i), gd.rowertablemodel[i])

        gd.rowerPlots[i] = RowerForm(i)
        gd.context.setContextProperty("rower_mpl"+str(i), gd.rowerPlots[i])
        # print(f'main: create the models  rower {i}      {gd.rowerPlots[i].update_figure}')            

    engine.load(str(app_Path / 'App' / 'qml' / 'main.qml'))

    gd.win = engine.rootObjects()[0]

    # set figures functions
    gd.mainPieces.figure = gd.win.findChild(QObject, "pieces").getFigure()
    gd.mainView.figure = gd.win.findChild(QObject, "viewpiece").getFigure()
    gd.boatPlots.figure = gd.win.findChild(QObject, "viewboat").getFigure()
    gd.crewPlots.figure = gd.win.findChild(QObject, "viewcrew").getFigure()

    engine.quit.connect(app.quit)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
