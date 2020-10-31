#!/bin/sh
# script to start the RtcNoord App from the desktop on a Mac.
#   should be called RtcNoord.command
#   should have execution permission:   chmod a+x RtcNoord.command

# assuming that is where the app resides 
python3 ~/RtcNoordApp/App/main.py

# Can be started in the Finder
# Change the associated icon:
#    - select and open an image
#    - copy it using <command> + a   and <command> + c
#    - open the info window of the current icon of the app: <command> + i
#    - select the icon in the left top corner and paste the new image, <command> + v

