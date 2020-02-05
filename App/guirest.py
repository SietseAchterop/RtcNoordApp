"""The Gui related classes for the RTCnoord app."""

import os, sys, re, yaml, time, math
from stat import S_IREAD, S_IRGRP, S_IROTH
from pathlib import Path

import traceback

from shutil import copyfile, move
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d

from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty, QMetaObject, Qt, QTimer, QByteArray, QAbstractListModel, QModelIndex
from PyQt5.QtGui import QColor
from PyQt5.QtQml import QJSValue

import globalData as gd

from utils import *

from models import *

import matplotlib.pyplot as plt


# matplotlib plot in View Piece
class FormView(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, data2=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None

        # in seconds
        self.xFrom = 0
        self.xTo = 1
        # in index
        self.xFrom2 = 0
        self.xTo2 = 1

        # length of segment shown in the plots, initial limited
        self._length = 2000
        self._starttime = 0
        #
        self.syncMode = False
        # synchronisation position for video
        self.videoStart = 0
        self.videoNewStart = 0
        # current position of frame in data
        self.videoPos = 0
        self.pieceWidth = 60
        self.traceCentre = 30
        
        self.scale = 1
        self.panon = False
        self.pandistance = 0
        self.panbase = self.traceCentre

        self.dd = None
        self.ee = None

        # with legends it becomes slow
        self._legend = True

        self._data = data
        self._traces = None

        # the part we show
        self._window_tr = None
        self._window_tr2 = None
        # for second session
        self.stroketime = 100  # needed for when no piece is set
        # second session
        self.secondary = False
        self._data2 = data2
        self._traces2 = None
        self.times = []
        
        self.vid_state = 0

        self.update_figure()

    def onclick_d(self, event):
        try:
            """
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))
            """
            if event.inaxes == self.ax1:
                if event.button == 1:
                    if gd.runningvideo:
                        if self.syncMode:
                            self.videoNewStart = event.xdata
                            print(f'vs {self.videoNewStart}')
                        else:
                            gd.player.seek(event.xdata - self.videoPos)
                            self.videoPos = event.xdata
                            print(f'vp {self.videoPos}')
                        self.update_figure()
                elif event.button == 3:
                    # panning start
                    self.panon = True
                    self.pandistance = event.x
                    self.panbase = self.traceCentre
            else:
                pass
            
        except TypeError:
            # clicked outside the plot, ignore
            pass

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
                self.scale += event.step*0.05  # nog beter maken.
                if self.scale < 0.05:
                    self.scale = 0.05
                self.update_figure()
        except TypeError:
            pass

    def onnotify(self, event):
        try:
            if event.inaxes == self.ax1:
                # button 3, maar gaat altijd goed
                if self.panon:
                    diff = (self.pandistance - event.x)
                    self.traceCentre = self.panbase + diff*0.1
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
        self.ax1 = self.figure.add_subplot(111)    
        self.ax1.set_title('Traces')

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)

        cid1 = fig.canvas.mpl_connect('button_press_event', self.onclick_d)
        cid2 = fig.canvas.mpl_connect('button_release_event', self.onclick_u)
        cid3 = fig.canvas.mpl_connect('scroll_event', self.onscroll)
        cid4 = fig.canvas.mpl_connect('motion_notify_event', self.onnotify)
        
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

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Traces')

        has_series = False

        # always use 120 seconds of data, 30 seconds before the start of the piece and 90 after
        #    this to (almost) always be able to have a secondary session to show
        #  when no piece selected use the first 120 seconds
        #  the secondary session is mapped onto this
        #  evt. mapping aanpassen: strokes voor en achteruit via de gui

        self.dd = self.ax1.scatter([self.xFrom], [0], marker='>', color='green')
        self.ee = self.ax1.scatter([self.xTo], [0], marker='<', color='red')
       
        for row in range(self._data.rowCount()):
            model_index = self._data.index(row, 0)
            checked = self._data.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data.data(model_index, DataSensorsModel.NameRole)                
                i = self._data.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._window_tr[:, i]
                self.ax1.plot(self.times, values, linewidth=0.6,  label=name)

        if gd.runningvideo:
            self.ax1.vlines(self.videoStart, 0, 20, transform=self.ax1.get_xaxis_transform(), colors='r')
            self.ax1.vlines(self.videoPos, 0, 20, transform=self.ax1.get_xaxis_transform(), colors='b')

        # secondary plots
        for row in range(self._data2.rowCount()):
            model_index = self._data2.index(row, 0)
            checked = self._data2.data(model_index, DataSensorsModel.SelectedRole)
            

            if checked:
                has_series = True
                name = self._data2.data(model_index, DataSensorsModel.NameRole)                
                i = self._data2.data(model_index, DataSensorsModel.DataRole) + 1
                values = self._window_tr2[:, i]
                self.ax1.plot(self.times, values, linewidth=0.7,  label=name, linestyle='--')

        self.ax1.plot([self.traceCentre], [0], marker='D', color='b')                
        # what about pieceWidth?
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

    def set_windows(self, piece=False, x=0, y=0):
        """Set windows for primary and secondary datasets.
           Limit view to 120 seconds max"""
        if piece:
            xFrom = x
            self._starttime = int(x/Hz)
            xTo = x + len(self._traces[x: y, 1])
            self._length = xTo - xFrom
            self._window_tr = self._traces[xFrom: xTo, :]
            self.times = list(map( lambda x: x/Hz, list(range(xTo-xFrom))))
            self.xFrom = 0
            self.xTo =  int((self._length)/Hz)
            self.traceCentre = self.xTo/2

            if self.secondary:
                if len(self._window_tr2) > self._length:
                    window2 = np.copy(self._window_tr2[0: self._length, :])
                    self._window_tr2 = window2
                else:
                    a, _ = self._window_tr.shape
                    s, b = self._window_tr2.shape
                    window2 = np.copy(self._window_tr2)
                    window2.resize((a, b))
                    window2[s:, :] = np.nan
                    self._window_tr2 = window2

        else:
            # we limit the initial size of the plot
            self._starttime = 0
            xFrom = 0
            xTo = self._length

            self._window_tr = self._traces[xFrom: xTo, :]
            self.times = list(map( lambda x: x/Hz, list(range(xTo-xFrom))))
            self.xFrom = int(xFrom/Hz)
            self.xTo = int(xTo/Hz)
            self.traceCentre = self.xTo/2
        return xFrom, xTo

    @pyqtSlot(str)
    def set_piece(self, name):
        for i in gd.data_model2.alldata():        
            if i.name() == name:
                xFrom, xTo = i.data()
                # we always begin at a strokes beginning
                tempi = gd.sessionInfo['Tempi']
                # set cycle time for secondary session using 2 strokes
                md = 0
                for t, r in tempi:
                    if md == 0:
                        if t >= xFrom:
                            xFrom = t
                            md = 1
                    elif md == 1:
                        md = 2
                    else:
                        self.stroketime = (t-xFrom)/2
                        break
                self._length = xTo - xFrom
                strt, end = self.set_windows(piece=True, x=xFrom, y=xTo)
        self.update_figure()

    # aangeroepen vanuit FromPieces (dan 2de sessie eruit) en lokaal bij nieuwe secondary
    def set_data_traces(self, local=False):
        self._data.load_sessionInfo(gd.sessionInfo['uniqHeader'])
        self._traces = gd.dataObject
        gd.data_model2.set_all(gd.sessionInfo['Pieces'])

        if not local:
            # always start without a secondary session
            self.secondary = False
            gd.config['Session2'] = ''
            saveConfig(gd.config)
            gd.data_model5.del_all()
            self._starttime = 0
            
        if self.secondary:
            gd.data_model4.del_all()
            gd.data_model4.load_sessionInfo(gd.sessionInfo2['uniqHeader'])
            gd.data_model5.del_all()
            gd.data_model5.set_all(gd.sessionInfo2['Pieces'])

        strt, end = self.set_windows()
        if self.secondary:
            window2 = self._traces2[strt: end, :]
            size = window2.shape[0]
            if size < self._length:
                a, _ = self._window_tr.shape
                _, b = window2.shape
                self._window_tr2 = np.copy(window2)
                self._window_tr2.resize((a, b))
                self._window_tr2[size:, :] = np.nan
            else:
                #
                end = strt + self._length
                self._window_tr2 = np.copy(self._traces2[strt: end, :])
            # normalise to compare better (alleen als we met pieces bezig zijn)
        self.update_figure()


    # Toggle video
    #  steeds mpv starten/stoppen
    @pyqtSlot()
    def videoOpenClose(self):
        if gd.novideo:
            return
        
        if self.vid_state == 0:
            # uit sesionInfo halen
            v = gd.sessionInfo['Video']
            if v[0] == 'None':
                return
            file = videoFile(v[0])
            self.videoStart = float(v[1])
            self.videoPos = float(v[2])
            print(f'started with {v[1]}  {v[2]}')
            startVideo()
            gd.player.window_scale = 0.5
            gd.player.pause= True
            gd.hr_seek = 'yes'
            gd.player.loadfile(file.as_uri())
            time.sleep(0.1)  # waarom nodig, en hoeveel (bij langzame computers)

            gd.player.seek(self.videoStart)
            self.videoStart = self.videoPos  # now videostart marker ok
            self.vid_state = 1
        else:
            stopVideo()
            self.vid_state = 0
            self.videoStart = 0
            self.videoPos = 0
        self.update_figure()

    """
    sync procedure, uitgaand van video op beginpositie, dus meteen na starten video
       dan staat de video op waarde uit sessionInfo['Video'][1]
       zet video op beoogd syncpositie
       tel verplaatsing bij oude waarde op, dat is nu syncpositie in video  (a)

       klik middelste knopje, wordt rood
       klik met muis precies op goede plaats in de data
       nu weten we de plaats in de data (b)

       klik middelste knopje, wordt weer gewoon
       zet a, b in sessionInfo['Video']

    """

    @pyqtSlot(bool)
    def sync_mode(self, on):
        if gd.runningvideo:
            if on:
                # fix startpunt in de video (a)
                self.nieuw_vid = float(gd.sessionInfo['Video'][1]) + self.videoPos - self.videoStart
                print(f'nv {self.nieuw_vid}')
                
                self.syncMode = True
                # linker muisknop verplaatst nu rode lijn
            else:
                # fix data tov video startpunt (b)
                file = gd.sessionInfo['Video'][0]
                gd.sessionInfo['Video'] = [ file,  str(self.nieuw_vid), str(self.videoNewStart) ]
                # gd.sessionInfo['Video'][2] = self.videoNewStart
                print(f'saved as {gd.sessionInfo["Video"]}')
                saveSessionInfo(gd.sessionInfo)
                # zet blauwe lijn op rode
                self.videoPos = self.videoNewStart
                self.syncMode = False
                self.update_figure()
            
    @pyqtSlot()
    def frame_step(self):
        if gd.novideo:
            return
        gd.player.frame_step()
        self.videoPos += 0.02
        self.update_figure()

    @pyqtSlot()
    def frame_back_step(self):
        if gd.novideo:
            return
        gd.player.frame_back_step()
        self.videoPos -= 0.02
        self.update_figure()

    @pyqtSlot(float)
    def frame_seek(self, s):
        if gd.novideo:
            return
        gd.player.seek(s)
        self.videoPos += s
        print(f'frame pos {self.videoPos}')
        self.update_figure()

    # handling of second session

    # een andere sessie kan een aander aantal sensoren hebben, hoe de mappen?

    @pyqtProperty(str, notify=stateChanged)
    def sessionName(self):
        return gd.config['Session2']

    @pyqtSlot(str)
    def selectSecondFile(self, f):
        """ used from the menu to select a secondary session."""
        session_file = re.sub('\Afile://', '', f)

        # only accept files in session_data dir
        sessionbase =  str(Path.home() / gd.config['BaseDir'] / 'session_data') + '/'
        if sessionbase not in session_file:
            # ignore
            return

        s = os.path.basename(session_file)
        session = re.sub('.yaml', '', s)

        gd.config['Session2'] = session
        saveConfig(gd.config)
        
        self.selectSecond(session_file, session)

    def selectSecond(self, session_file, session):
        sesdir = re.sub(session + '.yaml', '', session_file)
        cachesdir = re.sub('session_data', 'caches' , sesdir)
        path = Path.home() / gd.config['BaseDir'] / 'caches'
        cache_file = cachesdir + session + '.npy'
    
        # wat nodig?
        # self.cleanup_global_data()
        gd.data_model3.del_all()
        gd.data_model5.del_all()

        # update sessionInfo2
        session_file = Path(session_file)
        try:
            fd = Path.open(session_file, 'r')
            inhoud = fd.read()
        except IOError:
            print(f'selectSecond: cannot read Sessions file, should not happen  {session_file}')
            gd.config['Session2'] = 'None'
            saveConfig(gd.config)
            exit()
        gd.sessionInfo2 = yaml.load(inhoud, Loader=yaml.UnsafeLoader)
        gd.cal_value2 = gd.sessionInfo2['Calibration']

        # update dataObject (should be there)
        cache_file = Path(cache_file)
        try:
            fd = Path.open(cache_file, 'r')
            fd.close()
            gd.dataObject2 = np.load(cache_file)
        except IOError:
            print(f'Cannot read secondary cachefile, should not happen  {cache_file}')
            gd.config['Session2'] = 'None'
            saveConfig(gd.config)
            exit()
            
        calibrate(True)
        self.update_the_2nd_models(session)

    def update_the_2nd_models(self, session):
        self.statusText = "Secondary session:  " + session

        self._traces2 = gd.dataObject2
        self.secondary = True

        self.set_data_traces(local=True)
        self.update_figure()


        
    @pyqtSlot(str)
    def set_2nd_piece(self, name):
        for i in gd.data_model5.alldata():        
            if i.name() == name:
                xFrom2, xTo2 = i.data()
                # put xFrom2 on first catch, and calculate cycle time using 2 strokes
                tempi2 = gd.sessionInfo2['Tempi']
                md = 0
                for t, r in tempi2:
                    if md == 0:
                        if t >= xFrom2:
                            xFrom2 = t
                            md = 1
                    elif md == 1:
                        md = 2
                    else:
                        stroketime_2nd = (t-xFrom2)/2
                        break
                self.xFrom2, self.xTo2 = xFrom2/Hz, xTo2/Hz

                # normalize to the current main piece
                nmbr_sensors2 = self._traces2.shape[1]                
                self._window_tr2 = np.zeros((self._length, nmbr_sensors2))

                stretch = stroketime_2nd/self.stroketime

                # for each sensor
                l = int(self._length * stretch)
                x = np.arange(l)
                factor = ((l-1)/(self._length-1))
                for i in range(nmbr_sensors2):
                    # interp1d is allergic to nans!
                    k = 0
                    for g in range(len(self._traces2[xFrom2: xFrom2+l, i])):
                        if math.isnan(self._traces2[xFrom2+g, i]):
                            self._traces2[xFrom2+g, i] = 0
                    g = interp1d(x, np.copy(self._traces2[xFrom2:xFrom2+l, i]), kind='cubic', fill_value='extrapolate')
                    xnew = np.arange(self._length)*factor
                    self._window_tr2[:, i] = g(xnew)

                self.update_figure()

    @pyqtProperty(list, notify=stateChanged)
    def the_2nd_pieces(self):
        return [i.name() for i in gd.data_model5.alldata()]


