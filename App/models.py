"""The model related classes for the RTCnoord app."""

import os, re, yaml, time
from shutil import copyfile
import numpy as np

from PyQt5.QtCore import QVariant, QObject, pyqtSignal, pyqtSlot, pyqtProperty, QMetaObject, Qt, QTimer, QByteArray, QAbstractListModel, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor

import globalData as gd

from utils import *
from profil import profile
from report import make_pdf_report, make_csv_report, make_xlsx_report

class DataSerie(object):
    """Class to contain a data item for the datamodels"""

    def __init__(self, name, data, selected=False):
        self._name = name
        self._data = data
        self._selected = selected

    def name(self):
        return self._name

    def selected(self):
        return self._selected

    def data(self):
        return self._data


# dataModel for the listview to select sensors
class DataSensorsModel(QAbstractListModel):
    """

    """
    # Define role enum
    SelectedRole = Qt.UserRole
    NameRole = Qt.UserRole + 1
    DataRole = Qt.UserRole + 2

    _roles = {
        SelectedRole: b"selected",
        NameRole: b"name",
        DataRole: b"data"
    }

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self._data_series = []

    # data model from gd.sessionInfo['uniqHeader']
    #  we read the session file.
    def load_sessionInfo(self, sInfo=None):
        self._data_series.clear()
        # fill data from sessionInfo, remove Time and Normalized time columns
        n = sInfo.index('Normalized Time')
        for i, name in enumerate(sInfo[1:n]):
            series = DataSerie(name, i)
            self.add_data(series)

    def add_data(self, data_series):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data_series.append(data_series)
        self.endInsertRows()

    def roleNames(self):
        return self._roles

    def rowCount(self, parent=QModelIndex()):
        return len(self._data_series)

    def data(self, index, role=Qt.DisplayRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return QVariant()

        series = self._data_series[index.row()]

        if role == self.SelectedRole:
            return series.selected()
        elif role == self.NameRole:
            return series.name()
        elif role == self.DataRole:
            return series.data()

        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return False
        
        series = self._data_series[index.row()]
        if role == self.SelectedRole:
            series._selected = value
            self.dataChanged.emit(index, index, [role,])
            return True
                
        return False

    def del_all(self):
        self.beginRemoveColumns(QModelIndex(), 0, len(self._data_series))
        self._data_series = []
        self.endRemoveRows()
    


# dataModel for the makePiecesModel and viewPiecesModel
class DataPiecesModel(QAbstractListModel):

    # Define role enum
    SelectedRole = Qt.UserRole
    NameRole = Qt.UserRole + 1
    DataRole = Qt.UserRole + 2

    _roles = {
        SelectedRole: b"selected",
        NameRole: b"name",
        DataRole: b"data"
    }

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self._data_series = []
        
    def roleNames(self):
        return self._roles
    
    def add_piece(self, name, data):
        # print(name, data)
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data_series.append(DataSerie(name, data))
        self.endInsertRows()

    def del_piece(self, row):
        row = int(row)
        self.beginRemoveColumns(QModelIndex(), row, row)
        del self._data_series[row]
        self.endRemoveRows()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data_series)
        
    def data(self, index, role=Qt.DisplayRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return QVariant()
        
        series = self._data_series[index.row()]
        
        if role == self.SelectedRole:
            return series.selected()
        elif role == self.NameRole:
            return series.name()
        elif role == self.DataRole:
            return series.data()
        
        return QVariant()
    
    def setData(self, index, value, role=Qt.EditRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return False
        
        series = self._data_series[index.row()]
        if role == self.SelectedRole:
            series._selected = value
            self.dataChanged.emit(index, index, [role,])
            return True
                
        return False

    def alldata(self):
        return self._data_series

    def set_all(self, pieces):
        for (name, i, cr, tl) in pieces:
            self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
            self._data_series.append(DataSerie(name, i))
            self.endInsertRows()

    def del_all(self):
        self.beginRemoveColumns(QModelIndex(), 0, len(self._data_series))
        self._data_series = []
        self.endRemoveRows()


class BoatTableModel(QAbstractTableModel):

    # info from out and sessionInfo
    def __init__(self, out=None, parent=None):
        super().__init__(parent)

        self._data = []
        self._header = {}
        self._row = 0
        self._column = 0

    def columnCount(self, parent=QModelIndex()):
        return self._column

    def rowCount(self, parent=QModelIndex()):
        return self._row

    def data(self, index, role=Qt.DisplayRole):
        i = index.row()
        j = index.column()
        if role == Qt.DisplayRole:
            return self._data[i].data()[j]

    @pyqtSlot(int, Qt.Orientation, result="QVariant")
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header[section]
            else:
                return str(section)

    def del_all(self):
        self.beginRemoveColumns(QModelIndex(), 0, self._row)
        self._data = []
        self._row = 0
        self._column = 0
        self.endRemoveRows()
    
    @pyqtSlot(bool)
    def set_averaging(self, checked):
        gd.averaging = not checked
        self.make_profile()

    @pyqtSlot(bool)
    def set_filter(self, checked):
        gd.filter = not checked
        self.make_profile()

    @pyqtSlot(bool)
    def set_custom(self, checked):
        gd.custom_report = not checked
        self.make_profile()

    def fillBoatTable(self, out):
        self._data.clear()

        pieces = gd.sessionInfo['Pieces']
        cntrating = [cr for nm, x, cr, tl in pieces]

        # First header line
        n = 1
        series = DataSerie(n, [''] + ['Average'] + gd.p_names)
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data.append(series)

        # the rest
        # calculate averages
        self._data.append(
            DataSerie(2, ['Strokes'] + [''] + [c for c, r in cntrating]))
        rateavg = sum( [r for c, r in cntrating])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Stroke rate'] + [f'{rateavg:.0f}'] + [f'{r:.0f}' for c, r in cntrating]))
        rhythmavg = sum([d["Rhythm"] for d, e in out])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Rythm % cycle time'] + [f'{rhythmavg:.0f}'] + [f'{d["Rhythm"]:.0f}' for d, e in out]))
        # print(f' model split {[ d["Split"] for d, e in out]}')
        split = sum([d['Split'] for d, e in out])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['500m split'] + [f'{int(split/60)}:{split%60:04.1f}'] + [f'{int(d["Split"]/60)}:{d["Split"]%60:04.1f}' for d, e in out]))
        dist = sum([d["DistancePerStroke"] for d, e in out])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Distance/stroke'] + [f'{dist:.1f}'] + [f'{d["DistancePerStroke"]:.1f}' for d, e in out]))
        ploss = sum([d['PowerLoss'] for d, e in out])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Speed power loss(%)'] + [f'{ploss:.1f}'] + [f'{d["PowerLoss"]:.1f}' for d, e in out]))
        self._data.append(
            DataSerie(2, ['Max speed at % cycle'] + [''] + [f'{d["MaxAtP"]:.1f}' for d, e in out]))
        '''
        self._data.append(
            DataSerie(2, ['Min speed at % cycle'] + [''] + [f'{d["MinAtP"]:.1f}' for d, e in out]))
        '''
        self._data.append(
            DataSerie(2, ['Maximum Yaw (\u00b0)'] + [''] + [f'{d["YawMax"]:.1f}' for d, e in out]))
        self._data.append(
            DataSerie(2, ['Maximum Roll (\u00b0)'] + [''] + [f'{d["RollMax"]:.1f}' for d, e in out]))

        self.endInsertRows()
        self._column = len(self._data[0].data())
        self._row = len(self._data)

        # for i in self._data:
        #     print(i.data())

    # create complete profile here
    def prepareData(self):
        pcs = gd.sessionInfo['Pieces']
        if pcs == []:
            gd.profile_available = False
            self.del_all()   # nodig?
            return False
        gd.p_names = [ nm for nm, be, cr, tl in gd.sessionInfo['Pieces']]
        gd.out = profile()

        self.fillBoatTable(gd.out)
        for i in range(gd.sessionInfo['RowerCnt']):
            gd.rowertablemodel[i].fillRowerTable(gd.out)
            
    def make_profile(self):
        self.prepareData()
        gd.boatPlots.update_figure()
        gd.crewPlots.update_figure()        
        for i in range(gd.sessionInfo['RowerCnt']):
            gd.rowerPlots[i].update_figure()
            gd.stretcherPlots[i].update_figure()
        

    @pyqtSlot()
    def make_report(self):
        self.prepareData()    # maybe already done!

        if gd.profile_available:
            make_pdf_report()
            # make_csv_report()
            make_xlsx_report()

