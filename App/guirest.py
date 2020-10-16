"""The rest of the gui related classes for the RTCnoord app."""

import sys, re, yaml, time, math
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
        # secondary
        self.xFrom2 = 0
        self.xTo2 = 1

        # length of segment shown in the plots, initial limited
        self._length = 2000
        self._starttime = 0
        #
        self.inSync = False
        # synchronisation position for video
        self.videoPos = 0
        self.videoNewStart = 0
        # current position of frame in data
        self.dataPos = 0
        self.traceCentre = 30
        
        self.scaleX = 1
        self.panon = False
        self.pandistance = 0
        self.panbase = self.traceCentre

        # scaling of the plots
        self.scaling = False
        # with legends it becomes slow
        self._legend = True

        self._data = data
        self._traces = None

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
                        if self.inSync:
                            self.videoNewStart = event.xdata
                            print(f'vs {self.videoNewStart}')
                        else:
                            gd.player.seek(event.xdata - self.dataPos)
                            self.dataPos = event.xdata
                            print(f'vp {self.dataPos}')
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
                # button 3
                self.panon = False
        except TypeError:
            pass

    def onscroll(self, event):
        try:
            if event.inaxes == self.ax1:
                self.scaleX += event.step*0.05  # improve upon this
                if self.scaleX < 0.05:
                    self.scaleX = 0.05
                self.update_figure()
        except TypeError:
            pass

    def onnotify(self, event):
        try:
            if event.inaxes == self.ax1:
                # button 3
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

        #  when no piece selected use the first 40 seconds

        #  self.scaling
        factors = gd.sessionInfo['ScalingFactors']

        self.ax1.scatter([self.xFrom], [0], marker='>', color='green')
        self.ax1.scatter([self.xTo], [0], marker='<', color='red')
       
        senslist = []
        for row in range(self._data.rowCount()):
            model_index = self._data.index(row, 0)
            checked = self._data.data(model_index, DataSensorsModel.SelectedRole)
            
            if checked:
                has_series = True
                name = self._data.data(model_index, DataSensorsModel.NameRole)                
                i = self._data.data(model_index, DataSensorsModel.DataRole) + 1
                if self.scaling:
                    scaleY = factors[i]
                else:
                    scaleY = 1
                values = gd.view_tr[:, i] * scaleY
                self.ax1.plot(self.times, values, linewidth=0.6,  label=name)
                senslist.append((i, name, scaleY))

        if gd.runningvideo:
            self.ax1.vlines(self.videoPos, 0, 20, transform=self.ax1.get_xaxis_transform(), colors='r')
            self.ax1.vlines(self.dataPos, 0, 20, transform=self.ax1.get_xaxis_transform(), colors='b')

        # secondary plots
        secsenslist = []
        if self.secondary:
            factors = gd.sessionInfo2['ScalingFactors']
            for row in range(self._data2.rowCount()):
                model_index = self._data2.index(row, 0)
                checked = self._data2.data(model_index, DataSensorsModel.SelectedRole)

                if checked:
                    has_series = True
                    name = self._data2.data(model_index, DataSensorsModel.NameRole)                
                    i = self._data2.data(model_index, DataSensorsModel.DataRole) + 1
                    if self.scaling:
                        scaleY = factors[i]
                    else:
                        scaleY = 1
                    values = gd.view_tr2[:, i] * scaleY
                    self.ax1.plot(self.times, values, linewidth=0.7,  label=name, linestyle='--')
                    secsenslist.append((i, name, scaleY))

        self.ax1.plot([self.traceCentre], [0], marker='D', color='b')                

        dist = (self.xTo - self.xFrom)
        xFrom = self.traceCentre - self.scaleX*dist/2
        xTo = self.traceCentre + self.scaleX*dist/2
        
        self.ax1.set_xlim(xFrom, xTo)
        # start at correct beginvalue
        locs = self.ax1.get_xticks()
        ticks = [item+self._starttime for item in locs]
        self.ax1.set_xticklabels(ticks)

        if has_series and self.legend:
            self.ax1.legend()

        # set values for custom plot in report
        if senslist != [] or secsenslist != []:
            gd.extraplot = True
            gd.extrasettings = [self.xFrom, self.xTo, self._starttime, self.traceCentre, self.scaleX, senslist, secsenslist]
        else:
            gd.extraplot = False
            
        self.stateChanged.emit()

    def set_windows(self, setpiece=False, x=0, y=0):
        """Set windows for primary and secondary datasets.
           Limit view to 120 seconds max"""
        if setpiece:
            xFrom = x
            self._starttime = int(x/Hz)
            xTo = x + len(self._traces[x: y, 1])
            self._length = xTo - xFrom
            gd.view_tr = self._traces[xFrom: xTo, :]
            self.times = list(map( lambda x: x/Hz, list(range(xTo-xFrom))))
            self.xFrom = 0
            self.xTo =  int((self._length)/Hz)
            self.traceCentre = self.xTo/2

            if self.secondary:
                if len(gd.view_tr2) > self._length:
                    window2 = np.copy(gd.view_tr2[0: self._length, :])
                    gd.view_tr2 = window2
                else:
                    a, _ = gd.view_tr.shape
                    s, b = gd.view_tr2.shape
                    window2 = np.copy(gd.view_tr2)
                    window2.resize((a, b))
                    window2[s:, :] = np.nan
                    gd.view_tr2 = window2

        else:
            # we limit the initial size of the plot
            self._starttime = 0
            xFrom = 0
            xTo = self._length

            gd.view_tr = self._traces[xFrom: xTo, :]
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
                strt, end = self.set_windows(setpiece=True, x=xFrom, y=xTo)
        self.update_figure()

    # called from FromPieces (then no 2nd session) and locally with new secondary
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
                a, _ = gd.view_tr.shape
                _, b = window2.shape
                gd.view_tr2 = np.copy(window2)
                gd.view_tr2.resize((a, b))
                gd.view_tr2[size:, :] = np.nan
            else:
                #
                end = strt + self._length
                gd.view_tr2 = np.copy(self._traces2[strt: end, :])
            # normalise to compare better (only when doing pieces)
        self.update_figure()


    # Toggle video
    #  start/stop mpv
    @pyqtSlot()
    def videoOpenClose(self):
        if gd.novideo:
            return
        
        if self.vid_state == 0:
            v = gd.sessionInfo['Video']
            if v[0] == 'None':
                return
            file = videoFile(v[0])
            if not file.is_file():
                print(f'{file} does not exist, ignored')
                return
            self.videoPos = float(v[1])
            self.dataPos = float(v[2])
            print(f'started with {v[1]}  {v[2]}')
            startVideo()
            gd.player.window_scale = 0.5
            gd.player.pause= True
            gd.hr_seek = 'yes'
            gd.player.loadfile(file.as_uri())
            time.sleep(0.1)  # why needed?

            gd.player.seek(self.videoPos)
            self.videoPos = self.dataPos  # now videostart marker ok
            self.vid_state = 1
        else:
            stopVideo()
            self.vid_state = 0
            self.videoPos = 0
            self.dataPos = 0
        self.update_figure()

    """
    sync video to data:
      - Click the video button
      - If the video file exists is is shown, otherwise the command is ignored
      - 
       , starting from video at starting position, directly after starting video
       then sessionInfo['Video'][1] shows position

       Set video on intended syncposiion using the qui.
       Add displacement to old value (a).

       Click middle button, with will turn red
       Click exactly on intended position.
       We now know the position in the data (b)

       Click middle button, will return to normal
       Put a and b in sessionInfo['Video']

    """

    @pyqtSlot(bool)
    def sync_mode(self, on):
        if gd.runningvideo:
            if on:
                # fix start in video (a)
                self.nieuw_vid = float(gd.sessionInfo['Video'][1]) + self.dataPos - self.videoPos
                print(f'nv {self.nieuw_vid}')
                
                self.inSync = True
                # left button places red line
            else:
                # fix data wrt video start (b)
                file = gd.sessionInfo['Video'][0]
                gd.sessionInfo['Video'] = [ file,  str(self.nieuw_vid), str(self.videoNewStart) ]
                # gd.sessionInfo['Video'][2] = self.videoNewStart
                print(f'saved as {gd.sessionInfo["Video"]}')
                saveSessionInfo(gd.sessionInfo)
                # put blue line on red one.
                self.dataPos = self.videoNewStart
                self.inSync = False
                self.update_figure()
            
    @pyqtSlot()
    def frame_step(self):
        if gd.novideo:
            return
        gd.player.frame_step()
        self.dataPos += 0.02
        self.update_figure()

    @pyqtSlot()
    def frame_back_step(self):
        if gd.novideo:
            return
        gd.player.frame_back_step()
        self.dataPos -= 0.02
        self.update_figure()

    @pyqtSlot(float)
    def frame_seek(self, s):
        if gd.novideo:
            return
        gd.player.seek(s)
        self.dataPos += s
        print(f'frame pos {self.dataPos}')
        self.update_figure()

    # handling of second session

    # what is that session has a different number of sensors, mapping?

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
    
        # what to cleanup exactly?
        # self.cleanup_global_data()
        gd.data_model3.del_all()
        gd.data_model5.del_all()

        # update sessionInfo2
        if gd.os == 'win32':
            session_file = re.sub('^/', '', session_file)   # hack for windows
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

        # update dataObject2 (should be there)
        if gd.os == 'win32':
            cache_file = re.sub('^/', '', cache_file)   # hack for windows
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

                # normalize wrt current main piece
                nmbr_sensors2 = self._traces2.shape[1]                
                gd.view_tr2 = np.zeros((self._length, nmbr_sensors2))

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
                    gd.view_tr2[:, i] = g(xnew)

                self.update_figure()

    @pyqtProperty(list, notify=stateChanged)
    def the_2nd_pieces(self):
        return [i.name() for i in gd.data_model5.alldata()]

    # scaling
    @pyqtSlot(bool)
    def set_scaling(self, checked):
        self.scaling = not checked
        self.update_figure()

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


    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.3)
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
        self.ax1.set_title('Speed')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Acceleration')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Pitch')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Acceleration-Tempo per Piece')

        # do the plotting
        # bootsnelheid, accel, pitch
        if gd.profile_available:
            sensors = gd.sessionInfo['Header']
            pieces = gd.sessionInfo['Pieces']
            cntrating = [cr for nm, x, cr, tl  in pieces]

            if gd.boatPiece == 0:
                for i in range(len(gd.p_names)):
                    self.ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.6, label=gd.p_names[i])
                    self.ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label=gd.p_names[i])
                    self.ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.6, label=gd.p_names[i])
                i = 0
            elif gd.boatPiece == len(gd.p_names) + 1:
                i = 0
                speed = np.zeros((100,))
                accel = np.zeros((100,))
                pitch = np.zeros((100,))
                for i in range(len(gd.p_names)):
                    speed += gd.norm_arrays[i, :, sensors.index('Speed')]
                    accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                    pitch += gd.norm_arrays[i, :, sensors.index('Pitch Angle')]
                self.ax1.plot(speed/6, linewidth=0.6, label=gd.p_names[i])
                self.ax2.plot(accel/6, linewidth=0.6, label=gd.p_names[i])
                self.ax3.plot(pitch/6, linewidth=0.6, label=gd.p_names[i])
            else:
                i = gd.boatPiece - 1
                self.ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.6, label=gd.p_names[i])
                self.ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label=gd.p_names[i])
                self.ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.6, label=gd.p_names[i])


            # gate angle of the stroke (optional?)
            if False:
                #  we use start piece when showing all
                rsens = rowersensors(int(gd.sessionInfo['RowerCnt']) - 1)
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    ind_ga = rsens['GateAngle']
                    self.ax1.plot((gd.norm_arrays[i, :, ind_ga])/17+4, linewidth=0.6, label='Angle')
                else:
                    ind_ga = rsens['P GateAngle']
                    self.ax1.plot((gd.norm_arrays[i, :, ind_ga])/17+4, linewidth=0.6, label='Angle')
            
            pa = []
            for i in range(len(gd.p_names)):
                # accel and tempo per piece
                d, aa = gd.out[i]
                pa.append((d['Speed'], cntrating[i][1]))
            pa = list(zip(*pa))
            p = [ 10*x for x in pa[0]]  # ad hoc scaling, speed in decimeters/second
            self.ax4.scatter(list(range(len(gd.p_names))), p, marker='H', color='green', label='Accel')  # Todo: labels zichtbaar maken
            self.ax4.scatter(list(range(len(gd.p_names))), pa[1], marker='H', color='blue', label='Tempo')

        if self.legend:
            self.ax1.legend(loc='lower right')

        self.stateChanged.emit()

    def del_all(self):
        if gd.profile_available:
            gd.profile_available = False
        self.update_figure()
        """ not needed
        self.twee.remove()
        self.drie.remove()
        """

    @pyqtSlot(int)
    def showPiece(self, s):
        gd.boatPiece = s
        self.update_figure()

    @pyqtProperty(list, notify=stateChanged)
    def allPieces(self):
        if gd.p_names == []:
            return ['no pieces']
        else:
            return ['all'] + gd.p_names + ['average']

