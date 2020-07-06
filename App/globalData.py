"""Global data for the app."""

#
orgname = 'RTC Noord'
orgdomain = 'RTC'
appname = 'RtcApp'

# the host operating system
# Note: a None is actually the string 'None'!
os = None
configfile = None
config = None

# data from the GlobalSettings yaml file
globals     = {}

# the primary data
# data from the session yaml file
sessionInfo = {}
# ESSENTIAL: sensors are in same order as in dataObject
dataObject  = []

# the secondary data
sessionInfo2 = {}
dataObject2  = []

# the models for:
# the sensors in setup pieces
data_model = []
# the pieces in setup pieces and view piece
data_model2 = []
# the sensors in view pieces
data_model3 = []
# the secondary sensors in view pieces
data_model4 = []
# the secondary pieces in view pieces
data_model5 = []

# for the properties
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
rowerPlots =  [None, None, None, None, None, None, None, None, None, None, None, None]
stretcherPlots =  [None, None, None, None, None, None, None, None, None, None, None, None]
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
# averaging or not
averaging = True
filter = False
custom_report = False

# the averaged data and normalized data (pieces, length, sensors)
norm_arrays = None
out = None

# mpv player
novideo = False
runningvideo = False
player = None
