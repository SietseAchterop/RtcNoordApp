import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Boat report

Item {
    id: prboat

    function formatText(count, modeldata) {
	return modeldata
    }

    ColumnLayout {

	Text {
	    text: ' '
	}
	Row {
	    spacing:0
    
	    TableView {
		id: boatTableView
		columnWidthProvider: function (column) { if (column == 0)
                                                           return 150;
                                                         else if (column == 1)
                                                                return 100;
                                                             else return 50; }
		rowHeightProvider: function (column) { return 20; }
		model: boatTableModel
		height: 260
		width: 500  // dit moet anders...
		delegate: Rectangle {
		    // implicitWidth: 100
		    height: 50
		    color: {(index%boatTableView.rows)%2 ? 'gainsboro' : 'antiquewhite'}
		    //  tableView rows en columns gebruiken: om en om andere kleuren
		    Text {
			text: display
		    }
		}
		ScrollIndicator.horizontal: ScrollIndicator { }
		ScrollIndicator.vertical: ScrollIndicator { }
	    }

	    Column {

		Row {
		    Button {
			text: 'Create profile'
			onPressed: {
			    boatTableModel.make_profile();
			    boatTableView.forceLayout()
			}
		    }

		    Column {
			CheckBox {
			    checked: true
			    text: qsTr("Averaged")
			    onPressed: {
				boatTableModel.set_averaging(checked);
				boatTableView.forceLayout();
			    }
			}

			CheckBox {
			    checked: false
			    text: qsTr("Filtered")
			    onPressed: {
				boatTableModel.set_filter(checked);
				boatTableView.forceLayout();
			    }
			}
		    }

		    Column {
			Button {
			    text: 'Create report'
			    onPressed: {
				boatTableModel.make_report();
			    }
			}
			/*
			CheckBox {
			    checked: false
			    text: qsTr("Custom")
			    onPressed: {
				boatTableModel.set_custom(checked);
				boatTableView.forceLayout();
			    }
			}
			*/
		    }
		}
		Tumbler {
		    id: tumbler
		    
		    height: 80
		    model: ['all', 'start', 't20', 't24', 't28', 't32', 'max', 'average']
		    visibleItemCount: 3
    
		    onCurrentIndexChanged: {
			boat_mpl.showPiece(tumbler.currentIndex);
		    }

		    contentItem: ListView {
			model: tumbler.model
			delegate: tumbler.delegate
			
			snapMode: ListView.SnapToItem
			highlightRangeMode: ListView.StrictlyEnforceRange
			preferredHighlightBegin: height / 2 - (height / tumbler.visibleItemCount / 2)
			preferredHighlightEnd: height / 2 + (height / tumbler.visibleItemCount / 2)
			clip: true
			opacity: 1.0 - 2* (Math.abs(Tumbler.displacement))

			// 0.4 + Math.max(0, 1 - Math.abs(Tumbler.displacement)) * 0.6
		    }
		}
	    }
	}

	// plots in the boat profile
        FigureToolbar {
            id: boatView
            objectName : "viewboat"
                            
            Layout.fillWidth: true
            Layout.fillHeight: true
                
            Layout.minimumWidth: 1000
            Layout.minimumHeight: 600
        }
    }
}
