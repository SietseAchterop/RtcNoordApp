"""Utility functions for the RTCnoord app"""

import sys, os, subprocess, socket, math, time, csv, yaml, copy, shlex
from pathlib import Path
from shutil import copyfile

import globalData as gd

import numpy as np
try:
    import mympv
except OSError:
    gd.novideo = True
    print('nompv')

import globalData as gd
from catapult import catapult

# sampling rate of the logger
Hz = 50

def startup():
    """Determine platform we are on.
Load the config file to find the data and session to use.

    Create a config file in the appropriate location, if it does not exist.
    """

    # determine OS
    gd.os = sys.platform
    try:
        os.environ['ANDROID_ARGUMENT']
        gd.os = 'android'
    except KeyError:
        pass

    if gd.os == 'linux' or gd.os == 'android':
        gd.configfile = Path.home() / '.config' / gd.appname
    elif gd.os == 'win32':
        localSettingsDir = Path.home() / 'Application Data' / 'Local Settings'
        appConfDir = localSettingsDir / gd.orgname
        gd.configfile = appConfDir / gd.appname
    elif gd.os == 'darwin':
        gd.configfile = Path.home() / 'Library' / 'Application Support' / gd.appname

    appDir = Path(sys.argv[0]).parent.absolute().parent

    # read or create configfile
    #  and AppAuthor dir on win32 if needed
    try:
        fd = Path.open(gd.configfile, 'r')
        rtcnoordconfig = fd.read()
        config = yaml.load(rtcnoordconfig, Loader=yaml.UnsafeLoader)
    except IOError:
        if gd.os == 'win32':
            if not localSettingsDir.is_dir():
                localSettingsDir.mkdir()
            if not appConfDir.is_dir():
                appConfDir.mkdir()
        copyfile(appDir / 'App' / 'RtcApp', gd.configfile)
        fd = Path.open(gd.configfile, 'r')
        rtcnoordconfig = fd.read()
        config = yaml.load(rtcnoordconfig, Loader=yaml.UnsafeLoader)

    # we now have a configfile
    base_dir = Path.home() / config['BaseDir']
    if not base_dir.is_dir():
        base_dir.mkdir()
        (base_dir / 'configs').mkdir()
        (base_dir / 'csv_data').mkdir()
        (base_dir / 'session_data').mkdir()
        (base_dir / 'caches').mkdir()
        (base_dir / 'videos').mkdir()
        (base_dir / 'reports').mkdir()
        (base_dir / 'peach').mkdir()
        # fill configs
        copyfile(appDir / 'configs' / 'GlobalSettings.yaml', base_dir / 'configs' / 'GlobalSettings.yaml')
        copyfile(appDir / 'configs' / 'session_template.yaml', base_dir / 'configs' / 'session_template.yaml')
        copyfile(appDir / 'configs' / 'RowerData.yaml', base_dir / 'configs' / 'RowerData.yaml')
        config['Session'] = 'None'
        saveConfig(config)
    # we now have the  data directories
    return config

def saveConfig(config):
    """Save config data to the yaml file."""
    fd = Path.open(gd.configfile, 'w')
    yaml.dump(config, fd)

def readGlobals():
    """Return the GlobalSettings from the config."""
    try:
        fd = Path.open(configsDir() / 'GlobalSettings.yaml')
        inhoud = fd.read()
    except IOError:
        print('Cannot read GlobalSettings file.')
        exit()

    globals = yaml.load(inhoud, Loader=yaml.UnsafeLoader)
    return globals

def configsDir():
    """Return the path to the configs dir."""
    path = Path.home() / gd.config['BaseDir'] / 'configs'
    return path

def csvsDir():
    """Return the path to the csv_data dir."""
    path = Path.home() / gd.config['BaseDir'] / 'csv_data'
    if gd.config['SubDir'] != '':
        path = path / gd.config['SubDir']
    return path

def sessionsDir():
    """Return the path to the session_data dir."""
    path = Path.home() / gd.config['BaseDir'] / 'session_data'
    if gd.config['SubDir'] != '':
        path = path / gd.config['SubDir']
    return path

