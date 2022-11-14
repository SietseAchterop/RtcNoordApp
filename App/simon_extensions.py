"""
RTC Noord app extensions

Description

- The purpose of this file is to do extra calculations on top of what is done in the RTCnoordapp.
- The data from the app is imported into this file, so the pieces selected in the app can be used by this algorithm.
- The output data is also written into an excel file wich is stored in the RtcNoord/reports folder under file name: 'Data Extensions [original file name]'.
- The data from the RTCNoord App is imported via 'main' and globalData. 

- At the moment three different catch and finish analyses are included in this algroritm.
- Also phase analyses as done by Cuijpers et al., 2016 is included, with measures for both continious realative phase and descrete relative phase compared to the stroke rower.


Written by Simon Coopmans, 2021

Literature:
1. Sève C, Nordez A, Poizat G, Saury J. Performance analysis in sport: contributions from a joint analysis of athletes' experience and biomechanical indicators. Scand J Med Sci Sports. 2013 Oct;23(5):576-84. 
2. Wing AM, Woodburn C. The coordination and consistency of rowers in a racing eight. J Sports Sci. 1995 Jun;13(3):187-97.
3. Hill H. Dynamics of coordination within elite rowing crews: evidence from force pattern analysis. J Sports Sci. 2002 Feb;20(2):101-17.
4. Cuijpers LS, Passos PJM, Murgia A, Hoogerheide A, Lemmink KAPM, de Poel HJ. Rocking the boat: does perfect rowing crew synchronization reduce detrimental boat movements? Scand J Med Sci Sports. 2017 Dec;27(12):1697-1704.

"""

# import necessary packages
import globalData as gd
import main
main.interactive()
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import csv
import os
from pathlib import Path
import pandas as pd
import numpy as np
import scipy.signal as signal
import time

# import data and session information
data=pd.DataFrame(gd.dataObject);
data.columns=gd.sessionInfo['uniqHeader'];
sampleTime=20;  #miliseconds
fs=1000/sampleTime; #Hz
nPieces=len(gd.sessionInfo["Pieces"][:]);
nRowers=gd.sessionInfo['RowerCnt'];
rowerNames=['R1','R2','R3','R4','R5','R6','R7','R8'];
pieceNames=[];
scullSweep=gd.sessionInfo['ScullSweep'];
columNum=0;

# prepare output
outputData=pd.DataFrame(np.zeros([18,nRowers*nPieces+1]));
outputColumns=['Var Name'];
for i in range(0,nRowers*nPieces):
    outputColumns=outputColumns+['Var ' + str(i+1)];


# prefix for variable names to only select port side for sculling, this to simplify the analyses
if scullSweep=='scull':
    scullAdd='P ';
else :
    scullAdd='';

# butterworth Filter definition
def butterworthFilter(order,cutOffFr,data):
    orderBut=order; # order of butterworth filter
    fc=cutOffFr; #cut off frequency
    [b, a] = signal.butter(orderBut, 2*fc/fs, btype='low');
    filterdData = signal.filtfilt(b, a, data);
    return filterdData

# angle derivative definition
def angleToAngularVelocity(k,ts,angleData): # k, sample Time (seconds), input angle data
    angVel = np.empty(len(angleData), dtype=float);
    angVel.fill(np.nan);
    for i in range(k,len(angleData)-k):
        angVel[i] = (angleData.iloc[i+k]-angleData.iloc[i-k]) / (2*k*ts);
    return angVel

def timeToStringFormat(inputTime):
    timeArray=np.zeros(len(inputTime))
    timeArray=list(timeArray)
    for i,t in enumerate(inputTime) :
        timeArray[i]=time.strftime ('%H:%M:%S.%f', time.gmtime(t)) # milliseconds are not working with this function
    return timeArray

data['Time']=data['Time']/1000;
data['TimeString']=timeToStringFormat(data['Time']);