# matplotlib plot in BoatProfile
class BoatForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None

        self.een = None
        self.twee = None
        self.drie = None
        
        self._legend = True

        self._data = data
        # pieces to show
        self.show = 0

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        gs = self._figure.add_gridspec(2, 2)
        self.ax1 = self._figure.add_subplot(gs[0, 0])
        self.ax2 = self._figure.add_subplot(gs[0, 1])
        self.ax3 = self._figure.add_subplot(gs[1, 0])
        self.ax4 = self._figure.add_subplot(gs[1, 1])

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)
        
        self.update_figure()
        
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

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Snelheid')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Versnelling')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Pitch')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Versnelling-Tempo per Piece')

        # do the plotting
        # bootsnelheid, accel, pitch
        if gd.profile_available:
            sensors = gd.sessionInfo['Header']
            if self.show == 0:
                for i in range(len(prof_pcs)):
                    self.ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.6, label=prof_pcs[i])
                    self.ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label=prof_pcs[i])
                    self.ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.6, label=prof_pcs[i])
            else:
                i = self.show - 1
                self.ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.6, label=prof_pcs[i])
                self.ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label=prof_pcs[i])
                self.ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.6, label=prof_pcs[i])
                    


            pa = []
            for i in range(len(prof_pcs)):
                # versnelling en tempo per piece
                #  bij de oude software was dit versnelling tegen tempo
                d, a = gd.out[i]
                pa.append((d['Speed'], gd.sessionInfo['PieceCntRating'][i][1]))
            pa = list(zip(*pa))
            p = [ 10*x for x in pa[0]]  # ad hoc schaling, snelheid decimeters/seconde
            self.ax4.scatter(list(range(6)), p, marker='H', color='green')
            self.ax4.scatter(list(range(6)), pa[1], marker='H', color='blue')

        if self.legend:
            self.ax1.legend()

        self.stateChanged.emit()

    def del_all(self):
        if gd.profile_available:
            gd.profile_available = False
        self.update_figure()
        """ deze kennelijk niet nodig
        self.twee.remove()
        self.drie.remove()
        """

    @pyqtSlot(int)
    def showPiece(self, s):
        self.show = s
        self.update_figure()