def cachesDir():
    """Return the path to the caches dir."""
    path = Path.home() / gd.config['BaseDir'] / 'caches'
    if gd.config['SubDir'] != '':
        path = path / gd.config['SubDir']
    return path

def reportsDir():
    """Return the path to the reports dir."""
    path = Path.home() / gd.config['BaseDir'] / 'reports'
    if gd.config['SubDir'] != '':
        path = path / gd.config['SubDir']
    return path


# select and read session info
def selectSession():
    """Load the selected session.

    Use session None if the selected one does not exist
    """

    if not gd.config['Session']:
        print('No session set, should not happen')

    session = gd.config['Session']
    file = sessionsDir() / (session + '.yaml')

    inhoud = ''
    try:
        fd = Path.open(file, 'r')
        inhoud = fd.read()
    except IOError:
        print(f'SelectSession: cannot read Sessions file, should not happen   {file}')
        gd.config['Session'] = 'None'
        saveConfig(gd.config)
        # make cleaner solution
        exit()

    # new config set
    return yaml.load(inhoud, Loader=yaml.UnsafeLoader)


def saveSessionInfo(sessionInfo):
    """Save session data to the yaml file."""
    file = sessionsDir() / (gd.config['Session'] + '.yaml')
    fd = Path.open(file, 'w')
    yaml.dump(sessionInfo, fd)
    # waarom dit?
    gd.p_names = [nm for nm, be, cr, tl in sessionInfo['Pieces']]



def calibrate(secondary=False):
    """Calibrate speed and distance data"""
    if not secondary:
        try:
            i = gd.sessionInfo['Header'].index('Speed')
        except ValueError:
            # when a new session is created
            return
        gd.dataObject[:, i] = gd.dataObject[:, i] * gd.cal_value
        i = gd.sessionInfo['Header'].index('Distance')
        gd.dataObject[:, i] = gd.dataObject[:, i] * gd.cal_value
    else:
        i = gd.sessionInfo2['Header'].index('Speed')
        gd.dataObject2[:, i] = gd.dataObject2[:, i] * gd.cal_value2
        i = gd.sessionInfo2['Header'].index('Distance')
        gd.dataObject2[:, i] = gd.dataObject2[:, i] * gd.cal_value2
        

# csv and session file have same name
def readCsvData(config, csvdata):
    """Read data for a session from the csv-file.

    Csv data can use comma or tab as delimiter
    """
    
    path = csvsDir() / (config['Session'] + '.csv')
    fd = Path.open(path, newline='')
    dialect = csv.Sniffer().sniff(fd.read(20000))
    fd.seek(0)
    reader = csv.reader(fd, dialect)    

    # if we could use the logger directly.
    # preheader:  rtcnoord, logger, filename, from, to

    """
    Idea:
    Read first 10 columns to determine number of relevant colums (untill Normalized time.
    The further columns are then free for other use: meta data for the session.
       of repair data

    JA, en session info er eventueel bij schrijven!

    """

    header = next(reader)
    lenheader = len(header)
    header2 = next(reader)
    # aquire boat type from first 2 rows?
    # cope with backwings and there "wrong" connection of the sensors?

    # we can now cope with concatenated csv files created with powerline
    csvpieces = []
    skip = False
    for line, row in enumerate(reader):
        if skip:
            skip = False
            continue
        if len(row) == 0:
            break
        if row[0] == 'Time':
            skip = True
            csvpieces.append(line/Hz)
            continue
        for i in range(lenheader):
            if row[i] == '':
                row[i] = float('NaN')
            else:
                row[i] = float(row[i])
        csvdata.append(row)
    gd.sessionInfo['CsvPieces'] = csvpieces
    return header, header2