# Loop over number of pieces
for iPiece in range(0,nPieces):
    [
        namePiece,        # name of piece given in RtcNoord App
        startEndPoint,    # unit 20 milliseconden, number of 1/50 secondes from  start session
        nStrokeAVG,       # number of strokes in piece and average tempo of piece
        startStrokes      # list of start times of the strokes
        ] = gd.sessionInfo["Pieces"][iPiece];

    pieceNames=pieceNames+[str(namePiece)];
    
    #Preallocating variables
    catchIndex1=np.zeros([len(startStrokes)-1,nRowers]);
    catchIndex2=np.zeros([len(startStrokes)-1,nRowers]);
    catchIndex3=np.zeros([len(startStrokes)-1,nRowers]);
    finishIndex1=np.zeros([len(startStrokes)-1,nRowers]);
    finishIndex2=np.zeros([len(startStrokes)-1,nRowers]);
    finishIndex3=np.zeros([len(startStrokes)-1,nRowers]);
    strokeDuration1=np.zeros([len(startStrokes)-1,nRowers]);
    strokeDuration2=np.zeros([len(startStrokes)-1,nRowers]);
    strokeDuration3=np.zeros([len(startStrokes)-1,nRowers]);
    strokeDurationDiff1=np.zeros([len(startStrokes)-1,nRowers]);
    strokeDurationDiff2=np.zeros([len(startStrokes)-1,nRowers]);
    strokeDurationDiff3=np.zeros([len(startStrokes)-1,nRowers]);
    catchTimeDiff1=np.zeros([len(startStrokes)-1,nRowers]);
    catchTimeDiff2=np.zeros([len(startStrokes)-1,nRowers]);
    catchTimeDiff3=np.zeros([len(startStrokes)-1,nRowers]);
    finishTimeDiff1=np.zeros([len(startStrokes)-1,nRowers]);
    finishTimeDiff2=np.zeros([len(startStrokes)-1,nRowers]);
    finishTimeDiff3=np.zeros([len(startStrokes)-1,nRowers]);
    rowerCatchTime=np.zeros([len(startStrokes)-1,nRowers]);
    strokeRowerCatch=np.zeros([len(startStrokes)-1,1]);
    relativeStrokeTime=np.zeros([len(startStrokes)-1,1]);
    PEcatch=np.zeros([len(startStrokes)-2,nRowers]);
    PEfinish=np.zeros([len(startStrokes)-2,nRowers]);

    # loop over number of rowers
    for rower in range(0,nRowers):
        for stroke in range(0,len(startStrokes)-1):
            strokeAngleData=data[scullAdd + 'GateAngle '+str(rower+1)][startStrokes[stroke]:startStrokes[stroke+1]];
            strokeForceData=data[scullAdd + 'GateForceX '+str(rower+1)][startStrokes[stroke]:startStrokes[stroke+1]];

            #Seve et al., 2013 method: catch and finish time at minimal/maximal angle.
            minOfStroke=min(strokeAngleData);
            maxOfStroke=max(strokeAngleData);
            catchIndex1[stroke,rower] = startStrokes[stroke]+np.where(strokeAngleData == minOfStroke)[0][0];    #index of data point in dataset marking the catch
            finishIndex1[stroke,rower] = startStrokes[stroke]+np.where(strokeAngleData == maxOfStroke)[0][0];   #index of data point in dataset marking the finish
            
            # Wing and Woodburn, 1995 method: catch time at force > 15 kilo for more than 100ms, finish Time at minimum force.
            period = 100;
            thresholdForce =15;
            for idp in range(0,len(strokeForceData)-int(period/sampleTime)):
                if strokeForceData.iloc[idp] >= thresholdForce and min(strokeForceData.iloc[idp:int(idp+period/sampleTime)]) >= thresholdForce:
                    ic=idp;
                    break
            catchIndex2[stroke,rower] = startStrokes[stroke]+ic;    #index of data point in dataset marking the catch
            minForce=min(strokeForceData);
            finishIndex2[stroke,rower] = startStrokes[stroke]+np.where(strokeForceData == minForce)[0][0];  #index of data point in dataset marking the finish

            # Hill, 2002 method: catch and finish time at the point extrapolated to baseline from the steepest slope in time-force curve.
                #Steepest (positive) slope in time-force curve before reaching 50% of peak force for catch, and steepest (negative) slope after dropping lower than 30% of peak force for finish.
            strokeForceDataFilt=np.zeros(len(strokeForceData));
            strokeForceDataDelta=np.zeros(len(strokeForceData));
            maxDelta=0;
            minDelta=0;
            for idpFilt in range(2,len(strokeForceDataFilt)-2):
                strokeForceDataFilt[idpFilt]=np.mean(strokeForceData[idpFilt-2:idpFilt+3]); # five step movering average filter
                if idpFilt>2:
                    strokeForceDataDelta[idpFilt]=strokeForceDataFilt[idpFilt]-strokeForceDataFilt[idpFilt-1];
                    if strokeForceDataDelta[idpFilt] > maxDelta and strokeForceDataDelta[idpFilt] <= 0.5*np.max(strokeForceData):
                        maxDelta=strokeForceDataDelta[idpFilt];
                    elif strokeForceDataDelta[idpFilt] < minDelta and strokeForceDataDelta[idpFilt] <= 0.3*np.max(strokeForceData):
                        minDelta = strokeForceDataDelta[idpFilt];
            tAtMaxDelta = np.where(strokeForceDataDelta==maxDelta)[0][0];
            tAtMinDelta = np.where(strokeForceDataDelta==minDelta)[0][0];
            dataPointsBackToGetToZeroFromMax = int(round(strokeForceDataFilt[np.where(strokeForceDataDelta==maxDelta)[0][0]]/maxDelta));  # tangent of slope extrapolating to 0
            dataPointsBackToGetToZeroFromMin = int(round(strokeForceDataFilt[np.where(strokeForceDataDelta==minDelta)[0][0]]/minDelta));  # tangent of slope extrapolating to 0
            catchIndex3[stroke,rower] = startStrokes[stroke] + tAtMaxDelta - dataPointsBackToGetToZeroFromMax;  #index of data point in dataset marking the catch
            finishIndex3[stroke,rower] = startStrokes[stroke] + tAtMinDelta - dataPointsBackToGetToZeroFromMin; #index of data point in dataset marking the finish

        if nRowers>=2:
            strokeDuration1[:,rower] = (finishIndex1[:,rower] - catchIndex1[:,rower]) * sampleTime;
            strokeDuration2[:,rower] = (finishIndex2[:,rower] - catchIndex2[:,rower]) * sampleTime;
            strokeDuration3[:,rower] = (finishIndex3[:,rower] - catchIndex3[:,rower]) * sampleTime;
            strokeDurationDiff1[:,rower]=strokeDuration1[:,rower]-strokeDuration1[:,0];
            strokeDurationDiff2[:,rower]=strokeDuration2[:,rower]-strokeDuration2[:,0];
            strokeDurationDiff3[:,rower]=strokeDuration3[:,rower]-strokeDuration3[:,0];
        
            catchTimeDiff1[:,rower] = (catchIndex1[:,rower] - catchIndex1[:,0]) * sampleTime;
            catchTimeDiff2[:,rower] = (catchIndex2[:,rower] - catchIndex2[:,0]) * sampleTime;
            catchTimeDiff3[:,rower] = (catchIndex3[:,rower] - catchIndex3[:,0]) * sampleTime;
        
            finishTimeDiff1[:,rower] = (finishIndex1[:,rower] - finishIndex1[:,0]) * sampleTime;
            finishTimeDiff2[:,rower] = (finishIndex2[:,rower] - finishIndex2[:,0]) * sampleTime;
            finishTimeDiff3[:,rower] = (finishIndex3[:,rower] - finishIndex3[:,0]) * sampleTime;

            #Point estimates of relative Phase, as in Cuijpers et al., 2017.
            PEcatch[:,rower]  = (catchIndex1[0:-1,rower] - catchIndex1[0:-1,0]) / (np.delete(catchIndex1[:,rower],0) - catchIndex1[0:-1,rower]) * 360;      # (tCatch2-tCatch1)/(duration catch tot catch rower 2)*360deg
            PEfinish[:,rower] = (finishIndex1[0:-1,rower] - finishIndex1[0:-1,0]) / (np.delete(finishIndex1[:,rower],0) - finishIndex1[0:-1,rower]) * 360;  # same but with finish
    

    oarAngleDataFilt=pd.DataFrame();
    phase=pd.DataFrame();
    relativePhase=pd.DataFrame();
    oarAngleDataFilt['Time']=data['Time'][startEndPoint[0]:startEndPoint[1]];
    fn=np.zeros([startEndPoint[1]-startEndPoint[0],nRowers]);
    fn=fn+9999;
    
    # loop over rowers
    for rower in range(0,nRowers):
        columNum=columNum+1;
        outputColumns[columNum]=namePiece + ' R' + str(rower+1)
        
        # Filter and intergrate angle to anglar velocity 
        oarAngleDataFilt['GateAngle '+str(rower+1)] = butterworthFilter(2,4,data[scullAdd + 'GateAngle ' + str(rower+1)][startEndPoint[0]:startEndPoint[1]]+90); # filter and add 90 degrees
        oarAngleDataFilt['GateAngVel '+str(rower+1)] = angleToAngularVelocity(1, sampleTime/1000, oarAngleDataFilt ['GateAngle ' + str(rower+1)]);

        #calculate phase
        ph=oarAngleDataFilt['Time'];
        ph[:]=0;

        #loop over data strokes to calculate the normalisation factor calculation, this is de pi/(halve a period). As done in Varlet and Richardson 2011 and Cuijpers et al., 2017
        fn[0 : int( catchIndex1[0,rower]-startEndPoint[0] )] = np.pi / ( ( catchIndex1[0,rower] - startEndPoint[0] ) * sampleTime/1000 );    #data untill first catch
        for i in range(0,len(catchIndex1)):
            fn[ int( catchIndex1[i,rower] - startEndPoint[0] ) : int( finishIndex1[i,rower] - startEndPoint[0] ) ,rower] = np.pi / ( ( finishIndex1[i,rower] - catchIndex1[i,rower] ) * sampleTime/1000 );    #stroke
            if i<len(catchIndex1)-1:
                fn[ int( finishIndex1[i,rower] - startEndPoint[0] ) : int( catchIndex1[i+1,rower] - startEndPoint[0] ) ,rower] = np.pi / ( (catchIndex1[i+1,rower] - finishIndex1[i,rower] ) * sampleTime/1000 );    #recovery
        fn[ int( finishIndex1[-1,rower] - startEndPoint[0] ) : startEndPoint[1]  - startEndPoint[0] ,rower] = np.pi / ( ( startEndPoint[1] - finishIndex1[-1,rower] ) * sampleTime/1000 );    #data after last finish
                       
        #calculate phase and relative phase as in Cuijpers et al., 2017.
        phase['phase '+str(rower+1)] = np.arctan( ( oarAngleDataFilt['GateAngVel '+str(rower+1)].loc[startEndPoint[0]:startEndPoint[1]] / fn[:,rower] )  / oarAngleDataFilt['GateAngle '+str(rower+1)].loc[startEndPoint[0]:startEndPoint[1]]) / np.pi*180;
        relativePhase['CRF '+str(rower+1)] = phase['phase '+str(rower+1)] - phase['phase 1'];

        #output data
        outputData.iloc[0,0]=['MAE_CRF'];
        outputData.iloc[0,iPiece*nRowers+rower+1]=np.mean(np.absolute(relativePhase['CRF '+str(rower+1)]));
        outputData.iloc[1,0]=['MAE_dt_ca_Amin'];
        outputData.iloc[1,iPiece*nRowers+rower+1]=np.mean(np.absolute(catchTimeDiff1[:,rower]));
        outputData.iloc[2,0]=['MAE_dt_fi_Amax'];
        outputData.iloc[2,iPiece*nRowers+rower+1]=np.mean(np.absolute(finishTimeDiff1[:,rower]));
        outputData.iloc[3,0]=['MAE_dt_ca_F15N'];
        outputData.iloc[3,iPiece*nRowers+rower+1]=np.mean(np.absolute(catchTimeDiff2[:,rower]));
        outputData.iloc[4,0]=['MAE_dt_fi_Fmin'];
        outputData.iloc[4,iPiece*nRowers+rower+1]=np.mean(np.absolute(finishTimeDiff2[:,rower]));
        outputData.iloc[5,0]=['MAE_dt_ca_slopeMax'];
        outputData.iloc[5,iPiece*nRowers+rower+1]=np.mean(np.absolute(catchTimeDiff3[:,rower]));
        outputData.iloc[6,0]=['MAE_dt_fi_SlopeMin'];
        outputData.iloc[6,iPiece*nRowers+rower+1]=np.mean(np.absolute(finishTimeDiff3[:,rower]));
        outputData.iloc[7,0]=['MEA_PE_DRF_catch'];
        outputData.iloc[7,iPiece*nRowers+rower+1]=np.mean(np.absolute(PEcatch[:,rower]));
        outputData.iloc[8,0]=['MEA_PE_DRF_finish'];
        outputData.iloc[8,iPiece*nRowers+rower+1]=np.mean(np.absolute(PEfinish[:,rower]));
        outputData.iloc[9,0]=['STD_CRF'];
        outputData.iloc[9,iPiece*nRowers+rower+1]=np.std(relativePhase['CRF '+str(rower+1)]);
        outputData.iloc[10,0]=['STD_dt_catch'];
        outputData.iloc[10,iPiece*nRowers+rower+1]=np.std(catchTimeDiff1[:,rower]);
        outputData.iloc[11,0]=['STD_dt_finish'];
        outputData.iloc[11,iPiece*nRowers+rower+1]=np.std(finishTimeDiff1[:,rower]);
        outputData.iloc[12,0]=['STD_dt_ca_F15N'];
        outputData.iloc[12,iPiece*nRowers+rower+1]=np.std(catchTimeDiff2[:,rower]);
        outputData.iloc[13,0]=['STD_dt_fi_Fmin'];
        outputData.iloc[13,iPiece*nRowers+rower+1]=np.std(finishTimeDiff2[:,rower]);
        outputData.iloc[14,0]=['STD_dt_ca_slopeMax'];
        outputData.iloc[14,iPiece*nRowers+rower+1]=np.std(catchTimeDiff3[:,rower]);
        outputData.iloc[15,0]=['STD_dt_fi_slopeMin'];
        outputData.iloc[15,iPiece*nRowers+rower+1]=np.std(finishTimeDiff3[:,rower]);
        outputData.iloc[16,0]=['STD_PE_DRF_catch'];
        outputData.iloc[16,iPiece*nRowers+rower+1]=np.std(PEcatch[:,rower]);
        outputData.iloc[17,0]=['STD_PE_DRF_finish'];
        outputData.iloc[17,iPiece*nRowers+rower+1]=np.std(PEfinish[:,rower]);
        outputData.columns=outputColumns;

    #Phase and relative phase of entire piece
    if nRowers >=2:
        fig, axs = plt.subplots(2)
        axs[0].plot(data['Time'][startEndPoint[0]:startEndPoint[1]],phase.loc[startEndPoint[0]:startEndPoint[1]])
        axs[0].set_title('Phase, piece = ' + namePiece)
        axs[0].legend(rowerNames[0:nRowers]);
        axs[0].set_xlabel('Time (s)')
        axs[0].set_ylabel('Phase (deg)')
        axs[1].plot(data['Time'][startEndPoint[0]:startEndPoint[1]],relativePhase.loc[startEndPoint[0]:startEndPoint[1]])
        axs[1].set_title('Relative phase, piece = ' + namePiece)
        axs[1].legend(rowerNames[0:nRowers]);
        axs[1].set_xlabel('Time (s)')
        axs[1].set_ylabel('Phase (deg)')
        plt.suptitle('Phase and continuous relative phase of the rowers compared to the stroke rower (R1)')
        plt.show()


        #Phase and relative phase of the last strokes of the piece
        numOfStrokesInPlot=6;
        startPlot=gd.sessionInfo["Pieces"][iPiece][3][-numOfStrokesInPlot];
        endPlot=gd.sessionInfo["Pieces"][iPiece][3][-1];

        fig, axs = plt.subplots(2)
        axs[0].plot(data['Time'].loc[startPlot:endPlot],phase.loc[startPlot:endPlot])
        axs[0].set_title('Phase, piece = ' + namePiece)
        axs[0].legend(rowerNames[0:nRowers]);
        axs[0].set_xlabel('Time (s)')
        axs[0].set_ylabel('Phase (deg)')
        axs[1].plot(data['Time'].loc[startPlot:endPlot],relativePhase.loc[startPlot:endPlot])
        axs[1].set_title('Relative phase, piece = ' + namePiece)
        axs[1].legend(rowerNames[0:nRowers]);
        axs[1].set_xlabel('Time (s)')
        axs[1].set_ylabel('Phase (deg)')
        plt.suptitle('Phase and continuous relative phase of the rowers compared to the stroke rower (R1)')
        plt.show()