class RowerTableModel(QAbstractTableModel):

    # info from out and sessionInfo
    def __init__(self, rower, out=None, parent=None):
        super().__init__(parent)

        self._data = []
        self._header = {}
        self._row = 0
        self._column = 0
        self.rower = rower

    def columnCount(self, parent=QModelIndex()):
        return self._column

    def rowCount(self, parent=QModelIndex()):
        return self._row

    def data(self, index, role=Qt.DisplayRole):
        i = index.row()
        j = index.column()
        if role == Qt.DisplayRole:
            return self._data[i].data()[j]

    @pyqtSlot(int, Qt.Orientation, result="QVariant")
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._header[section]
            else:
                return str(section)

    def del_all(self):
        self.beginRemoveColumns(QModelIndex(), 0, self._row)
        self._data = []
        self._row = 0
        self._column = 0
        self.endRemoveRows()
    
    # averaging over the entire piece (use shortest piece for length)
    @pyqtSlot(bool)
    def set_averaging(self, checked):
        gd.averaging = not checked
        self.make_profile()

    def fillRowerTable(self, out):
        self._data.clear()
        
        pieces = gd.sessionInfo['Pieces']
        cntrating = [cr for nm, x, cr, tl  in pieces]

        # target values
        targets = gd.globals['Standards'][gd.metaData['BoatType']]

        # First header line
        n = 1
        series = DataSerie(n, ['', '2k Target', 'Average'] + gd.p_names)
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data.append(series)

        # how from self.rower to data?
        outboat = [ d for d, e in out]
        # outboat[piece][rower]
        ri = [a[self.rower] for a in outboat]    # rower info per piece
        # sp = [a['Split'] for a in outboat]       # split per piece

        # the rest
        self._data.append(
            DataSerie(2, ['Stroke rate'] + [''] + [''] + [f'{r:.0f}' for c, r in cntrating]))
        """
        self._data.append(
            DataSerie(2, ['' for i in range(len(gd.p_names)+3)]) )
        """
        avsplit = sum([d['Split'] for d, e in out])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['500m split'] + [''] + [f'{int(avsplit/60)}:{avsplit%60:04.1f}'] + [f'{int(d["Split"]/60)}:{d["Split"]%60:04.1f}' for d, e in out]))
        targ = targets['angleIn']
        avain = sum([r['CatchA'] for r in ri])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Catch angle (\u00b0)'] + [f'{targ:.0f}'] + [f'{avain:.0f}'] + [f'{r["CatchA"]:.0f}' for r in ri]))
        targ = targets['angleOut']
        avaout = sum([r['FinA'] for r in ri])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Finish angle (\u00b0)'] + [f'{targ:.0f}'] + [f'{avaout:.0f}'] + [f'{r["FinA"]:.0f}' for r in ri]))
        targ = targets['angleOut'] - targets['angleIn']
        avat = sum([r['FinA']-r['CatchA'] for r in ri])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Total angle (\u00b0)'] + [f'{targ:.0f}'] + [f'{avat:.0f}'] + [f'{r["FinA"]-r["CatchA"]:.0f}' for r in ri]))
        targ = targets['slipIn']
        aslip = sum([r['Slip'] for r in ri])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Catch slip (\u00b0) '] + [f'{targ:.0f}'] + [f'{aslip:.0f}'] + [f'{r["Slip"]:.0f}' for r in ri]))
        targ = targets['slipOut']
        awash = sum([r['Wash'] for r in ri])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Finish wash (\u00b0) '] + [f'{targ:.0f}'] + [f'{awash:.0f}'] + [f'{r["Wash"]:.0f}' for r in ri]))
        targ = targets['angleOut'] - targets['angleIn'] - targets['slipIn'] - targets['slipOut']
        effan = sum([r['EffAngle'] for r in ri])/len(gd.p_names)
        self._data.append(
            DataSerie(2, ['Effective angle (\u00b0)'] + [f'{targ:.0f}'] + [f'{effan:.0f}'] + [f'{r["EffAngle"]:.0f}' for r in ri]))
        self._data.append(
            DataSerie(2, ['Gate force average'] + [''] + [''] + [ f'{r["GFEff"]:.0f}' for r in ri]) )
        """
        self._data.append(
            DataSerie(2, ['Gate force max'] + [''] + [''] + [ f'{r["GFMax"]:.0f}' for r in ri]) )
        self._data.append(
            DataSerie(2, ['Ratio avg/max Gate force'] + [''] + [''] + ['', '', '', '', '', '', '' , '' ]))
        self._data.append(
            DataSerie(2, ['Gate force max at'] + [''] + [''] + ['', '', '', '', '', '', '' , '' ]))
        self._data.append(
            DataSerie(2, ['Gate force up to 70% at (\u00b0)'] + [''] + [''] + [f'{r["UpAt70"]:.0f}' for r in ri]))
        self._data.append(
            DataSerie(2, ['Gate force under 70% at (\u00b0)'] + [''] + [''] + [f'{r["DownAt70"]:.0f}' for r in ri]))
        self._data.append(
            DataSerie(2, ['' for i in range(len(gd.p_names)+3)]) )
        self._data.append(
            DataSerie(2, ['Work (J)'] + [''] + [''] + [f'{r["Work"]:.0f}' for r in ri]))
        """
        targ = targets['power']
        self._data.append(
            DataSerie(2, ['Power average (W)'] + [f'{targ:.0f}'] + [''] + [ f'{r["PMean"]:.0f}' for r in ri]) )
        self._data.append(
            DataSerie(2, ['Power/weight'] + [''] + [''] + [ f'{r["PperKg"]:.2f}' for r in ri]) )
        self._data.append(
            DataSerie(2, ['Progn Power target rate'] +  ['' for i in range(len(gd.p_names)+2)]) )
        
        # power benen romp bankje?

        self.endInsertRows()
        self._column = len(self._data[0].data())
        self._row = len(self._data)
        #print('rowertable')
        #for i in self._data:
        #    print(i.data())


