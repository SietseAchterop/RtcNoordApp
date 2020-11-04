"""Utility functions for the RTCnoord app"""

import sys, os, subprocess, socket, math, time, csv, yaml, copy, shlex, tempfile, shutil, re
from pathlib import Path, PurePath
from datetime import date

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
        fd.close()
    except IOError:
        if gd.os == 'win32':
            if not localSettingsDir.is_dir():
                localSettingsDir.mkdir()
            if not appConfDir.is_dir():
                appConfDir.mkdir()
        shutil.copyfile(appDir / 'App' / 'RtcApp', gd.configfile)
        fd = Path.open(gd.configfile, 'r')
        rtcnoordconfig = fd.read()
        config = yaml.load(rtcnoordconfig, Loader=yaml.UnsafeLoader)
        fd.close
        
    # we now have a configfile, now the base dir
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
        shutil.copyfile(appDir / 'configs' / 'RowerData.yaml', base_dir / 'configs' / 'RowerData.yaml')
        config['Session'] = 'None'
        saveConfig(config)
    # we now have the  data directories
    return config

def saveConfig(config):
    """Save config data to the yaml file."""
    with Path.open(gd.configfile, 'w') as fd:
        yaml.dump(config, fd)
    

def appconfigsDir():
    """ Return the config dir of the app """
    path = Path(sys.argv[0]).parent.absolute().parent / 'configs' 
    return path


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

def csvs2Dir():
    """Return the path to the csv_data dir as used for the secondary session."""
    path = Path.home() / gd.config['BaseDir'] / 'csv_data'
    if gd.config['SubDir2'] != '':
        path = path / gd.config['SubDir2']
    return path

def sessionsDir():
    """Return the path to the session_data dir."""
    path = Path.home() / gd.config['BaseDir'] / 'session_data'
    if gd.config['SubDir'] != '':
        path = path / gd.config['SubDir']
    return path

def sessions2Dir():
    """Return the path to the session_data dir as used for the secondary session."""
    path = Path.home() / gd.config['BaseDir'] / 'session_data'
    if gd.config['SubDir2'] != '':
        path = path / gd.config['SubDir2']
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

def readGlobals(cwd = 'onzin'):
    """Return the GlobalSettings from the config."""
    try:
        # PAS OP: klopt niet bij interactive, appconfdir geeft /usr/configs
        if cwd == 'onzin':
            fd = Path.open(appconfigsDir() / 'GlobalSettings.yaml')            
        else:
            fd = open(cwd + '/../configs/' + 'GlobalSettings.yaml')

        inhoud = fd.read()
        fd.close()
    except IOError:
        print('Cannot read GlobalSettings file.')
        exit()

    globals = yaml.load(inhoud, Loader=yaml.UnsafeLoader)
    return globals


# select and read session info
def loadSession():
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
        fd.close()
    except IOError:
        print(f'SelectSession: cannot read Sessions file, should not happen   {file}')
        gd.config['Session'] = 'None'
        saveConfig(gd.config)
        # make cleaner solution
        exit()

    # new config set
    return yaml.load(inhoud, Loader=yaml.UnsafeLoader)


def selectCurrentInteractive():
    """Used in main.interactive """
    session = gd.config['Session']
    session_file = sessionsDir() / (session + '.yaml')

    # from selectIt
    session_file = sessionsDir() / (session + '.yaml')
    cache_file = cachesDir() / (session + '.npy')

    # update sessionInfo
    try:
        fd = Path.open(session_file, 'r')
        inhoud = fd.read()
        fd.close()
    except IOError:
        print(f'selectCurrentInteractive: cannot read Sessions file, should not happen  {session_file}')
        print('   Restart complete interactive session!')
        return

    gd.sessionInfo = yaml.load(inhoud, Loader=yaml.UnsafeLoader)
    gd.p_names = [nm for nm, be, cr, tl in gd.sessionInfo['Pieces']]

    # update dataObject (should be there)
    try:
        fd = Path.open(cache_file, 'r')
        fd.close()
        gd.dataObject = np.load(cache_file)
    except IOError:
        print(f'selectCurrentInteractive: cannot read cachefile, should not happen  {cache_file}')
        exit()

    getMetaData(True)


