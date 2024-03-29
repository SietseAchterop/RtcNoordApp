"""The rest of the gui related classes for the RTCnoord app."""

import sys, os, re, yaml, time, math
from stat import S_IREAD, S_IRGRP, S_IROTH
from pathlib import Path

import traceback

from shutil import copyfile, move
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d, make_interp_spline

from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty
from PyQt5.QtGui import QColor


import globalData as gd

from utils import *

from models import *

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import mplcursors

# matplotlib plot in View Piece
class FormView(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()
    shiftChanged = pyqtSignal(int)

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
        self._shiftX2 = 0

        # length of segment shown in the plots, initial limited
        self._length = 2000
        self._starttime = 0

        # Video stuff
        self.inSync = False
        # start position in video (0.02 is the first frame)
        self.videoStart = 0.02
        # start position in data  (red line)
        self.dataStart = 0
        # current position of frame in data (blue line)
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
        self.fontP = FontProperties()

        self._data = data
        self._traces = None

        # for second session
        self.stroketime = 100  # also needed for when no piece is set
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
                    """ find tempo at this point
                    st = (self._starttime + event.xdata) * Hz
                    tempo = 0
                    for s, t in gd.sessionInfo['Tempi']:
                        if s < st:
                            start = s
                            tempo = t
                            continue
                        break
                    print(f'tempo {tempo:.1f} at cursor')
                    """

                    if gd.runningvideo:
                        if self.inSync:
                            self.dataStart = event.xdata
                            print(f'vs {self.dataStart}')
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
                self.scaleX += event.step*0.0001  # improve upon this
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
                    self.traceCentre = self.panbase + diff*0.01
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
                lines1 = self.ax1.plot(self.times, values, linewidth=0.6,  label=name)
                cursor = mplcursors.cursor(lines1)
                #cursor.connect(
                #    "add", lambda sel: sel.annotation.set_text("labels[sel.target.index]"))

                senslist.append((i, name, scaleY))

        if gd.runningvideo:
            self.ax1.vlines(self.dataStart, 0, 20, transform=self.ax1.get_xaxis_transform(), colors='r')
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
                    lines2 = self.ax1.plot(self.times, values, linewidth=0.7,  label=name, linestyle=stippel)
                    secsenslist.append((i, name, scaleY))
                    mplcursors.cursor(lines2)

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
            self.ax1.legend(loc='upper right', prop=self.fontP)

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
        gd.selPiece = name
        for i in gd.data_model2.alldata():        
            if i.name() == name:
                xFrom, xTo = i.data()
                # we always begin with oars perpendicular to the boat.
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
            vfile = gd.metaData['Video']
            v = gd.sessionInfo['Video']
            if vfile == 'None':
                return
            file = videoFile(vfile)
            if not file.is_file():
                print(f'{file} does not exist, ignored')
                return
            self.videoStart = float(v[1])
            self.dataStart = float(v[2])
            print(f'started with {v[1]}  {v[2]}')
            startVideo()
            gd.player.hr_seek = 'yes'
            gd.player.loadfile(file.as_uri())
            time.sleep(0.1)  # why needed?

            gd.player.seek(self.videoStart)
            self.dataPos = self.dataStart  # now videostart marker ok
            self.vid_state = 1
        else:
            stopVideo()
            self.vid_state = 0
            self.videoPos = 0
            self.dataPos = 0
        self.update_figure()


    @pyqtSlot(bool)
    def sync_mode(self, on):
        """ Sync video with data, see README
        """
        if gd.runningvideo:
            if on:
                # fix start in video (a)
                #   self.videoPos could be wrong, should use real position in video!
                # put blue line on red one.
                change = round((self.dataPos - self.dataStart)*50)
                self.videoStart = self.videoStart + change/50
                print(f'nv {self.videoStart}')
                self.inSync = True
                # left button places red line
            else:
                # fix data wrt video start (b)
                # do not move video!
                file = gd.metaData['Video']
                gd.sessionInfo['Video'] = [ file,  str(self.videoStart), str(self.dataStart) ]
                saveSessionInfo(gd.sessionInfo)
                self.dataPos = self.dataStart
                self.inSync = False
            self.update_figure()
            
    @pyqtSlot()
    def frame_step(self):
        if gd.novideo:
            return
        if self.inSync:
            self.dataStart = self.dataStart + 0.02
        else:
            gd.player.frame_step()
            self.dataPos += 0.02
        self.update_figure()

    @pyqtSlot()
    def frame_back_step(self):
        if gd.novideo:
            return
        if self.inSync:
            self.dataStart = self.dataStart - 0.02
        else:
            self.dataPos -= 0.02
            gd.player.frame_back_step()
        self.update_figure()

    @pyqtSlot(float)
    def frame_seek(self, s):
        if gd.novideo:
            return
        if self.inSync:
            self.dataStart = self.dataStart + s
        else:
            gd.player.seek(s)
            self.dataPos += s
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
        sessionbase = re.sub('\\\\', '/', sessionbase)   # for windows
        if sessionbase not in session_file:
            # ignore
            return

        # update and use SubDir2
        tail = re.sub(sessionbase, '', session_file)
        tail = re.sub('^/', '', tail)   # hack voor windows
        b = os.path.basename(tail)
        subdir = re.sub(b, '', tail)
        gd.config['SubDir2'] = subdir


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
            fd.close()
        except IOError:
            print(f'selectSecond: cannot read Sessions file, should not happen  {session_file}')
            gd.config['Session2'] = 'None'
            saveConfig(gd.config)
            exit()
        gd.sessionInfo2 = yaml.load(inhoud, Loader=yaml.UnsafeLoader)

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
            
        getMetaData2()
        gd.cal_value2 = float(gd.metaData2['Calibration'])
        calibrate(True)
        self.update_the_2nd_models(session)

    def update_the_2nd_models(self, session):

        self._traces2 = gd.dataObject2
        self.secondary = True
        # reset slider
        xxx = gd.win.findChild(QObject, "slider")
        xxx.setProperty("value", 0)

        self.set_data_traces(local=True)
        self.update_figure()


        
    @pyqtSlot(str)
    def set_2nd_piece(self, name):
        gd.sd_selPiece = name
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

                # shift secondary using the slider
                xFrom2 = xFrom2 - self._shiftX2
                xTo2 = xTo2 - self._shiftX2

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

    @pyqtProperty(float, notify=shiftChanged)
    def shift(self):
        return self._shiftX2

    @shift.setter
    def shift(self, v):
        self._shiftX2 = int(v)
        self.shiftChanged.emit(self._shiftX2)
        self.set_2nd_piece(gd.sd_selPiece)

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
        self.fontP = FontProperties()

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

        self.fontP.set_size('xx-small')

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


            # gate angle of the stroke (optional?) See markers in Rower pages.
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
                d, aa = gd.prof_data[i]
                pa.append((d['Speed'], cntrating[i][1]))
            pa = list(zip(*pa))
            p = [ 10*x for x in pa[0]]  # ad hoc scaling, speed in decimeters/second
            self.ax4.scatter(list(range(len(gd.p_names))), p, marker='H', color='green', label='Accel')  # Todo: labels zichtbaar maken
            self.ax4.scatter(list(range(len(gd.p_names))), pa[1], marker='H', color='blue', label='Tempo')

            if self.legend:
                self.ax1.legend(loc='lower right', prop=self.fontP)

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

        self.een = None
        self.twee = None
        self.drie = None
        
        self._legend = True
        self.fontP = FontProperties()

        self._data = data

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.7)
        gs = self._figure.add_gridspec(5, 2)
        self.ax1 = self._figure.add_subplot(gs[0:3, :])
        self.ax2 = self._figure.add_subplot(gs[3:, 0])
        self.ax3 = self._figure.add_subplot(gs[3:, 1])

        self.fontP.set_size('xx-small')

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

        if gd.profile_available:
            # otherwise an error when starting the app. Sloppy!
            sensors = gd.sessionInfo['Header']
        else:
            sensors = []

        # stretcherforceX gaat uit van een bepaalde hoek van het voetenboord!
        if 'StretcherForceX' in sensors and not None:
            stretcher = True
        else:
            stretcher = False
            
        self.ax1.clear()
        self.ax1.grid(True)
        self.ax1.set_title('GateAngle - GateForceX')
        self.ax2.clear()
        self.ax2.grid(True)
        if stretcher:
            self.ax2.set_title('StretcherForceX')
        else:
            self.ax2.set_title('No Stretcher sensor')
        self.ax3.clear()
        self.ax3.grid(True)
        self.ax3.set_title('Power')

        # do plotting of all rowers for the selected piece
        cp = gd.crewPiece
        # speed, accel, pitch
        if gd.profile_available:
            rcnt = gd.sessionInfo['RowerCnt']
            if gd.crewPiece < len(gd.p_names):
                # a seperate piece, from the tumbler
                d, aa = gd.prof_data[cp]
                
                for r in range(rcnt):
                    sns = rowersensors(r)
                    if gd.sessionInfo['ScullSweep'] == 'sweep':
                        i = sns['GateAngle']
                        j = sns['GateForceX']
                    else:
                        i = sns['P GateAngle']
                        j = sns['P GateForceX']

                    if stretcher:
                        k = sns['Stretcher Z']
                        self.ax2.plot(gd.norm_arrays[gd.crewPiece, :, k], linewidth=0.6, label=f'R {r+1}')

                    self.ax1.plot(gd.norm_arrays[cp, :, i],
                                  gd.norm_arrays[cp, :, j], linewidth=0.6, label=f'R {r+1}')

                    self.ax3.plot(aa[0+3*r], linewidth=0.6, label=f'R {r+1}')

                    self.ax3.plot([gd.gmin[gd.crewPiece]], [0], marker='v', color='b')
                    self.ax3.plot([gd.gmax[gd.crewPiece]], [0], marker='^', color='b')

                # reference curve derived from the stroke
                sns = rowersensors(rcnt-1)
                fmean = d[rcnt-1]['GFEff']
                # just to make the curve better for our purpose.....
                fmean = 1.15*fmean
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    i = sns['GateAngle']

                    j = sns['GateForceX']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']
                minpos = min(gd.norm_arrays[cp, :, i])
                maxpos = max(gd.norm_arrays[cp, :, i])
                minarg = np.argmin(gd.norm_arrays[cp, :, i])
                maxarg = np.argmax(gd.norm_arrays[cp, :, i])
                fmin = gd.norm_arrays[cp, minarg, j]
                fmax = gd.norm_arrays[cp, maxarg, j]
                xstep = (maxpos - minpos)/20
                ystep = (fmin - fmax)/20   # assume fmin > fmax
                # is dit nodig? (totale hoek veel kleiner bij sweep (86 en 110)
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                    yref = np.array([fmin  , fmin+50,          1.05*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])
                else:
                    xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                    yref = np.array([fmin  , fmin+50,          1.05*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])

                curveref = make_interp_spline(xref, yref)
                xrefnew =  np.linspace(min(xref), max(xref), int(maxpos-minpos))

                self.ax1.plot(xrefnew, curveref(xrefnew), color='black', linewidth=0.5, linestyle=stippel)
                
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
                    if stretcher:
                        k = sns['Stretcher Z']
                    
                    # average
                    nmbrpieces = len(gd.p_names)
                    angle = np.zeros((100,))
                    force = np.zeros((100,))
                    stretcherZ = np.zeros((100,))
                    power = np.zeros((100,))
                    for p in range(nmbrpieces):
                        angle  += gd.norm_arrays[p, :, i]
                        force  += gd.norm_arrays[p, :, j]
                        if stretcher:
                            stretcherZ += gd.norm_arrays[p, :, k]
                        d, aa = gd.prof_data[p]
                        power  += aa[0+3*r]

                    # plot
                    self.ax1.plot(angle,
                                  force, linewidth=0.6, label=f'R {r+1}')

                    if stretcher:
                        self.ax2.plot(stretcherZ, linewidth=0.6, label=f'R {r+1}')
                    self.ax3.plot(power/nmbrpieces, linewidth=0.6, label=f'R {r+1}')
                # no reference curve here

            if self.legend:
                self.ax1.legend(loc='upper right', prop=self.fontP)
                #self.ax2.legend(loc='upper left', prop=self.fontP)
                self.ax3.legend(loc='upper right', prop=self.fontP)

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
        gd.metaData['CrewName'] = s[0]
        oldcal = float(gd.metaData['Calibration'])
        newcal = float(s[1])
        gd.metaData['Calibration'] = newcal
        gd.metaData['Misc'] = s[2]
        gd.metaData['Rowers'] = s[3]
        gd.metaData['Video'] = s[4]
        gd.sessionInfo['Video'][0] = s[4]
        gd.metaData['PowerLine'] = s[5]
        gd.metaData['Venue'] = s[6]
        saveMetaData(gd.metaData)
        saveSessionInfo(gd.sessionInfo)  # hack alleen vanwege video
        if oldcal != newcal:
            gd.cal_value = newcal/oldcal
            calibrate()
            gd.boattablemodel.make_profile()

