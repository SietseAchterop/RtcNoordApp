import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12

Item {
    ColumnLayout {
	id: sessionId
	anchors.fill: parent
	spacing: 5
	
	// Data source, CrewInfo, RowerNames, Misc, Calibration, Video
	property var sinfo: ([] )
	Connections {
            target: crew_mpl
            onSessionsig: {
		sessionId.sinfo = sessig;
		crewname.placeholderText = sessig[0]
		calib.placeholderText = sessig[1]
		misc.placeholderText = sessig[2]
	    }
	}

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

	// Todo: twee rijen bij een 8
	RowLayout {
	    Repeater {
		id:sessrepeater
		model: draw_mpl.nmbrRowers
		delegate: RowLayout {
		    spacing: 10

		    TextField {
			selectByMouse: true   // is iets raars mee?
			implicitWidth: 120
			placeholderText: qsTr("Name")
		    }
		    Text {
			text: 'Rower ' + (index+1).toString()
		    }
		}
	    }
	}
	
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

	RowLayout {
	    spacing: 10

	    TextField {
		id: videoname
		selectByMouse: true   // is iets raars mee?
		implicitWidth: 120
		placeholderText: qsTr("Name")
	    }
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