def saveMetaData(metadata, savetime=False):
    # vervang metadata in csv file
    path = csvsDir() / (gd.config['Session'] + '.csv')
    #
    tmpdir = tempfile.gettempdir()
    tmpfd = Path(tmpdir) / 'rtcapp'
    shutil.move(path, tmpfd)

    d = date.today()
    with Path.open(path, 'w') as fd:
        '''
        '''
        #  write directly is faster, but we need to cater for the csv-delimiter
        #  make this better later

        # alleen tijd aanpassen bij savetime==True


        if gd.dialect.delimiter == ',':
            if savetime:
                fd.write(f'Metadata, {d.strftime("%d-%m-%Y")}\n')
            else:
                fd.write(f'Metadata, {metadata["Sessiontime"]}\n')

            fd.write('Crew name, ' + metadata['CrewName'] + '\n')
            fd.write('Boattype, ' + metadata['BoatType'] + '\n')
            fd.write('Calibration, ' + str(metadata['Calibration']) + '\n')
            fd.write('Venue, ' + metadata['Venue'] + '\n')
            for i in range(8):
                fd.write(f'Rower {i+1}, ' + metadata['Rowers'][i][0] + ', ' + str(metadata['Rowers'][i][1]) + ', ' + str(metadata['Rowers'][i][2]) + ', ' + str(metadata['Rowers'][i][3]) + '\n')        
            fd.write('Misc, ' + metadata['Misc'] + '\n')
            fd.write('Video, ' + metadata['Video'] + '\n')
            fd.write('Data source, ' + metadata['PowerLine'] + '\n')
            fd.write('Spare, ' + metadata['Spare'] + '\n')
        else:
            if savetime:
                fd.write(f'Metadata\t{d.strftime("%d-%m-%Y")}\n')
            else:
                fd.write(f'Metadata\t{metadata["Sessiontime"]}\n')
                
            fd.write('Crew name\t' + metadata['CrewName'] + '\n')
            fd.write('Boattype\t' + metadata['BoatType'] + '\n')
            fd.write('Calibration\t' + str(metadata['Calibration']) + '\n')
            fd.write('Venue\t' + metadata['Venue'] + '\n')
            for i in range(8):
                fd.write(f'Rower {i+1}\t' + metadata['Rowers'][i][0] + '\t' + str(metadata['Rowers'][i][1]) + '\t' + str(metadata['Rowers'][i][2]) + '\t' + str(metadata['Rowers'][i][3]) + '\n')        
            fd.write('Misc\t' + metadata['Misc'] + '\n')
            fd.write('Video\t' + metadata['Video'] + '\n')
            fd.write('Data source\t' + metadata['PowerLine'] + '\n')
            fd.write('Spare\t' + metadata['Spare'] + '\n')
        count = 0
        with open(tmpfd) as infile:
            for line in infile:
                if count < 17:  # number of lines with metadata to skip
                    count += 1
                else:
                    fd.write(line)

