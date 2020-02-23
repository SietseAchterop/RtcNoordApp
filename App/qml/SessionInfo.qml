import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12

Item {
    RowLayout {
	id: sessionId
	anchors.fill: parent
	spacing: 5

	// Data source, CrewInfo, RowerNames, Misc, Calibration, Video
	property var sinfo: ([] )
	property var rowers: ([] )
	property var video: ([] )
	Connections {
            target: crew_mpl
            onSessionsig: {
		sessionId.sinfo = sessig;
		crewname.placeholderText = sessig[0];
		calib.placeholderText = sessig[1];
		misc.placeholderText = sessig[2];
		sessionId.rowers = sessig[3];
		
		sessionId.video = sessig[4];
		videoname.placeholderText = sessionId.video[0];
	    }
	}

	ColumnLayout {

	    RowLayout {
		spacing: 10

		TextField {
		    id: crewname
		    selectByMouse: true   // is iets raars mee?
		    implicitWidth: 120
		    onAccepted: {
			sessionId.sinfo[0] = text;
			crew_mpl.newsesinfo(sessionId.sinfo)
		    }
		}
		Text {
		    text: 'Crew name'
		}
	    }

	    ColumnLayout {
		Repeater {
		    id:sessrepeater
		    model: draw_mpl.nmbrRowers
		    delegate: RowLayout {
			spacing: 10
			
			RowLayout {
			    TextField {
				selectByMouse: true   // is iets raars mee?
				implicitWidth: 120
				placeholderText: { sessionId.rowers[index][0] }
				onAccepted: {
				    sessionId.rowers[index] = [ text, sessionId.rowers[index][1], sessionId.rowers[index][2], sessionId.rowers[index][3]];
				    sessionId.sinfo[3][index] = sessionId.rowers[index];
				    crew_mpl.newsesinfo(sessionId.sinfo)
				}
			    }
			    TextField {
				selectByMouse: true   // is iets raars mee?
				implicitWidth: 60
				placeholderText: { sessionId.rowers[index][2] }
				onAccepted: {
				    sessionId.rowers[index] = [ sessionId.rowers[index][0], sessionId.rowers[index][1], parseInt(text), sessionId.rowers[index][3]];
				    sessionId.sinfo[3][index] = sessionId.rowers[index];
				    crew_mpl.newsesinfo(sessionId.sinfo)
				}
			    }
			    TextField {
				selectByMouse: true   // is iets raars mee?
				implicitWidth: 60
				placeholderText: { sessionId.rowers[index][3] }
				onAccepted: {
				    sessionId.rowers[index] = [ sessionId.rowers[index][0], sessionId.rowers[index][1], sessionId.rowers[index][2], parseInt(text)];
				    sessionId.sinfo[3][index] = sessionId.rowers[index];
				    crew_mpl.newsesinfo(sessionId.sinfo)
				}
			    }
			    Text {
				text: 'Rower ' + (index+1).toString()
			    }
			}
		    }
		}
	    }

	    RowLayout {
		spacing: 10

		TextField {
		    id: misc
		    selectByMouse: true   // is iets raars mee?
		    implicitWidth: 300
		    placeholderText: qsTr("Name")
		    onAccepted: {
			sessionId.sinfo[2] = text;
			crew_mpl.newsesinfo(sessionId.sinfo)
		    }
		}
		Text {
		    text: 'Misc'
		}
	    }

	}

	ColumnLayout {

	    RowLayout {
		spacing: 10

		TextField {
		    id: calib
		    selectByMouse: true   // is iets raars mee?
		    implicitWidth: 120
		    inputMethodHints: Qt.ImhFormattedNumbersOnly
		    onAccepted: {
			sessionId.sinfo[1] = text;
			crew_mpl.newsesinfo(sessionId.sinfo)
		    }
		}
		Text {
		    text: 'Calibration value'
		}
	    }

	    RowLayout {
		spacing: 10

		TextField {
		    id: videoname
		    selectByMouse: true   // is iets raars mee?
		    implicitWidth: 120
		    placeholderText: qsTr("Name")
		    onAccepted: {
			sessionId.sinfo[4][0] = text;
			crew_mpl.newsesinfo(sessionId.sinfo)
		    }
		}
		// veldje  piece er nog bij
		Text {
		    text: 'Video Info'
		}
	    }

	    RowLayout {
		spacing: 10

		TextField {
		    id: sourcename
		    selectByMouse: true   // is iets raars mee?
		    implicitWidth: 120
		    placeholderText: qsTr("Name")
		}
		Text {
		    text: 'Data source (powerline)'
		}
	    }
	}
    }
}