def makecache(file):
    """Create and cache the data read from the csv-file in a .npy file """
    csvdata = []
    h1, h2 = readCsvData(gd.config, csvdata)
    gd.sessionInfo['Header']   = h1
    gd.sessionInfo['Header2']  = h2
    gd.sessionInfo['ScalingFactors'] = factors()

    gd.dataObject = np.asarray(csvdata)

    # forces to Newton
    for s in range(len(h1)):
        if 'Force' in h1[s]:
            gd.dataObject[:, s] = gd.dataObject[:, s] * 9.81

    # shift seat positions, to get a better view in ViewPiece
    for s in range(len(h1)):
        if h1[s] == 'Seat Posn':
            gd.dataObject[:, s] = gd.dataObject[:, s] + 700

    # negate StretcherForceX
    for s in range(len(h1)):
        if 'StretcherForceX' in h1[s]:
            gd.dataObject[:, s] = -gd.dataObject[:, s]

    # impellor working?
    gd.sessionInfo['noDistance'] = False
    distsens = h1.index('Distance')
    if np.sum(gd.dataObject[100, distsens]) == 0:
        gd.sessionInfo['noDistance'] = True

    # use catapult data if available
    catapult()

    np.save(file, gd.dataObject)

    # correction for backwing rigging: no seat position 1 means backwing.
    #    not now

    # use stroke rower to determine start of stroke and rating
    #   bow has rower number 1
    try:
        h1.index('P GateAngle')
        gd.sessionInfo['ScullSweep'] = 'scull'
        indexes = [i for i, x in enumerate(h1) if x == "P GateAngle"]
        i = indexes[-1]
        indexes = [i for i, x in enumerate(h1) if x == "P GateForceX"]
        j = indexes[-1]
    except ValueError:
        h1.index('GateAngle')
        gd.sessionInfo['ScullSweep'] = 'sweep'
        indexes = [i for i, x in enumerate(h1) if x == "GateAngle"]
        i = indexes[-1]
        indexes = [i for i, x in enumerate(h1) if x == "GateForceX"]
        j = indexes[-1]

    gd.sessionInfo['Tempi'] = tempi(gd.dataObject[:, i], gd.dataObject[:, j])

    # add position number to sensor name
    n = []
    h1 = copy.copy(h1)
    for i in range(len(h1)):
        if not (h2[i] == 'Boat' or h2[i] == ''):
            n.append(h2[i])
            h1[i] = h1[i] + ' ' + h2[i]
            h2[i] = int(h2[i])
    # number of rowers
    #  depend on correct connections (backwings)
    rowercnt = gd.sessionInfo['RowerCnt'] = int(max(n)) - int(min(n)) + 1
    gd.sessionInfo['RowerCnt'] = rowercnt
    if int(min(n)) != 1:
        print('WARNING: Rower numbering in header2 should start with 1!')

    # Which boats/standards row to use?
    #  set default, can be changed in SessionInfo tab
    if gd.sessionInfo['BoatType'] is None:
        if gd.sessionInfo['ScullSweep'] == 'sweep':
            if rowercnt == 2:
                gd.sessionInfo['BoatType'] = 'M2-'
            elif rowercnt == 4:
                gd.sessionInfo['BoatType'] = 'M4-'
            elif rowercnt == 8:
                gd.sessionInfo['BoatType'] = 'M8+'
            else:
                print(f"should not happen: rowercnt = {rowercnt}")
        else:
            if rowercnt == 1:
                gd.sessionInfo['BoatType'] = 'M1x'
            elif rowercnt == 2:
                gd.sessionInfo['BoatType'] = 'M2x'
            elif rowercnt == 4:
                gd.sessionInfo['BoatType'] = 'M4x'
            else:
                print(f"should not happen: rowercnt = {rowercnt}")

    gd.sessionInfo['uniqHeader'] = h1

    saveSessionInfo(gd.sessionInfo)