# matplotlib plot in Rower Profile
class RowerForm(QObject):

    legendChanged = pyqtSignal()
    statusTextChanged = pyqtSignal()
    stateChanged = pyqtSignal()
    rowerDataChanged = pyqtSignal(list)

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
        self.fontP = FontProperties()

        self._data = data
        self.rower = rower

    @property
    def figure(self):
        return self._figure
    
    @figure.setter
    def figure(self, fig):
        self._figure = fig
        self._figure.set_facecolor('white')
        fig.subplots_adjust(hspace=0.4, wspace=0.1)
        gs = self._figure.add_gridspec(1, 1)
        self.ax1 = self._figure.add_subplot(gs[0, 0])

        self.fontP.set_size('xx-small')

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
        self.ax1.set_title('GateAngle - GateForceX/Y')

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
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                      gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.6, label=f'{gd.p_names[i]}')
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                      gd.norm_arrays[i, :, rsens['GateForceY']], linestyle=stippel, linewidth=0.6, label=f'{gd.p_names[i]}')
                    else:
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                      gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.6, label=f'{gd.p_names[i]}')
                        self.ax1.plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                      gd.norm_arrays[i, :, rsens['P GateForceY']], linestyle=stippel, linewidth=0.6, label=f'{gd.p_names[i]}')
            elif gd.rowerPiece[self.rower] == len(gd.p_names) + 1:
                # average
                angle = np.zeros((100,))
                forceX = np.zeros((100,))
                forceY = np.zeros((100,))
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    for i in range(len(gd.p_names)):
                        angle += gd.norm_arrays[i, :, rsens['GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['GateForceX']]
                        forceY += gd.norm_arrays[i, :, rsens['GateForceY']]
                    self.ax1.plot(angle/6, forceX/6, linewidth=0.6, label='FX')
                    self.ax1.plot(angle/6, forceY/6, linestyle=stippel, linewidth=0.6, label='FY')
                else:
                    for i in range(len(gd.p_names)):
                        angle += gd.norm_arrays[i, :, rsens['P GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['P GateForceX']]
                        forceY += gd.norm_arrays[i, :, rsens['P GateForceY']]
                    self.ax1.plot(angle/6, forceX/6, linewidth=0.6, label='FX')
                    self.ax1.plot(angle/6, forceY/6, linestyle=stippel, linewidth=0.6, label='FY')
            else:
                # normal pieces
                rp = gd.rowerPiece[self.rower] - 1
                sns = rowersensors(self.rower)

                # ad hoc angle x 10. Bettet via (max-min). Scale is for force
                # print(f'Create rowerplot for {self.rower}')
                outboat = [ d for d, e in gd.prof_data]
                ri = [a[self.rower] for a in outboat]    # rower info per piece
                fmean = ri[rp]['GFEff']
                # just to make the curve better for our purpose.....
                fmean = 1.15*fmean
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    i = sns['GateAngle']
                    j = sns['GateForceX']
                    k = sns['GateForceY']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']
                    k = sns['P GateForceY']

                
                # TESTING referentie curve
                # lengte uit tabel? Voorlopig 100, begin goed zetten
                # scale with avarage force
                minpos = min(gd.norm_arrays[rp, :, i])
                maxpos = max(gd.norm_arrays[rp, :, i])
                minarg = np.argmin(gd.norm_arrays[rp, :, i])
                maxarg = np.argmax(gd.norm_arrays[rp, :, i])
                fmin = gd.norm_arrays[rp, minarg, j]
                fmax = gd.norm_arrays[rp, maxarg, j]
                xstep = (maxpos - minpos)/20
                ystep = (fmin - fmax)/20   # assume fmin > fmax
                # sweep en scull versies?

                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                    yref = np.array([fmin  , fmin+50,          1.05*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])
                else:
                    xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                    yref = np.array([fmin  , fmin+50,          1.05*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])

                curveref = make_interp_spline(xref, yref)
                xrefnew =  np.linspace(min(xref), max(xref), int(maxpos-minpos))

                self.ax1.plot(gd.norm_arrays[rp, :, i],
                              gd.norm_arrays[rp, :, j], linewidth=0.6, label=f'{gd.p_names[rp]} FX')
                self.ax1.plot(gd.norm_arrays[rp, :, i],
                              gd.norm_arrays[rp, :, k], linestyle=stippel, linewidth=0.6, label=f'{gd.p_names[rp]} FY')
                self.ax1.plot(xrefnew, curveref(xrefnew), color='black', linewidth=0.5, linestyle=stippel)

                #print(ri[rp]['Slip'], "test ", gd.norm_arrays[rp, ri[rp]['Test'], j])
                # zoek plaats in gd.norm_array[rp, :, j] waar het slip punt is. welke waarde in profile opslaan naast Test?
                # sl = ri[rp]['Slip']
                # ypos = gd.norm_arrays[rp, ri[rp]['Test'], j]
                # self.ax1.plot([sl], [ypos], marker='>', color='g')
                

            if self.legend:
                self.ax1.legend(bbox_to_anchor=(1.0, 1), prop=self.fontP)

        self.stateChanged.emit()
        self.rowerDataChanged.emit([[ 'een', '1'], ['twee', '2']])

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

    @pyqtProperty(list, notify=rowerDataChanged)
    def rowerData(self):
        names = []
        if bool(gd.sessionInfo):
            for i in range(gd.sessionInfo['RowerCnt']):
                names.append(gd.metaData['Rowers'][i])
        else:
            names = [['empty', '0'], ['empty', '1']]            
        return names

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
                self.ax1.text(0.1, 0.5, 'Not used when showing piece "all".')
                pass
            elif gd.rowerPiece[self.rower] == len(gd.p_names) + 1:
                # average DOEN WE NIET
                self.ax1.text(0.02, 0.5, 'Not used when showing piece "average".')
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