def saveSessionInfo(sessionInfo):
    """Save session data to the yaml file."""
    file = sessionsDir() / (gd.config['Session'] + '.yaml')
    with Path.open(file, 'w') as fd:
        yaml.dump(sessionInfo, fd)
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

    After a first use metadata is present in the higher columns, containing the SessionInfo data.

    === Todo
    Zet metadata voor csvdata indien nog niet aanwezig
       os.system(f'mv {csvfile} {saved};  cat {metadata} {saved} > {csvfile}')

    Metadata staat er daarmee altijd
    Aantal rijen van metadata moet altijd hetzelfde blijven, en lengte van rows niet niet langer worden dan de rest (iets van 20 velden)
    Dus
     - vul sessionInfo met metadata
     - lees csvfile

    In Session info tab
      save knop voor update metadata in csvfile
          csvdata = tail (wordcount - metadatalenght)
          os.system(f'cat {metadata} {csvdata} > {csvfile}')


    sessioninfo splitsen in deel csv en deel sessioninfo, of dubbel in csv?
    

    with statement gebruiken!

    """

    path = csvsDir() / (config['Session'] + '.csv')

    # hier zorgen dat metadata er voor staat

    with Path.open(path, newline='') as fd:
        gd.dialect = csv.Sniffer().sniff(fd.readline())
        fd.seek(0)
        reader = csv.reader(fd, gd.dialect)    

        header = next(reader)
    if header[0] == 'Time':
        tmpdir = tempfile.gettempdir()
        tmpfd = Path(tmpdir) / 'rtcapp'
        metadata = appconfigsDir() / 'metadata.csv'
        shutil.move(path, tmpfd)
        with open(path, 'w') as fd:
            with open(metadata) as infile:
                for line in infile:
                    if gd.dialect.delimiter != ',':
                        line = re.sub(',', gd.dialect.delimiter, line)
                    fd.write(line)
            with open(tmpfd) as infile:
                for line in infile:
                    fd.write(line)

    #  now for real
    csvpieces = []   # for when the csv file is made up from multiple pieces from the peach data.
    with Path.open(path, newline='') as fd:
        reader = csv.reader(fd, gd.dialect)    

        # skip the 17 metadata lines (will be processed later)
        for i in range(17):
            header = next(reader)
        
        # the peach data
        header = next(reader)
        lenheader = len(header)
        header2 = next(reader)

        # aquire boat type from first 2 rows. See makecache
        # cope with backwings and there "wrong" connection of the sensors?

        # We can now cope with concatenated csv files created with powerline
        #   we skip the first 2 lines of each part
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
            # we leave room for the sessioninfo metadata
            for i in range(lenheader):
                if row[i] == '':
                    row[i] = float('NaN')
                else:
                    row[i] = float(row[i])
            csvdata.append(row)
        gd.sessionInfo['CsvPieces'] = csvpieces
    
    # if no metadata, then put defaults in
    #  Metadata to be found in row 3 and column lenheader+2

    # else, use it to fill sessioninfo

    return header, header2

def getMetaData(interactive=False):
    path = csvsDir() / (gd.config['Session'] + '.csv')

    with Path.open(path, newline='') as fd:
        gd.dialect = csv.Sniffer().sniff(fd.readline())
        fd.seek(0)  # waarom ook al weer?
        reader = csv.reader(fd, gd.dialect)    

        # voorlopig vaste volgorde in metadata!!
        i = next(reader)
        gd.metaData['Sessiontime'] = i[1]
        i = next(reader)
        gd.metaData['CrewName'] = i[1]
        i = next(reader)
        gd.metaData['BoatType'] = i[1]
        i = next(reader)
        gd.metaData['Calibration'] = i[1]
        i = next(reader)
        gd.metaData['Venue'] = i[1]

        rwrs = []
        for k in range(8):
            i = next(reader)
            rwrs.append([i[1], i[2], i[3], i[4]])
        gd.metaData['Rowers'] = rwrs

        i = next(reader)
        gd.metaData['Misc'] = i[1]
        i = next(reader)
        gd.metaData['Video'] = i[1]
        i = next(reader)
        gd.metaData['PowerLine'] = i[1]
        i = next(reader)
        gd.metaData['Spare'] = i[1]

    # voorlopig dubbelop
    gd.sessionInfo['Video'][0] = gd.metaData['Video']
    
    gd.cal_value = float(gd.metaData['Calibration'])

    if interactive == False:
        # list with data for the session Info tab (placeholdertext)
        sinfo = [
            gd.metaData['CrewName'],
            gd.cal_value,
            gd.metaData['Misc'],
            gd.metaData['Rowers'],
            gd.metaData['Video'],
            gd.metaData['PowerLine'],
            gd.metaData['Venue'],
            '...'
        ]

        gd.crewPlots.sessionsig.emit(sinfo)

    calibrate()

def getMetaData2():
    path = csvs2Dir() / (gd.config['Session2'] + '.csv')

    with Path.open(path, newline='') as fd:
        dialect = csv.Sniffer().sniff(fd.readline())
        fd.seek(0)  # waarom ook al weer?
        reader = csv.reader(fd, dialect)    

        i = next(reader)
        # voorlopig vaste volgorde in metadata!!
        i = next(reader)
        gd.metaData2['CrewName'] = i[1]
        i = next(reader)
        gd.metaData2['BoatType'] = i[1]
        i = next(reader)
        gd.metaData2['Calibration'] = i[1]
        i = next(reader)
        gd.metaData2['Venue'] = i[1]

        rwrs = []
        for k in range(8):
            i = next(reader)
            rwrs.append([i[1], i[2], i[3], i[4]])
        gd.metaData2['Rowers'] = rwrs

        i = next(reader)
        gd.metaData2['Misc'] = i[1]
        i = next(reader)
        gd.metaData2['Video'] = i[1]
        i = next(reader)
        gd.metaData2['PowerLine'] = i[1]
        i = next(reader)
        gd.metaData2['Spare'] = i[1]

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
    if np.sum(gd.dataObject[50, distsens]) == 0:  # we assume csv file is not too small
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
    #  depend on correct connections!  (backwings)
    rowercnt = gd.sessionInfo['RowerCnt'] = int(max(n)) - int(min(n)) + 1
    gd.sessionInfo['RowerCnt'] = rowercnt
    if int(min(n)) != 1:
        print('WARNING: Rower numbering in header2 should start with 1!')

    getMetaData()
    
    # Which boats/standards row to use?
    #  set default, can be changed in SessionInfo tab
    if gd.metaData['BoatType'] is None:
        if gd.sessionInfo['ScullSweep'] == 'sweep':
            if rowercnt == 2:
                gd.metaData['BoatType'] = 'M2-'
            elif rowercnt == 4:
                gd.metaData['BoatType'] = 'M4-'
            elif rowercnt == 8:
                gd.metaData['BoatType'] = 'M8+'
            else:
                print(f"should not happen: rowercnt = {rowercnt}")
        else:
            if rowercnt == 1:
                gd.metaData['BoatType'] = 'M1x'
            elif rowercnt == 2:
                gd.metaData['BoatType'] = 'M2x'
            elif rowercnt == 4:
                gd.metaData['BoatType'] = 'M4x'
            else:
                print(f"should not happen: rowercnt = {rowercnt}")

    gd.sessionInfo['uniqHeader'] = h1

    saveSessionInfo(gd.sessionInfo)

    gd.mainPieces.update_the_models(gd.config['Session'])

    # boattype to csv-metadata
    # savetime eigenlijk fout bij repair van cache!
    saveMetaData(gd.metaData, True)


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
