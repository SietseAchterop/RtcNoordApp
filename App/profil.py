"""The profile module

Contains the functions to create and visualise the profiles

This file contains the following functions:

   * profile - creates the basic profile and returns a data structure
   * visualise - makes a visualisation of the data structure

"""
import sys, os, math, time, csv, yaml
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d

import globalData as gd
from utils import *

def profile():
    """Create a profile with averaging over n strokes

    Globals
    ----
    Uses the following global data from globalData
      config, sessionInfo, dataObject


    Parameters
    ----------

    """
    # offset: how much later to start

    pieces = gd.sessionInfo['Pieces']
    if pieces == []:
        gd.profile_available = False
        return []
    
    # allocate array for the average arrays, we need at least one cycle
    length = int(1.5*Hz*60/min([r for name, (a, b), (cnt, r), tl in pieces]))
    sensors = gd.sessionInfo['Header']
    uniqsens = gd.sessionInfo['uniqHeader']
    av_arrays = np.zeros((len(pieces), length, len(sensors)))

    # how many strokes to use
    if gd.averaging:
        n = min([cnt for name, (a, b), (cnt, r), tl in pieces])
    else:
        n = 1

    # average the data
    #  make offset possible when n == 1?
    #  how to cope with too much variation in tempo?
    for i, p in enumerate(pieces):
        nm, be, c, st = p
        for j in range(n):
            r = st[j] + length
            av_arrays[i, :, :] += gd.dataObject[st[j]:r, :]
    av_arrays = av_arrays/n

    # filter some signals: speed, power, position. But not stretcher RL or TB
    [B, A] = signal.butter(4, 2*5/Hz)
    #   before or after averaging?
    if gd.filter:
        # here the general signals
        i = sensors.index('Accel')
        av_arrays[:, :, i] = signal.filtfilt(B, A, av_arrays[:, :, i])

    # scull: gate angle and force:  average and add
    #        Use port side
    if gd.sessionInfo['ScullSweep'] == 'scull':
        for i, s in enumerate(sensors):
            # note: assume S site is at next position!
            if s.find('P GateAngle') >= 0:
                av_arrays[:, :, i] = (av_arrays[:, :, i] + av_arrays[:, :, i+1])/2
            if s.find('P GateForce') >= 0:
                av_arrays[:, :, i] =  av_arrays[:, :, i] + av_arrays[:, :, i+1]

    # test nan
    for i in range(len(pieces)):
        for j in range(len(sensors)-2):
            #  Stretcher RL en TB will always have nan values!
            #  Speed Pos (Vel) can alos miss values.
            #  we will ignore them for the moment
            if 'Stretcher' not in sensors[j]:
                printit = True
                for k, c in enumerate(av_arrays[i, :, j]):
                    # print only one
                    if math.isnan(c):
                        if printit:
                            print(f'NaN in piece {i} in {uniqsens[j]} sensor at pos {k}')
                            printit = False

    # now the real computations
    outcome = []
    # allocate norm_arrays
    gd.norm_arrays = np.empty((len(pieces), 100, len(sensors)))
    gd.gmin = [0]*len(pieces)
    gd.gmax = [100]*len(pieces)

    for i, pp in enumerate(pieces):
        outcome.append(pieceCalculations(pp, i, av_arrays[i, :, :]))

    saveSessionInfo(gd.sessionInfo)
    gd.profile_available = True
    return outcome