# matplotlib plot in Crew Profile
# voorlopig kiezen we een piece en laten de data voor iedere roeiers zien
# uiteindelijk het te gebruiken piece via de gui aangeven
#
#  here the properties of the sessionInfo tab
class CrewForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None

        self.een = None
        self.twee = None
        self.drie = None
        
        self._legend = True

        self._data = data

        self.show = 0

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        gs = self._figure.add_gridspec(2, 2)
        self.ax1 = self._figure.add_subplot(gs[0, 0])
        self.ax2 = self._figure.add_subplot(gs[0, 1])
        self.ax3 = self._figure.add_subplot(gs[1, 0])
        self.ax4 = self._figure.add_subplot(gs[1, 1])

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)
        
        self.update_figure()
        
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

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('Gate Angle')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Gate Force')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Stretcher Force')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Power')

        # do the plotting of all rowers for the selected piece
        # bootsnelheid, accel, pitch
        if gd.profile_available:

            rcnt = gd.sessionInfo['RowerCnt']
            for r in range(rcnt):
                sns = rowersensors(r)
                # print(sns)
                # print(f'Maak crewplot voor {r}')
                if gd.sessionInfo['BoatType'] == 'sweep':
                    i = sns['GateAngle']
                    j = sns['GateForceX']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']
                # stretchers is er niet altijd!
                # k = sns['Stretcher Z']
                # nog schakelaar voor maken om stretche en seatposition wel/niet mee te laten doen
                #  niet als ze er niet zijn
                #  optioneel als ze er (gedeeltelijk zijn)
                    
                self.een  = self.ax1.plot(gd.norm_arrays[self.show, :, i], linewidth=0.6, label=f'R {r+1}')
                self.twee = self.ax2.plot(gd.norm_arrays[self.show, :, j], linewidth=0.6, label=f'R {r+1}')
                # self.drie = self.ax3.plot(gd.norm_arrays[self.show, :, k], linewidth=0.6, label=prof_pcs[r])

        if self.legend:
            self.ax1.legend()

        self.stateChanged.emit()

    def del_all(self):
        if gd.profile_available:
            for l in self.een:
                l.remove()
            gd.profile_available = False
        self.update_figure()

    @pyqtSlot(int)
    def showPiece(self, s):
        self.show = s
        self.update_figure()

    # session Info tab
    sessionsig = pyqtSignal(list, arguments =['sessig'])

    @pyqtSlot('QVariant')
    def newsesinfo(self, sinfo):
        s = sinfo.toVariant()
        gd.sessionInfo['CrewInfo'] = s[0]
        gd.sessionInfo['Calibration'] = int(s[1])
        gd.sessionInfo['Misc'] = s[2]
        saveSessionInfo(gd.sessionInfo)