# output output data
reportLocation=str(Path.home()) + '/RtcNoord' + '/reports/';
currentSession=gd.config['Session'];
fileName=str('Data Extensions ' + currentSession + '.xlsx');
outputData.columns=outputColumns;
outputData.to_excel(reportLocation+fileName); # output to excel

# Plot Mean absolote error and standard deviation of continuous relative phase compared between stroke rower (R1) and others over multiple pieces.
if nRowers==2:
    fig, axs = plt.subplots(1,2);
    for p in range(0,nRowers):
        columnsForGraph=[x + ' R'+str(p+1) for x in pieceNames];
        axs[p].plot(pieceNames,outputData[columnsForGraph].iloc[0,:],marker="o")
        axs[p].plot(pieceNames,outputData[columnsForGraph].iloc[9,:],marker="o")
        axs[p].set_title('R' + str(p+1))
        axs[p].legend(['MAE_CRF','STD_CRF'])
        axs[p].set_xlabel('Piece Name')
        axs[p].set_ylabel('Value')
    plt.suptitle('Mean absolote error and standard deviation of continuous relative phase compared between stroke rower (R1) and others over multiple pieces')
    plt.show()
if nRowers>2:
    if nRowers>2 and nRowers<=4:
        fig, axs = plt.subplots(2,2);
        cut=2;
    if nRowers>4 and nRowers<=6:
        fig, axs = plt.subplots(2,3);
        cut=3;
    if nRowers>6 and nRowers<=8:
        fig, axs = plt.subplots(2,4);
        cut=4;
    for p in range(0,nRowers):
        columnsForGraph=[x + ' R'+str(p+1) for x in pieceNames];
        if p <= cut-1:
            axs[0,p].plot(pieceNames,outputData[columnsForGraph].iloc[0,:])
            axs[0,p].plot(pieceNames,outputData[columnsForGraph].iloc[9,:])
            axs[0,p].set_title('R' + str(p+1))
            axs[0,p].legend(['MAE_CRF','STD_CRF'])
            axs[0,p].set_xlabel('Piece name')
            axs[0,p].set_ylabel('Value of statistic')
        if p > cut-1:
            axs[1,p-cut].plot(pieceNames,outputData[columnsForGraph].iloc[0,:])
            axs[1,p-cut].plot(pieceNames,outputData[columnsForGraph].iloc[9,:])
            axs[1,p-cut].set_title('R' + str(p+1))
            axs[1,p-cut].legend(['MAE_CRF','SD_CRF'])
            axs[1,p-cut].set_xlabel('Piece Name')
            axs[1,p-cut].set_ylabel('Value of statistic')
    plt.suptitle('Mean absolote error and standard deviation of continuous relative phase compared between stroke rower (R1) and others over multiple pieces')
    plt.show()



   