# matplotlib plot in Crew Profile
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

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.4)
        gs = self._figure.add_gridspec(3, 2)
        self.ax1 = self._figure.add_subplot(gs[0, 0])
        self.ax2 = self._figure.add_subplot(gs[0, 1])
        self.ax3 = self._figure.add_subplot(gs[1, 0])
        self.ax4 = self._figure.add_subplot(gs[1, 1])
        self.ax5 = self._figure.add_subplot(gs[2, 0])
        self.ax6 = self._figure.add_subplot(gs[2, 1])

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
        self.ax2.set_title('Gate ForceX')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('StretcherForceX')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Power')
        self.ax5.clear()
        self.ax5.grid(True)
        self.ax5.set_title('Power Leg')
        self.ax6.clear()
        self.ax6.grid(True)
        self.ax6.set_title('Power Arm/Trunk')

        # do plotting of all rowers for the selected piece
        # speed, accel, pitch
        if gd.profile_available:
            rcnt = gd.sessionInfo['RowerCnt']
            if gd.crewPiece < len(gd.p_names):
                # a seperate piece, from the tumbler
                d, aa = gd.out[gd.crewPiece]
                for r in range(rcnt):
                    sns = rowersensors(r)
                    # print(f'Create crewplot for {r}')
                    if gd.sessionInfo['ScullSweep'] == 'sweep':
                        i = sns['GateAngle']
                        j = sns['GateForceX']
                    else:
                        i = sns['P GateAngle']
                        j = sns['P GateForceX']
                    # stretchers not always present!
                    # k = sns['Stretcher Z']
                    # todo: create switch to control working in this case

                    self.een = self.ax1.plot(gd.norm_arrays[gd.crewPiece, :, i], linewidth=0.6, label=f'R {r+1}')
                    self.twee = self.ax2.plot(gd.norm_arrays[gd.crewPiece, :, j], linewidth=0.6, label=f'R {r+1}')
                    # self.drie = self.ax3.plot(gd.norm_arrays[gd.crewPiece, :, k], linewidth=0.6, label=gd.p_names[r])
                    self.vier = self.ax4.plot(aa[0+r], linewidth=0.6, label='Power')

                    self.ax1.plot([gd.gmin[gd.crewPiece]], [0], marker='v', color='b')
                    self.ax1.plot([gd.gmax[gd.crewPiece]], [0], marker='^', color='b')
                    self.ax2.plot([gd.gmin[gd.crewPiece]], [0], marker='v', color='b')
                    self.ax2.plot([gd.gmax[gd.crewPiece]], [0], marker='^', color='b')
                    self.ax4.plot([gd.gmin[gd.crewPiece]], [0], marker='v', color='b')
                    self.ax4.plot([gd.gmax[gd.crewPiece]], [0], marker='^', color='b')
            else:
                # last item which is averageing all the pieces
                for r in range(rcnt):
                    sns = rowersensors(r)
                    # print(f'Create crewplot for {r}')
                    if gd.sessionInfo['ScullSweep'] == 'sweep':
                        i = sns['GateAngle']
                        j = sns['GateForceX']
                    else:
                        i = sns['P GateAngle']
                        j = sns['P GateForceX']
                    # stretchers not always present!
                    # k = sns['Stretcher Z']
                    # todo: create switch to control working in this case
                    
                    # average
                    nmbrpieces = len(gd.p_names)
                    angle = np.zeros((100,))
                    force = np.zeros((100,))
                    power = np.zeros((100,))
                    for p in range(nmbrpieces):
                        angle  += gd.norm_arrays[p, :, i]
                        force  += gd.norm_arrays[p, :, j]
                        # stretcherZ = gd.norm_arrays[p, :, k]
                        d, a = gd.out[p]
                        power  += a[0+r]

                    # plot
                    self.ax1.plot(angle/nmbrpieces, linewidth=0.6, label=f'R {r+1}')
                    self.ax2.plot(force/nmbrpieces, linewidth=0.6, label=f'R {r+1}')
                    # self.ax3.plot(stetcherZ/nmbrpieces:, k], linewidth=0.6, label=gd.p_names[r])
                    self.ax4.plot(power/nmbrpieces, linewidth=0.6, label='Power')

                    # no usefull markers here
                    
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
        gd.crewPiece = s
        self.update_figure()

    @pyqtProperty(list, notify=stateChanged)
    def allPieces(self):
        if gd.p_names == []:
            return ['no pieces']
        else:
            return gd.p_names + ['average']

    # session Info tab
    sessionsig = pyqtSignal(list, arguments =['sessig'])

    @pyqtSlot('QVariant')
    def newsesinfo(self, sinfo):
        s = sinfo.toVariant()
        gd.sessionInfo['CrewInfo'] = s[0]
        gd.sessionInfo['Calibration'] = float(s[1])
        gd.sessionInfo['Misc'] = s[2]
        gd.sessionInfo['Rowers'] = s[3]
        print(f" sess  {gd.sessionInfo['Video']}   {s[4]}")
        gd.sessionInfo['Video'] = s[4]
        gd.sessionInfo['PowerLine'] = s[5]
        gd.sessionInfo['Venue'] = s[6]
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

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.3)
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
        self.ax1.set_title('GateForceX/GateAngle')
        self.ax2.clear()
        self.ax2.grid(True)
        self.ax2.set_title('Acceleration')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('GateAngle - GateForceX (X/Y)')
        self.ax4.clear()
        self.ax4.grid(True)
        self.ax4.set_title('Power')

        # do the plotting
        # speed, accel, pitch
        scaleAngle = 10
        if gd.profile_available:
            pieces = gd.sessionInfo['Pieces']
            sensors = gd.sessionInfo['Header']
            rsens = rowersensors(self.rower)
            if gd.rowerPiece[self.rower] == 0:
                # all
                for i in range(len(gd.p_names)):
                    if gd.sessionInfo['ScullSweep'] == 'sweep':
                        # print(f'Create rowerplot for {self.rower}')
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['GateAngle']]*scaleAngle, linewidth=0.6, label='GateAngle')
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.6, label='GateForceX')
                        self.ax3.plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                      gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.6)
                    else:
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['P GateAngle']]*scaleAngle, linewidth=0.6, label='GateAngle')
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.6, label='GateForceX')
                        self.ax3.plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                      gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.6)
                    d, aa = gd.out[i]
                    self.vijf = self.ax4.plot(aa[0+self.rower], linewidth=0.6, label='Power')
                self.ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label='Accel')
            elif gd.rowerPiece[self.rower] == len(gd.p_names) + 1:
                # average
                angle = np.zeros((100,))
                forceX = np.zeros((100,))
                accel = np.zeros((100,))
                power = np.zeros((100,))
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    for i in range(len(gd.p_names)):
                        angle += gd.norm_arrays[i, :, rsens['GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['GateForceX']]
                        accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                        d, aa = gd.out[i]
                        power += aa[0+self.rower]
                    self.ax1.plot(scaleAngle*angle/6, linewidth=0.6, label='GateAngle')
                    self.ax1.plot(forceX/6, linewidth=0.6, label='GateForceX')
                    self.ax2.plot(accel/6, linewidth=0.6, label='Accel')
                    self.ax3.plot(angle/6, forceX/6, linewidth=0.6)
                    self.ax4.plot(power/6, linewidth=0.6, label='Power')
                else:
                    for i in range(len(gd.p_names)):
                        angle += gd.norm_arrays[i, :, rsens['P GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['P GateForceX']]
                        accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                        d, aa = gd.out[i]
                        power += aa[0+self.rower]
                    self.ax1.plot(scaleAngle*angle/6, linewidth=0.6, label='P GateAngle')
                    self.ax1.plot(forceX/6, linewidth=0.6, label='P GateForceX')
                    self.ax2.plot(accel/6, linewidth=0.6, label='Accel')
                    self.ax3.plot(angle/6, forceX/6, linewidth=0.6)
                    self.ax4.plot(power/6, linewidth=0.6, label='Power')

            else:
                i = gd.rowerPiece[self.rower] - 1

                # ad hoc angle x 10. Bettet via (max-min). Scale is for force
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    # print(f'Create rowerplot for {self.rower}')
                    self.ax1.plot(gd.norm_arrays[i, :, rsens['GateAngle']]*scaleAngle, linewidth=0.6, label='GateAngle')
                    self.ax1.plot(gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.6, label='GateForceX')
                    self.ax3.plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                  gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.6)
                else:
                    self.ax1.plot(gd.norm_arrays[i, :, rsens['P GateAngle']]*scaleAngle, linewidth=0.6, label='GateAngle')
                    self.ax1.plot(gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.6, label='GateForceX')
                    self.ax3.plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                  gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.6)
                self.ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label='Accel')

                d, aa = gd.out[i]
                self.vijf = self.ax4.plot(aa[0+self.rower], linewidth=0.6, label='Power')

                self.ax1.plot([gd.gmin[i]], [0], marker='v', color='b')
                self.ax1.plot([gd.gmax[i]], [0], marker='^', color='b')
                self.ax2.plot([gd.gmin[i]], [0], marker='v', color='b')
                self.ax2.plot([gd.gmax[i]], [0], marker='^', color='b')
                self.ax4.plot([gd.gmin[i]], [0], marker='v', color='b')
                self.ax4.plot([gd.gmax[i]], [0], marker='^', color='b')



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
        gd.rowerPiece[self.rower] = s
        self.update_figure()
        gd.stretcherPlots[self.rower].update_figure()

# matplotlib plot in Rower Profile
class StretcherForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()

    def __init__(self, rower, parent=None, data=None, traces=None):
        QObject.__init__(self, parent)

        self._status_text = ""
        self._figure = None
        self.ax1 = None
        
        self._legend = True

        self._data = data
        self.rower = rower

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        self.ax1 = self.figure.add_subplot(111)    

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
        self.ax1.set_title('Stretcher')

        if gd.profile_available:
            pieces = gd.sessionInfo['Pieces']
            sensors = gd.sessionInfo['Header']
            rsens = rowersensors(self.rower)
            if 'StretcherForceX' not in sensors:
                self.ax1.set_title('No Stretcher sensor')
                return

            # use dataObject directly, because of NaN's; we can't use interp1d.
            # todo: show data of all strokes to see variation
            
            if gd.rowerPiece[self.rower] == 0:
                # all DOEN WE NIET
                pass
            elif gd.rowerPiece[self.rower] == len(gd.p_names) + 1:
                # average DOEN WE NIET
                pass
            else: 
                # a piece (alleen dit)
                i = gd.rowerPiece[self.rower] - 1
                name, se, nr, sp = pieces[i]
                self.ax1.plot(gd.dataObject[sp[0]:sp[1], rsens['StretcherForceX']], linewidth=0.6, label='StretcherForceX')
                self.ax1.plot(10*gd.dataObject[sp[0]:sp[1], rsens['Stretcher RL']], linewidth=0.6, label='Stretcher RL')
                self.ax1.plot(10*gd.dataObject[sp[0]:sp[1], rsens['Stretcher TB']], linewidth=0.6, label='Stretcher TB')

                # we gebruiken norm_arrays niet
                f = (sp[1]-sp[0])/100
                self.ax1.plot([gd.gmin[i]*f], [0], marker='v', color='b')
                self.ax1.plot([gd.gmax[i]*f], [0], marker='^', color='b')

        if self.legend:
            self.ax1.legend()

        self.stateChanged.emit()
