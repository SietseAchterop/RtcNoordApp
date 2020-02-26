import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Crew report

Item {
    id: prcrew
    
    ScrollView {
	width: parent.width
	height: parent.height

	Column {
	    spacing: 10
	    Text {
		text: 'Profile crew report'
	    }

	    Text {
		text: ''
	    }

	    Tumbler {
		id: crewtumbler
		    
		height: 80
		model: ['start', 't20', 't24', 't28', 't32', 'max', 'average']
		visibleItemCount: 3
    
		Component.onCompleted: { crewtumbler.currentIndex = 6 }
		onCurrentIndexChanged: {
		    crew_mpl.showPiece(crewtumbler.currentIndex);
		}

		contentItem: ListView {
		    model: crewtumbler.model
		    delegate: crewtumbler.delegate
		    
		    snapMode: ListView.SnapToItem
		    highlightRangeMode: ListView.StrictlyEnforceRange
		    preferredHighlightBegin: height / 2 - (height / crewtumbler.visibleItemCount / 2)
		    preferredHighlightEnd: height / 2 + (height / crewtumbler.visibleItemCount / 2)
		    clip: true
		    opacity: 1.0 - 2* (Math.abs(Tumbler.displacement))
		}
		background: Item {
		    Rectangle {
			opacity: 0.3
			border.color: "black"
			color: "aquamarine"
			width: parent.width
			height: parent.height
		    }
		}
	    }

	    // plots in the boat profile
            FigureToolbar {
		id: crewView
		objectName : "viewcrew"
                            
		width: 1000
		height: 800
            }
	}
    }
}
    
