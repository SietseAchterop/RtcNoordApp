import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Crew report

Item {
    id: prcrew
    
	ColumnLayout {
	    anchors.fill: parent
            Layout.fillWidth: true

	    spacing: 10
	    Text {
		text: 'Profile crew report'
	    }

	    Text {
		text: ''
	    }

	    Tumbler {
		id: crewtumbler
		    
		Layout.preferredWidth: 50
		Layout.preferredHeight: 100
		model: crew_mpl.allPieces
		visibleItemCount: 1
    
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
                            
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Layout.minimumWidth: 200
                Layout.minimumHeight: 200
            }
	}
}
    