def pieceCalculations(piece, idx, a):
    """Calculate all parameters needed for the protocol

    Parameters
    ----------
    piece: the piece

    idx: index pieces array

    a: numpy.array (sensors, length)
    Array containing the averaged sensor data for the stroke

    Returns
    -------
    outcome: dict with calculated values
       outcome[i], with i an integer is info for roweri
    profile_data: extra arrays per rower: power, ...
       sizes depend on boattype and number of rowers
    """

    # will need filtering for some signals
    [B, A] = signal.butter(4, 2*5/Hz)
    #  We assume that there are NO NaN's in the pieces

    nm, aa, (scnt, r), sp = piece
    out = {}
    out['PieceName'] = nm

    sensors = gd.sessionInfo['Header']

    """ What we need:
    Boatreport:
      - table boat parameters
      - normalized graphs
          - speed and acceleration
          - pitch, roll, yaw
          - accell/powerloss agains tempi of different pieces ?
    """
    # number of strokes and average rating: in sessionInfo

    # 500 meter split in seconds
    i = sensors.index('Speed')
    speed = np.mean(a[:, i])
    out['Speed'] = speed

    # Speed from impeller is better!
    # use entire piece
    distsens = gd.sessionInfo['Header'].index('Distance')
    bb = gd.dataObject[sp[0], distsens]
    ee = gd.dataObject[sp[-1], distsens]
    speedimp =  (ee - bb)/(float(sp[-1] - sp[0])/50)
    out['Speedimp'] = speedimp

    if gd.sessionInfo['noDistance']:
        # just for now
        out['Split'] = 0
    else:
        out['Split'] = 500/speedimp
    # print(f'Split {speedimp}   {out["Split"]} in {nm}')

    # distance per stroke: 60*speed/rating
    out['DistancePerStroke'] = 60 * speedimp / r

    out['Starting points'] = sp

    # maximum speed at %cycle
    #  filter speed, find maximum in stroke.
    length = sp[1] - sp[0]
    f_speed = signal.filtfilt(B, A, a[0: length, i])
    mm = f_speed.argmax()
    mn = f_speed.argmin()
    out['MaxAtP'] = (mm/length)*100
    out['MinAtP'] = (mn/length)*100
    # positive en negative acceleration at %cycle

    # center yaw, pitch and angle ( averages in boat table) ?
    i = sensors.index('Yaw Angle')
    yaw_abs = np.absolute(a[:, i])
    out['YawMax'] = yaw_abs.max()
    i = sensors.index('Roll Angle')
    roll_abs = np.absolute(a[:, i])
    out['RollMax'] = roll_abs.max()

    # TODO
    # speed fluctuation
    #    max - min
    # speed fluctuation power loss
    i = sensors.index('Speed')
    out['PowerLoss'] = 100*(1 - speedimp**3/np.mean(a[:, i]**3))

    """
    Crewreport:
      - graphs to compare rowers
        - gate angles  (+accel as support)
        - seatposition (+accel as support)
        - gate force   (+accel as support)
        - gate force agains gate angle
        - stretcher force
        - stretcher force agains gate angle
        - propulsive force?
    """



    """
    Rower report, one for each rower
      - add table with targets
        - slip
        -
      - graphs
        - gate angle
        - gate force X/Y
        - power, handlevel, handlevdsseat
        - stretcher forces

    """
    # allocate data for profile data: power, handleVel, handleVDSSeat (3)
    #   or in a 3rd dimension?
    rwcnt = gd.sessionInfo['RowerCnt']
    length = a.shape[0]
    prof_data = np.zeros((3*rwcnt, length))

    scullsweep = gd.sessionInfo['ScullSweep']
    boattype = gd.sessionInfo['BoatType']
    inboard = gd.globals['Boats'][boattype]['inboard']
    outboard = gd.globals['Boats'][boattype]['outboard']
    
    for rwr in range(rwcnt):
        rsens = rowersensors(rwr)
        rowerstats = {}
        if scullsweep == 'sweep':
            # rename IOratio?
            IOratio = inboard * outboard/(inboard+outboard)

            ind_ga = rsens['GateAngle']
            ind_fx = rsens['GateForceX']
            ind_fy = rsens['GateForceY']

            if rwr == rwcnt-1:
                ga_ind = ind_ga

            # only look in first stroke
            g_fx = signal.filtfilt(B, A, a[:, ind_fx])
            gate_fx = g_fx[:sp[1]-sp[0]]
            g_a = signal.filtfilt(B, A, a[:, ind_ga])
            gate_a = g_a[:sp[1]-sp[0]]
            if gd.filter:
                # gate force and angle of all rowers
                a[:, ind_fx] = g_fx
                a[:, ind_ga] = g_a

            # time points of
            posmin = np.argmin(gate_a)
            posmax = np.argmax(gate_a)
            fmax   = np.argmax(gate_fx)

            rowerstats['GFMax'] = np.amax(gate_fx)   # also use fy?
            # only use the stroke
            rowerstats['GFEff'] = np.mean(gate_fx[: posmax])

            """
            # gate force up/down at 70% at
            threshold = 0.7*rowerstats['GFMax']
            upat70 = np.argmax(gate_fx > threshold)
            downat70 = fmax + np.argmax(gate_fx[fmax: ] < threshold)
            rowerstats['UpAt70'] = gate_a[upat70] - gate_a[posmin]
            rowerstats['DownAt70'] = gate_a[posmax] - gate_a[downat70]
            """
            # slip: number of degrees after the turning point in the angle the force is above the threshold
            # threshold = 9.81*int(gd.globals['Parameters']['threshCatchSweep'])
            threshold = 0.4*rowerstats['GFMax']
            slippos = np.argmax(gate_fx > threshold)
            # threshold = 9.81*int(gd.globals['Parameters']['threshFinSweep'])
            # start looking at posmax/2
            washpos = fmax + np.argmax(gate_fx[fmax: ] < threshold)

            # degrees from beginning of stroke
            rowerstats['Slip'] = gate_a[slippos] - gate_a[posmin]
            if slippos < posmin:
                rowerstats['Slip'] = -rowerstats['Slip']
            # degrees wrt end of stroke
            rowerstats['Wash'] = gate_a[posmax] - gate_a[washpos]
            rowerstats['EffAngle'] = gate_a[washpos] - gate_a[slippos]

            # power
            ga_rad          = math.pi * a[:, ind_ga] / 180
            # force in forward direction:
            pinForceTS      = (np.multiply(a[:, ind_fx], np.cos(ga_rad)) -
                                      np.multiply(a[:, ind_fy], np.sin(ga_rad)))
            moment          = IOratio * pinForceTS
            # speed in radians per second:
            gateAngleVel    = np.gradient(math.pi*g_a/180, 1/Hz)               # should be gate_a!
            power = moment * gateAngleVel
            prof_data[0+rwr]   = power
            # 0 being the first, add rwcnt and 2*rwcnt to the index for the next

            # a single stroke
            rowerstats['PMax']  = np.max(power[:sp[1]-sp[0]])
            work = np.trapz(power[:sp[1]-sp[0]], dx=1/Hz)
            rowerstats['Work'] = work
            rowerstats['PMean'] = Hz*work/(sp[1]-sp[0])
            rowerstats['PperKg'] = rowerstats['PMean']/gd.sessionInfo['Rowers'][rwr][3]
            
            # catch/finish angles
            rowerstats['CatchA'] = np.min(gate_a)
            rowerstats['FinA'] = np.max(gate_a)
            rowerstats['TotalA'] = rowerstats['FinA'] - rowerstats['CatchA']

            # only for stroke rower
            if rwr == 0:
                # rhythm: stroketime/cycletime in %
                out['Rhythm'] = 100*float(posmax-posmin)/(sp[1]-sp[0])

            # TODO: PowerLegs, PowerTruncArms

            # TODO: HandleVel, HandleVDSSeat
            #        uses gateAngleVel. from data or calculate? (peachCalc does both!

        else:   # scull
            IOratio = inboard * outboard/(inboard+outboard)

            # we already added P and S together in P
            ind_gap = rsens["P GateAngle"]
            ind_fxp = rsens["P GateForceX"]
            ind_fyp = rsens["P GateForceY"]

            if rwr == rwcnt-1:
                ga_ind = ind_gap

            # only look in the first stroke
            g_fx = signal.filtfilt(B, A, a[:, ind_fxp])
            gate_fx = g_fx[:sp[1]-sp[0]]
            g_a = signal.filtfilt(B, A, a[:, ind_gap])
            gate_a = g_a[:sp[1]-sp[0]]
            if gd.filter:
                # gate force and angle of all rowers
                a[:, ind_fxp] = g_fx
                a[:, ind_gap] = g_a

            # time points of
            posmin = np.argmin(gate_a)
            posmax = np.argmax(gate_a)
            fmax   = np.argmax(gate_fx)

            rowerstats['GFMax'] = np.amax(gate_fx)
            rowerstats['GFEff'] = np.mean(gate_fx[: posmax])

            """
            # gate force up/down at 70% at
            threshold = 0.7*rowerstats['GFMax']
            upat70 = np.argmax(gate_fx > threshold)
            downat70 = fmax + np.argmax(gate_fx[fmax: ] < threshold)
            rowerstats['UpAt70'] = gate_a[upat70] - gate_a[posmin]
            rowerstats['DownAt70'] = gate_a[posmax] - gate_a[downat70]
            """
            # slip: number of degrees after the turning point in the angle the force is above the threshold
            # threshold = 9.81*int(gd.globals['Parameters']['threshCatchSweep'])
            threshold = 0.4*rowerstats['GFMax']
            slippos = np.argmax(gate_fx > threshold)
            # threshold = 9.81*int(gd.globals['Parameters']['threshFinSweep'])
            # start looking at posmax/2
            washpos = fmax + np.argmax(gate_fx[fmax: ] < threshold)

            rowerstats['Slip'] = gate_a[slippos] - gate_a[posmin]
            if slippos < posmin:
                rowerstats['Slip'] = -rowerstats['Slip']
            rowerstats['Wash'] = gate_a[posmax] - gate_a[washpos]
            rowerstats['EffAngle'] = gate_a[washpos] - gate_a[slippos]

            # power (both oars merged)
            gate_a       = signal.filtfilt(B, A, a[:, ind_gap])
            ga_rad          = math.pi * (a[:, ind_gap]) / 180
            pinForceTS   = (np.multiply(a[:, ind_fxp], np.cos(ga_rad)) -
                            np.multiply(a[:, ind_fyp], np.sin(ga_rad)))
            moment       = IOratio * pinForceTS
            gateAngleVel = np.gradient(math.pi*g_a/180, 1/Hz)                           # should be gate_a!
            power = moment * gateAngleVel
            prof_data[0+rwr]   = power
            rowerstats['PMax']  = np.max(power[:sp[1]-sp[0]])
            work = np.trapz(power[:sp[1]-sp[0]], dx=1/Hz)
            rowerstats['Work'] = Hz*work/(sp[1]-sp[0])
            rowerstats['PMean'] = Hz*work/(sp[1]-sp[0])
            rowerstats['PperKg'] = rowerstats['PMean']/gd.sessionInfo['Rowers'][rwr][3]
            
            # catch/finish angles
            rowerstats['CatchA'] = np.min(gate_a)
            rowerstats['FinA'] = np.max(gate_a)
            rowerstats['TotalA'] = rowerstats['FinA'] - rowerstats['CatchA']

            # only for stroke rower
            if rwr == 0:
                # rhythm: stroketime/cycletime in %
                out['Rhythm'] = 100*float(posmax-posmin)/(sp[1]-sp[0])

            # TODO: PowerLegs, PowerTruncArms

            # TODO: HandleVel, HandleVDSSeat

        #
        out[rwr] = rowerstats

    #
    # TODO

    # normalize data for the averaged stroke in this piece
    ll = sp[1]-sp[0]+2  # little bit longer to really complete the cycle
    # print(f"pieces = {gd.sessionInfo['Pieces']}")
    # print(f'  ll  {ll}   a.shape  {a.shape}')
    
    for i in range(a.shape[1]):
        x = np.arange(ll)
        # wry wrong when ll = 105? fill_value helps
        # print(f'=====    {x.shape}    {a[0:ll,i].shape}')
        g = interp1d(x, a[0:ll, i], kind='cubic', fill_value="extrapolate")
        xnew = np.arange(100)*((ll-1)/(100-1))
        # print(len(x), len(xnew), len(a[0:ll, i]))
        # print(f'xnew {xnew}')
        # print(a[0:ll, i])

        gd.norm_arrays[idx, :, i] = g(xnew)

    # calculate marker positions
    g_a = signal.filtfilt(B, A, gd.norm_arrays[idx, :, ga_ind])  # hadden we al uitgerekend
    gd.gmin[idx] = np.argmin(g_a)
    gd.gmax[idx] = np.argmax(g_a)

    # normalize profile_data
    profile_data = np.zeros((3*rwcnt, 100))
    l = sp[1]-sp[0]+2
    x = np.arange(l)
    for i  in range(3*rwcnt):
        g = interp1d(x, prof_data[i, 0:l], kind='cubic', fill_value="extrapolate")
        xnew = np.arange(100)*((l-1)/(100-1))
        profile_data[i, :] = g(xnew)

    return out, profile_data


def visualize(data):
    print('Profile data pictures or pdf')
