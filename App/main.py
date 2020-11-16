"""First version of the RTCnoord application

Process and use the Powerline logger data.
Input is the csv_data that can be extracted from the Powerline software.

This program is a Qt program with a custom backend for use with QtQuick.
Matplotlib is used for the graphs.

"""

import os, sys, time, yaml, shlex
import locale
from pathlib import Path

import numpy as np

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType

import matplotlib

import globalData as gd

from formpieces import FormPieces
from guirest import *
from utils import *
from profil import *
#from extensions import *

app = None

def interactive(session=None):
    """For interactive use in python.

    This function creates the global variables associated with the currently selected session.
    To use this software from the python prompt do the following:

    import globalData as gd
    import main
    main.interactive()

    Now the global data can be used for experiments and development.
    For example:

    gd.sessionInfo
    import matplotlib.pyplot as plt

    gd.dataObject.shape
    plt.plot(gd.dataObject[:, 2])
    gd.norm_arrays.shape
    plt.plot(gd.norm_arrays[0, :, 17])

    plt.show()

    result = main.myFirstExtension(1000)
    plt.plot(result)
    ptl.show()

"""
    global app

    gd.config = startup()
    gd.globals = readGlobals(os.getcwd())
    gd.sessionInfo = loadSession()
    gd.p_names = [ nm for nm, be, cr, tl in gd.sessionInfo['Pieces']]

    if gd.config['Session'] is None:
        print('No session selected, should not happen!')
        print('Should be started in the RtcNoordApp/App directory')
        print('   Restart complete interactive session!')
        return
        
    selectCurrentInteractive()

    # if data cached, use that.
    file = cachesDir() / (gd.config['Session'] + '.npy')
    try:
        fd = Path.open(file, 'r')
        fd.close()
        gd.dataObject = np.load(file)
    except IOError:
        # first time, when there is no cache yet
        makecache(file)


    if gd.sessionInfo['Pieces'] == []:
        gd.profile_available = False
        if gd.profile_available:
            gd.boatPlots.del_all()
        return False

    gd.out = profile()
    return True

def main():
    """The main entry point when used as a regular app

    It assumes a session is selected. When not, a dummy session None is used.
    A real session can be created or selected from the menu.
    """
    global app

    # needed for making reports...
    matplotlib.use('Agg')

    app_Path = Path(__file__).parent.absolute() / '..'
    be = app_Path  / 'QtQuickBackend'
    sys.path.append(str(be))
    from backend_qtquick5 import FigureCanvasQTAggToolbar, MatplotlibIconProvider

    gd.config = startup()
    # always start without secondary session
    gd.config['Session2'] = None
    gd.globals = readGlobals()

    # sys_argv = sys.argv
    # sys_argv += ['--style', 'material']
    app = QGuiApplication(sys.argv)
    # app.aboutToQuit.connect(shutdown)
    
    locale.setlocale(locale.LC_NUMERIC, "C");

    # needed for filedialog
    app.setOrganizationName(gd.orgname)
    app.setOrganizationDomain(gd.orgdomain)
    app.setApplicationName(gd.appname)

    qmlRegisterType(FigureCanvasQTAggToolbar, "Backend", 1, 0, "FigureToolbar")
    imgProvider = MatplotlibIconProvider()

    engine = QQmlApplicationEngine()
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

        gd.stretcherPlots[i] = StretcherForm(i)
        gd.context.setContextProperty("stretcher_mpl"+str(i), gd.stretcherPlots[i])
        

    # Session info
    gd.data_model6 = DataBoatsModel()
    gd.context.setContextProperty("sInfoModel", gd.data_model6)
    gd.data_model6.load_boatsInfo()

    engine.load(str(app_Path / 'App' / 'qml' / 'main.qml'))

    gd.win = engine.rootObjects()[0]

    # set figures functions
    gd.mainPieces.figure = gd.win.findChild(QObject, "pieces").getFigure()
    gd.mainView.figure = gd.win.findChild(QObject, "viewpiece").getFigure()
    gd.boatPlots.figure = gd.win.findChild(QObject, "viewboat").getFigure()
    gd.crewPlots.figure = gd.win.findChild(QObject, "viewcrew").getFigure()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


#######  Place for extention functions to be used in an interactive session.

def myFirstExtension(n):
    # some stuff with the data
    s_1_data = gd.dataObject[0:n, 1]
    s_2_data = gd.dataObject[0:n, 2]
    return s_1_data + s_2_data


####### End of extentions

    