# matplotlib plot in Rower Profile
class RowerForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, rower, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None

        self.een = None
        self.twee = None
        self.drie = None
        
        self._legend = True

        self._data = data
        self.rower = rower

        self.show = 0
        
    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        gs = self._figure.add_gridspec(2, 2)
        self.ax1 = self._figure.add_subplot(gs[0, 0])
        self.ax2 = self._figure.add_subplot(gs[0, 1])
        self.ax3 = self._figure.add_subplot(gs[1, 0])
        self.ax4 = self._figure.add_subplot(gs[1, 1])

        # Signal connection
        self.stateChanged.connect(self._figure.canvas.draw_idle)
        self.legendChanged.connect(self._figure.canvas.draw_idle)
        
        self.update_figure()
        
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

    @pyqtSlot()
    def update_figure(self):
        if self.figure is None:
            return
    
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('GateForce/GateAngle')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Versnelling')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Pitch')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Power')

        # do the plotting
        # bootsnelheid, accel, pitch
        if gd.profile_available:
            sensors = gd.sessionInfo['Header']
            rsens = rowersensors(self.rower)
            # ad hoc angle x 10. Beter via (max-min). Schaal is goed, nl force
            if gd.sessionInfo['BoatType'] == 'sweep':
                # print(f'Maak rowerplot voor {self.rower}')
                self.een = self.ax1.plot(gd.norm_arrays[self.show, :, rsens['GateAngle']]*10, linewidth=0.6, label='GateAngle')
                self.twee = self.ax1.plot(gd.norm_arrays[self.show, :, rsens['GateForceX']], linewidth=0.6, label='GateForceX')
            else:
                self.een = self.ax1.plot(gd.norm_arrays[self.show, :, rsens['P GateAngle']]*10, linewidth=0.6, label='GateAngle')
                self.twee = self.ax1.plot(gd.norm_arrays[self.show, :, rsens['P GateForceX']], linewidth=0.6, label='GateForceX')
            # waarom werkt de legend hier niet?
            self.drie = self.ax2.plot(gd.norm_arrays[self.show, :, sensors.index('Accel')], linewidth=0.6, label='Accel')
            self.vier = self.ax3.plot(gd.norm_arrays[self.show, :, sensors.index('Pitch Angle')], linewidth=0.6, label='Pitch')
            d, a = gd.out[self.show]
            self.vijf = self.ax4.plot( a[0+self.rower], linewidth=0.6, label='Power')

        if self.legend:
            self.ax1.legend()

        self.stateChanged.emit()

    def del_all(self):
        if gd.profile_available:
            for l in self.een:
                l.remove()
            gd.profile_available = False
            print(f'gd.profile_available False')
        self.update_figure()

    @pyqtSlot(int)
    def showPiece(self, s):
        self.show = s
        self.update_figure()