# dataModel for the different boat types
class DataBoatsModel(QAbstractListModel, QObject):
    """

    """

    stateChanged = pyqtSignal()

    # Define role enum
    SelectedRole = Qt.UserRole
    NameRole = Qt.UserRole + 1
    DataRole = Qt.UserRole + 2

    _roles = {
        SelectedRole : b"selected",
        NameRole : b"name",
        DataRole : b"data"
    }
    
    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        self._data_series = []

    # data model to select boatinfo
    def load_boatsInfo(self):
        self._data_series.clear()
        boats = gd.globals['Boats']
        for i, name in enumerate(boats):
            series = DataSerie(name, i)
            self.add_data(series)

    def add_data(self, data_series):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data_series.append(data_series)
        self.endInsertRows()
    
    def roleNames(self):
        return self._roles
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data_series)
        
    def data(self, index, role=Qt.DisplayRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return QVariant()
        
        series = self._data_series[index.row()]
        if role == self.SelectedRole:
            return series.selected()
        elif role == self.NameRole:
            return series.name()
        elif role == self.DataRole:
            return series.data()
        
        return QVariant()
    
    def setData(self, index, value, role=Qt.EditRole):
        if(index.row() < 0 or index.row() >= len(self._data_series)):
            return False
        
        series = self._data_series[index.row()]
        if role == self.SelectedRole:
            series._selected = value
            self.dataChanged.emit(index, index, [role,])
            return True
                
        return False

    def alldata(self):
        return self._data_series

    def del_all(self):
        self.beginRemoveColumns(QModelIndex(), 0, len(self._data_series))
        self._data_series = []
        self.endRemoveRows()

    @pyqtSlot(str)
    def set_boattype(self, type):
        gd.metaData['BoatType'] = type
        saveMetaData(gd.metaData)
        gd.boattablemodel.make_profile()

    @pyqtProperty(list, notify=stateChanged)
    def the_boat_types(self):
        return [i.name() for i in self.alldata()]

    @pyqtProperty(int, notify=stateChanged)
    def current_boat_type(self):
        if gd.sessionInfo == {}:
            return 0
        return [i.name() for i in self.alldata()].index(gd.metaData['BoatType'])

        
