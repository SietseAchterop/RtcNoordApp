"""Global data for the Rtc app.
"""

#
orgname = 'RTC Noord'
orgdomain = 'RTC'
appname = 'RtcApp'

# the host operating system
# Note: a None is actually the string 'None'!
os = None
configfile = None
config = None

# csv dialect
dialect = None
# data from the configs/GlobalSettings.yaml file
globals     = {}

# the primary data used throughout the app.
# this data will be read/saved from/to the yaml file in the session_data directory
sessionInfo = {}
# metadata from the csv-file
metaData = {}

# will hold data from the clipboard
clipdata = None
delimiter = None

# dataObject contains the data from the csv-file
# ESSENTIAL: sensors are in same order as in dataObject
dataObject  = []

# Data of the secondary session
metaData2    = {}
sessionInfo2 = {}
dataObject2  = []

# the models for:
#   sensors in setup pieces
data_model = []
#   pieces in setup pieces and view piece
data_model2 = []
#   sensors in view pieces
data_model3 = []
#   secondary sensors in view pieces
data_model4 = []
#   secondary pieces in view pieces
data_model5 = []

# for the QML properties
context = None

# for the plots
win = None
aantal = 0

# Boat
boattablemodel = []
boatPlots = None
boatPiece = 0

# Crew piece used in report
#   moet anders
crewPiece = 6

# Rowers: models and plots, up to twelve pieces
rowertablemodel = [None, None, None, None, None, None, None, None, None, None, None, None]
rowerPlots = [None, None, None, None, None, None, None, None, None, None, None, None]
stretcherPlots = [None, None, None, None, None, None, None, None, None, None, None, None]
rowerPiece = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]

#
# list of piece names from 'Pieces'
p_names = []

mainPieces = None
mainView = None

# calibration value for speed and distance
cal_value = None
cal_value2 = None

# profile available?
profile_available = False
# averaging or not (set also in Boatprofile.qml)
averaging = True
filter = False
custom_report = False

# the averaged data and normalized data (pieces, length, sensors)
"""
out will be the result of the profile function
  It contains a list of piececalculations which contains tuple containing
    1 dictionary containing
        PieceName
        Speedimp
        Split
        DistancePerStroke
        StartingPoints
        MaxAtP
        MinAtP
        YawMax
        RowMax
        PowerLoss
        Rythmn
        0
        1
        ..
          Containing rowerstats for each rower, again a dictionary
             GFMax
             Slip
             Wash
             EffAngle
             GFEff
             PMax
             Work
             Pmean
             PperKg
             Name
             CatchA
             FinA
             TotalA
     2 a 2 dimentional array of shape 3,100 containing in the second dimention
            power
              ...
              ...

"""
out = None

"""

"""
norm_arrays = None


# minimum and maximum of gate angle of the stroke, for markers
# calculated for each piece
gmin = []
gmax = []

# custom plot from View piece
extraplot = False
# data for custom plot
#   [ start, end, scaled, sensorlist, secondlist   ]
extrasettings = []

# buffers for View piece and custom plot
view_tr = None
view_tr2 = None

# mpv player
novideo = False
runningvideo = False
player = None