def tempi(gateAngle, gateForce):
    """Creates a list with strokes from the session

    Returns:
       [(strokestart in seconds/Hz steps, rating)]
    """

    # negative edge of a gateangle is the beginning of a cycle?
    #   or in the recover: oars perpendicular on the boat
    # only recognize tempi between 10 en 60
    tempoList = []
    i = 0
    end = len(gateAngle)
    state = 1
    while i < end:
        if math.isnan(gateAngle[i]):
            i += 1
            state = 1
            continue
        if state == 1:
            # zero crossing to negative values
            if gateAngle[i] > 5:
                state = 2
        elif state == 2:
            # zero crossing!
            if gateAngle[i] < 0:
                strokestart = i
                i += 2
                state = 3
        elif state == 3:
            #
            if gateAngle[i] < -3:
                state = 4
        elif state == 4:
            # zero crossing to higher values
            if gateAngle[i] > 0:
                i += 2
                state = 5
        elif state == 5:
            if gateAngle[i] > 5:
                state = 6
        elif state == 6:
            # end of cycle
            if gateAngle[i] < 0:
                stroketime = (i - strokestart)
                rating = 60*Hz/stroketime
                if rating < 10 or rating > 60:
                    # tempo < 10 or > 60,  restart
                    state = 1
                # record stroke
                tempoList.append((strokestart, rating))
                strokestart = i
                i += 2
                state = 3
        i += 1

    # we use the turning point in the gate force at the catch as the starting point
    return tempoList

    """
    Using gate force is not very accurate or robust
    # filter the signal a bit
    [B, A] = signal.butter(4, 2*5/Hz)
    # filtfilt cannot cope with Nans.
    for j in range(len(gateForce)):
        if math.isnan(gateForce[j]):
            gateForce[j] = 0.0
    gate_f = signal.filtfilt(B, A, gateForce)

    # use first and second catch of stroke rower
    catchList = []
    end = len(tempoList) - 2
    for i, st in enumerate(tempoList):
        t, r = st
        # search in first halve of the strokes
        next = int(t+25*60/r)
        catch = t+np.argmin(gate_f[t: next])
        catchList.append((catch, r))
        if i == end:
            break

    return catchList
    """


def n_catches(n, x):
    """Return n catches starting at x"""
    ll = []
    for i, (j, _) in enumerate(gd.sessionInfo['Tempi']):
        if j < x:
            continue
        ll.append(j)
        if len(ll) == n:
            break
    return ll


def rowersensors(rower):
    """ returns dictionary with sensorname and columnnumber in dataObject """
    #  only once per session
    h1 = gd.sessionInfo['Header']
    h2 = gd.sessionInfo['Header2']
    # which sensors for this rower?
    sindex = {}
    j = -1
    for s, n in zip(h1, h2):
        j += 1
        try:
            i = int(n)
        except ValueError:
            continue
        if i-1 == rower:  # internally we start at 0
            # Need correct numbers in csv!! (starting from 2)
            sindex[s] = j
    if sindex == {}:
        print('Empty rowersensors(rower), error in csv-header?')
    return sindex


# Video processing
def videoFile(mp4file):
    """Return the path to the session."""
    path = Path.home() / gd.config['BaseDir'] / 'videos' / mp4file
    return path


def startVideo():
    if gd.novideo:
        return
    gd.player = mympv.MPV()
    gd.player.pause = True
    gd.player.window_scale = 0.5
    gd.runningvideo = True


def stopVideo():
    gd.player.terminate()
    del(gd.player)
    gd.runningvideo = False


def factors():
    """ return scaling factor for each sensor."""

    # note Vel before without it, and the break!
    f = {
        'GateAngleVel': 3,
        'GateAngle': 10,
        'GateForce': 1,
        'Seat Posn Vel': 0.5,
        'Seat Posn': 1,
        'StretcherForceX': 1,
        'Stretcher': 8,
        'Speed': 2,
        'Accel': 40,
        'Roll': 50,
        'Pitch': 50,
        'Yaw': 50
        }

    h = gd.sessionInfo['Header']
    result = []
    for s in h:
        r = 1
        found = False
        for k in f:
            if k in s:
                # print(k, '->', f[k])
                r = f[k]
                result.append(r)
                found = True
                break
        if not found:
            result.append(r)
    return result
