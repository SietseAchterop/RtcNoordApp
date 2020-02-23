"""The Gui related classes for the RTCnoord app."""

import os, sys, re, yaml, time, math
from stat import S_IREAD, S_IRGRP, S_IROTH
from pathlib import Path

import traceback

from shutil import copyfile, move
from pathlib import Path, PureWindowsPath, PurePosixPath
import numpy as np
from scipy.interpolate import interp1d

from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty, QMetaObject, Qt, QTimer, QByteArray, QAbstractListModel, QModelIndex
from PyQt5.QtGui import QColor
from PyQt5.QtQml import QJSValue

import globalData as gd

from utils import *

from models import *

import matplotlib.pyplot as plt

# matplotlib plot in Pieces
class FormPieces(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, tempi=[]):
        QObject.__init__(self, parent)

        s = gd.config['Session']
        if s == 'None':
            self._status_text = 'No session loaded, please create or load a session via the menu.'
        else:
            self._status_text = s            

        self._figure = None
        self.ax1 = None
        self.ax2 = None

        # in seconds
        self.xFrom = 0
        self.xTo = 1
        self._starttime = 0

        self.traceCentre = 30  # halverwege de x-as
        self.scale = 1
        self.scale_r = 1
        self.panon = False
        self.pandistance = 0
        self.panbase = self.traceCentre
        
        # with legends it becomes slow
        self._legend = False

        self._data = data
        # tempi en traces komen nu later
        self._tempi = tempi
        self._traces = None
        self.pieceWidth = 60
        self.times = []
        
        # markers
        self.tempoline = None
        self.markers_ax1 = None
        self.markers_ax2 = None
        
        # the pieces are put in data_model2
        # markers to be set
        self.mbegin = 0
        self.mend = 0

        # mode:   0:uit, 1:begin, 2:end,  3: creer gui entry en -> 1  (via qui -> 0)
        self.pmode = 0

    def onclick_d(self, event):
        try:
            """
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            """
            if event.inaxes == self.ax1:
                # ax1 processing
                #   zetten pieces (button 1)
                if event.button == 1:
                    if self.pmode == 1:
                        b = int(event.xdata*Hz)
                        # we start a piece 2/5 second before the catch, better for displaying
                        self.mbegin = n_catches(1, b)[0]-20
                        self.pmode = 2
                    elif self.pmode == 2:
                        self.mend = int(event.xdata*Hz)
                        self.pmode = 3
                    elif self.pmode == 3:
                        # will not occurr when the piece is accepted
                        print('set point in traces 3, remove markers')
                        self.pmode = 1
                elif event.button == 3:
                    # panning start
                    self.panon = True
                    self.pandistance = event.x
                    self.panbase = self.traceCentre

            elif event.inaxes == self.ax2:
                # ax2 processing
                # pos = selfelf.ax1.get_position()
                # print(pos)
                # draw new line
                self.tempoline.remove()
                self.tempoline = self.ax2.vlines(event.xdata, 0, 20,
                                                 transform=self.ax2.get_xaxis_transform(), colors='r')
                self.traceCentre = event.xdata
                self.xFrom = self.traceCentre - 100
                self.xTo = self.traceCentre + 100
                
                self.update_figure()
            else:
                #  ook hier verschillende buttons verwerken
                pass
            
        except TypeError:
            # clicked outside the plot, ignore
            pass


    # cid = fig.canvas.mpl_connect('button_press_event', onclick)
    # fig.canvas.mpl_disconnect(cid)

    def onclick_u(self, event):
        try:
            if event.inaxes == self.ax1:
                # button 3, maar gaat altijd goed
                # panning stop
                self.panon = False
        except TypeError:
            pass

    def onscroll(self, event):
        try:
            if event.inaxes == self.ax1:
                self.scale += event.step*0.05
                if self.scale < 0.05:
                    self.scale = 0.05
                self.update_figure()
            elif event.inaxes == self.ax2:
                pass
            else:
                pass

        except TypeError:
            pass

    def onnotify(self, event):
        try:
            if event.inaxes == self.ax1:
                # button 3, maar gaat altijd goed
                if self.panon:
                    diff = (self.pandistance - event.x)
                    self.traceCentre = self.panbase + diff*0.2
                    self.update_figure()
        except TypeError:
            pass
        

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.7)
        gs = self._figure.add_gridspec(3, 3)
        self.ax1 = self._figure.add_subplot(gs[0:2, :])
        self.ax2 = self._figure.add_subplot(gs[-1, :])

        self.ax1.set_title('Traces')
        self.ax2.set_title('Rating')

        self.tempoline = self.ax2.vlines(7, -10, 10, transform=self.ax2.get_xaxis_transform(), colors='r')

        # to set positions
        # pos1 = ax.get_position() # get the original position 
        # pos2 = [pos1.x0 + 0.3, pos1.y0 + 0.3,  pos1.width / 2.0, pos1.height / 2.0] 
        # ax.set_position(pos2) # set a new position

        # set limits
        # ax.get_xlim()
        # ax.set_xlim(a, b)
        
        cid1 = fig.canvas.mpl_connect('button_press_event', self.onclick_d)
        cid2 = fig.canvas.mpl_connect('button_release_event', self.onclick_u)
        cid3 = fig.canvas.mpl_connect('scroll_event', self.onscroll)
        cid4 = fig.canvas.mpl_connect('motion_notify_event', self.onnotify)

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)

        self.update_tempo_figure()
        
    @pyqtProperty('QString', notify=statusTextChanged)
    def statusText(self):
        return self._status_text
    
    @statusText.setter
    def statusText(self, text):
        if self._status_text != text:
            self._status_text = text
            self.statusTextChanged.emit()

    @pyqtProperty(bool, notify=legendChanged)
    def legend(self):
        return self._legend
    
    @legend.setter
    def legend(self, legend):
        if self.figure is None:
            return
            
        if self._legend != legend:
            self._legend = legend
            if self._legend:
                self.axes.legend()
            else:
                leg = self.axes.get_legend()
                if leg is not None:
                    leg.remove()
            self.legendChanged.emit()
            print('lengend')

    # twee functies voor de twee subplots?
    @pyqtSlot()
    def update_tempo_figure(self):
        if self.figure is None:
            return
    
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Rating')
        
        q = [list(t) for t in zip(*self._tempi)]
        if len(q) !=  0:
            t = [i/Hz for i in q[0]]            
            self.ax2.plot(t, q[1], linewidth=0.6)
            self.ax2.set_xlim((0, len(self._traces)/Hz))
        
        # set all prepared ax2 markers here
        #     marker tempoline is done in onclick
        for d in gd.data_model2.alldata():
            b, e = d.data()
            self.ax2.plot([b/Hz], [0], marker='>', color='g')
            self.ax2.plot([e/Hz], [0], marker='<', color='r')

        self.stateChanged.emit()
        

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Traces')

        has_series = False

        for row in range(self._data.rowCount()):
            model_index = self._data.index(row, 0)
            checked = self._data.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data.data(model_index, DataSensorsModel.NameRole)                
                i = self._data.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._traces[1: -1, i]
                self.ax1.plot(self.times, values, linewidth=0.6,  label=name)

        # set all prepared ax1 markers here
        for d in gd.data_model2.alldata():
            b, e = d.data()
            self.ax1.plot([b/Hz], [0], marker='>', color='g')
            self.ax1.plot([e/Hz], [0], marker='<', color='r')

        # self.ax1.set_xlim((self.xFrom, self.xTo))
        self.ax1.plot([self.traceCentre], [0], marker='D', color='b')        
        self.ax1.set_xlim((self.traceCentre - self.pieceWidth*self.scale, self.traceCentre + self.pieceWidth*self.scale))

        dist = (self.xTo - self.xFrom)
        xFrom = self.traceCentre - self.scale*dist/2
        xTo = self.traceCentre + self.scale*dist/2

        self.ax1.set_xlim(xFrom, xTo)
        # start at correct beginvalue
        locs = self.ax1.get_xticks()
        ticks = [item+self._starttime for item in locs]
        self.ax1.set_xticklabels(ticks)

        if has_series and self.legend:
            self.ax1.legend()

        self.stateChanged.emit()
        
    def update_figures(self):
        self.update_figure()
        self.update_tempo_figure()

    @pyqtSlot(str)
    def new_piece(self, name):
        #  Button "New Piece" processing
        
        if self.pmode == 0:
            self.pmode = 1
        if self.pmode == 3:
            # create new piece
            # the profile pieces (start, t20, t24, t28, t32, max) should be contiguous
            #   we could test for this, and signal is using the delete button for the piece.
            gd.data_model2.add_piece(name, (self.mbegin, self.mend))
            self.update_figures()
            self.pmode = 0

    @pyqtSlot(str)
    def remove_piece(self, index):
        gd.data_model2.del_piece(index)
        self.update_figures()
        
    @pyqtSlot()
    def savepieces(self):
        gd.sessionInfo['Pieces'] = [(i.name(), i.data()) for i in gd.data_model2.alldata()]
        saveSessionInfo(gd.sessionInfo)
        gd.boattablemodel.make_profile()

    @pyqtProperty(list, notify=stateChanged)
    def the_pieces(self):
        return [i.name() for i in gd.data_model2.alldata()]

    @pyqtProperty(str, notify=stateChanged)
    def csvDir(self):
        return csvsDir().as_uri()

    @pyqtProperty(int, notify=stateChanged)
    def nmbrRowers(self):
        if gd.sessionInfo == {}:
            return 1
        else:
            return gd.sessionInfo['RowerCnt']

    @pyqtProperty(str, notify=stateChanged)
    def sessionDir(self):
        return sessionsDir().as_uri()

    @pyqtProperty(str, notify=stateChanged)
    def sessionName(self):
        return gd.config['Session']

    def cleanup_global_data(self):
        if gd.sessionInfo == {}:
            return

        gd.sessionInfo = {}
        gd.dataObject = []
        gd.data_model.del_all()
        gd.data_model2.del_all()
        gd.data_model3.del_all()
        gd.data_model4.del_all()
        gd.data_model5.del_all()
        gd.boattablemodel.del_all()
        gd.boatPlots.del_all()
        gd.crewPlots.del_all()

    def update_the_models(self, session):
        self._data.load_sessionInfo(gd.sessionInfo['uniqHeader'])
        self.statusText = "Current session:  " + gd.config['SubDir'] + session

        self._traces = gd.dataObject
        self._tempi = gd.sessionInfo['Tempi']
        self.times = list(map( lambda x: x/Hz, list(range(len(self._traces) - 2))))
        self.xFrom = 0
        self.xTo = (len(self.times)/Hz)
        self.traceCentre = self.xTo/2
        
        gd.mainView.set_data_traces()
        self.update_figures()

        # Create Rower tables and plots
        for i in range(gd.sessionInfo['RowerCnt']):
            gd.rowertablemodel[i] = RowerTableModel(i)
            gd.context.setContextProperty("rowerTableModel"+str(i), gd.rowertablemodel[i])
            
    @pyqtSlot(str)
    def createSessionCsv(self, f):
        """Used from the menu when (re)creating a new session."""
        csv_file = re.sub('\Afile://', '', f)

        # Only accept files in csv_data dir
        csvbase =  str(Path.home() / gd.config['BaseDir'] / 'csv_data') + '/'
        csvbase = re.sub('\\\\', '/', csvbase)   # for windows, backslash komt op linux normaal niet voor.
        if csvbase not in csv_file:
            # ignore
            return

        # Update and use SubDir
        tail = re.sub(csvbase, '', csv_file)
        tail = re.sub('^/', '', tail)   # hack voor windows, slash komt normaal op linux  niet voor
        b = os.path.basename(tail)
        subdir = re.sub(b, '', tail)
        if subdir != gd.config['SubDir']:
            gd.config['SubDir'] = subdir
            saveConfig(gd.config)

        # session- and caches- dirs should reflect csv-dir
        b = os.path.basename(csv_file)
        session = re.sub('.csv', '', b)
        session_file = sessionsDir() / (session + '.yaml')
        cache_file = cachesDir() / (session + '.npy')
        
        # create subdirs in session, caches and reports
        if subdir != '':
            try:
                Path.mkdir(sessionsDir())
            except FileExistsError:
                pass
            try:
                Path.mkdir(cachesDir())
            except FileExistsError:
                pass
            try:
                Path.mkdir(reportsDir())
            except FileExistsError:
                pass
            
        # move session in old subdir and remove cache file if they exist
        # TODO: do not remove files in old, only after offering to copy relevant
        #       info to new session file is accepted.
        oldInfo = None
        try:
            fd = Path.open(session_file, 'r')
            inhoud = fd.read()
            oldInfo = yaml.load(inhoud, Loader=yaml.UnsafeLoader)
            # get old sessionInfo
            fd.close()
            try:
                Path.mkdir(sessionsDir() / 'old')
            except FileExistsError:
                pass
            oldfile = sessionsDir() / 'old' / (session + '.yaml')
            # don't save if there already is one
            try:
                fd = Path.open(oldfile, 'r')
                fd.close()
                print(f'createSessionCsv: old file already exists!')
            except:
                move(session_file, oldfile)
        except IOError:
            # assume no session_file
            pass
        try:
            fd = Path.open(cache_file, 'r')
            fd.close()
            os.remove(cache_file)
        except IOError:
            pass

        self.cleanup_global_data()
        gd.config['Session'] = session
        saveConfig(gd.config)

        # create sessionfile
        copyfile(configsDir() / 'session_template.yaml', session_file)
        gd.sessionInfo = selectSession()
        if oldInfo is not None:
            gd.sessionInfo['CrewInfo'] = oldInfo['CrewInfo']
            gd.sessionInfo['Calibration'] = oldInfo['Calibration']
            gd.sessionInfo['Misc'] = oldInfo['Misc']
            gd.sessionInfo['Video'] = oldInfo['Video']

        gd.cal_value = gd.sessionInfo['Calibration']

        # read numpy data
        makecache(cache_file)
        
        calibrate()
        self.update_the_models(session)
        
    @pyqtSlot()
    def selectCurrent(self):
        """Used when starting the program."""
        session = gd.config['Session']
        session_file = sessionsDir() / (session + '.yaml')

         # file should be there!

        if session != 'None':
            self.selectIt(session)

    @pyqtSlot(list, int)
    def rowerprofile(self, s, r):
        gd.rowerPlots[r].figure = s[0]()

    @pyqtSlot(str)
    def selectSessionFile(self, f):
        """Used from the menu to select an existing session."""
        session_file = re.sub('\Afile://', '', f)

        # only accept files in session_data dir
        sessionbase =  str(Path.home() / gd.config['BaseDir'] / 'session_data') + '/'
        sessionbase = re.sub('\\\\', '/', sessionbase)   # for windows, backslash komt op linux normaal niet voor.
        if sessionbase not in session_file:
            # ignore
            return

        # Update and use SubDir
        tail = re.sub(sessionbase, '', session_file)
        tail = re.sub('^/', '', tail)   # hack voor windows, slash komt normaal op linux  niet voor
        b = os.path.basename(tail)
        subdir = re.sub(b, '', tail)
        if subdir != gd.config['SubDir']:
            gd.config['SubDir'] = subdir
            saveConfig(gd.config)
        
        s = os.path.basename(session_file)
        session = re.sub('.yaml', '', s)

        gd.config['Session'] = session
        saveConfig(gd.config)

        self.selectIt(session)

    def selectIt(self, session):
        session_file = sessionsDir() / (session + '.yaml')
        cache_file = cachesDir() / (session + '.npy')

        self.cleanup_global_data()
        # update sessionInfo
        try:
            fd = Path.open(session_file, 'r')
            inhoud = fd.read()
        except IOError:
            print(f'selectIt: cannot read Sessions file, should not happen  {session_file}')
            gd.config['Session'] = 'None'
            saveConfig(gd.config)
            exit()
        gd.sessionInfo = yaml.load(inhoud, Loader=yaml.UnsafeLoader)
        gd.cal_value = gd.sessionInfo['Calibration']

        # list met data voor de session Info tab (placeholdertext)
        sinfo = [
            gd.sessionInfo['CrewInfo'],
            gd.cal_value,
            gd.sessionInfo['Misc'],
            gd.sessionInfo['Rowers'],
            gd.sessionInfo['Video'],
            '...'
            ]
        
        gd.crewPlots.sessionsig.emit(sinfo)

        # update dataObject (should be there)
        try:
            fd = Path.open(cache_file, 'r')
            fd.close()
            gd.dataObject = np.load(cache_file)
        except IOError:
            print(f'Cannot read cachefile, should not happen  {cache_file}')
            print("Repairing cache file,")
            makecache(cache_file)

        calibrate()
        self.update_the_models(session)
        gd.boattablemodel.make_profile()


