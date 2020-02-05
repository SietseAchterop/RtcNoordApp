import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Crew report

Item {
    id: prcrew
    
    ColumnLayout {
	Text {
	    text: 'Profile crew report'
	}

	Tumbler {
	    id: crewtumbler
		    
	    height: 40
	    model: ['start', 't20', 't24', 't28', 't32', 'max']
	    visibleItemCount: 3
    
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
	}

	

	Text {
	    text: ''
	}
	


	// plots in the boat profile
        FigureToolbar {
            id: crewView
            objectName : "viewcrew"
                            
            Layout.fillWidth: true
            Layout.fillHeight: true
                
            Layout.minimumWidth: 1000
            Layout.minimumHeight: 400
        }
    }
}
