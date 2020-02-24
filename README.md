# RtcNoordApp

Process data from the Powerline system from Peach Innovations.
This system collects data from a rowing boat using various sensors.
The app is attempt to get higher level data out of the raw data from this system.

## Installation

It basically works on linux, windows and mac. See the docs directory for a short description of the install process on the different platforms.

## Usage

  - Start the program from the App directory with: "python main.py", or create an Icon on the desktop.
  - The very first time the program is started a system dependant configuration-file RtcApp will be created where the "BaseDir" for all rowing data is set.
    The default value of BaseDir is RtcNoord in your home-directory.
    It that directory doesn't exist, it and a number of subdirectories will be created.
    With an upgrade of the software it probably is best to remove these files before starting the new version.
  - In the lower left part of the screens there is a status message.
  - Create a csv-file from the interesting part of a session using the Powerline software, creating a single piece and export the traces.
    Then paste that in, e.g, notepad. Finally put the result with a csv file extention in the csv-data directory, or a subdirectory thereof.
  - A few csv-files are already included.
  - Start the app and select the csv-file from the menu.
    Now data is preprocessed and saved in a sessionInfo-file and a dataObject-file.
    The csv-file is not used anymore.
  - You can only use files that are in the csv- and session-data- directories.
  - You can create subdirectories in the csv-data to organize your data according to years e.g.
    There subdirectories will automatically be replicated in the session-data directory
  - There is a very basic backup mechanism if a session is created a second time. The previous session file wil be saved in a directory 'old'.
  - The program consists of several tabs that can be selected at the bottom of the screen.
      - Setup pieces: the interesting parts can be selected for further study.
      - View pieces: study the sensordata in detail, comparing with other session, ...
      - Profile tabs: if the proper pieces are selected a profile of the crew and individual rowers can be created.
          - Boat, Crew, and rower tabs.
      - Session info: configure the session, name the rowers, set calibration value
	  
## Status

   - This is a basic working version.
     The layout of the graphical elements has not been done properly, so it is sometimes difficult to see some parts of a window. This is work in progress.

## Screenshots

Here a number screenshots to give an idea.
For the moment this part is also the rudimentary user guide.
Sessions can be created or selected from the menu at the top.
Below a description of the tabs.

### Setup Pieces

This normally is the first screen to use.
It is used to select the interesting pieces from the session.
If a socalled "profile" is to be generated, a number of 6 mandatory pieces have to be selected.

We can select the different sensors by checking the sensors, here two sensors are selected.
The currently selected pieces are shown in the right part of the screen.

![Eerste](docs/SetupPieces.png)

The plot in the bottom part gives an overview of the entire rowing session, it shows the rating.
With it, the different parts of the session can be easily found.

To select pieces click on the interesting part in the lower plot.
That part is now shown above magnified, and sensordata can be shown there.
A piece is created as follows: type the name of the piece, say "t20" in the field next to the "New piece" button.
Then click that button; it will turn red.
The next two clicks in the large plot define the beginning and end of the piece respectivily.
Finally click the button again; now the piece is created and shown below the button.
The buttons next to the pieces can be used to remove a piece.
The "save sessioninfo" button saves the pieces.

If pieces with names: start, t20, t24, t28, t32, and max are created, saving the pieces will also trigger the creation of the profile.

There is some panning and zooming possible with the mouse-wheel and right button.

### View Piece

In the View Piece tab we can study the traces in more detail.
The same panning and zooming is possible here.
The next screenshot shows a number of sensors, where they are scaled in such a way that the individual graphs are more or less the same size.

![Eerste](docs/ViewPiece.png)

Using the "Secondary" button another session can be selected
In this way it is possible to view 2 different sessions next to each other to compare traces from these sessions.

Below two parts of the same session are shown one, with a stroke rate of 24 and the other with a rate of 30.
The plots are "normalized" in that they overlap even if the rates are different, this to better compare the strokes.

![Eerste](docs/ViewPiece2.png)

### Using video

The view piece screen can also be used to connect a video session to the data.
After selecting a video via the button the video appears.
The video can be controlled with the video control button, apart from the middle one.
Clicking in the plot also positions the video.

The middle video control button is used the synchronise the video with the data as follows.
First position the video to a point where the data can be found that matches that point.
E.g. the first turning point of the oars at the intake after a start.
Then click the button, it will turn red; the video time is set.
Next click on the plot on the correct point in the data.
Finally click the button again. Synchronisation is complete.

![Eerste](docs/ViewVideo.png)

### Boat Profile

When the correct 6 pieces are selected a profile is created to aid in the interpretation of the data.
The image shows this boat profile tab.

![Eerste](docs/BoatProfile.png)

A profile is created using the button, but that is normally not needed, it will be done automatically when it is possible to do so.
A profile can be created using the first stroke of each piece or using the average over each piece.
Clicking the checkbox will select that.
The data can also be filtered using the other checkbox.

The plots show the selected (averaged/filtered) stroke that is used in profiling.
The plot shows exactly one stroke starting at the point that the stroke rower has his/here oar(s) perpendicular to the boat in the recover.
Using the tumble wheel below the create profile button we can select which pieces are shown in the plots.
All pieces, the individual pieces or the average of them can be selected.

The profile consists of this screen and the Crew- and Rower- screens, so creating a new profile will also affect those screens.
The "Create report" creates a pdf version of the profile, see the docs directory for an [example report](docs/example_report.pdf)

The report uses the selected settings of checkboxes and tumble wheels.

### Crew Profile

A number of plots to compare rowers in a crew.
The tumble wheel can be used to select the piece to look at, or the average can be used

![Eerste](docs/CrewProfile.png)

### Rower Profiles

Each rower has its own profile part.
Again the tumble wheel can be used to select a single piece or the average.

![Eerste](docs/RowerView.png)

### Session Info

In this tab some parts of the session can be configured: Crew name, calibration value, venue, ..

![Eerste](docs/SessionInfo.png)


### Addition tabs

  -  X/Y plots
  -  A tab to use video separate from the rest. E.g. to easilty make a short loop in the video a a slow speed.
