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
	anchors.fill: parent
        Layout.fillWidth: true


	RowLayout {
    
	    TableView {
		id: boatTableView
		model: boatTableModel
		height: 220
		//width: 600  // dit moet anders... (groot genoeg voor het aantal pieces)
		Layout.fillWidth: true
		Layout.preferredWidth: 600
		delegate: Rectangle {
		    implicitWidth: if (index == 0) return 180; else return 70;
		    implicitHeight: 20
		    height: 50
		    color: {(index%boatTableView.rows)%2 ? 'gainsboro' : 'aquamarine'}
		    //  tableView rows en columns gebruiken: om en om andere kleuren
		    Text {
			text: display
		    }
		}
		ScrollIndicator.horizontal: ScrollIndicator { }
		ScrollIndicator.vertical: ScrollIndicator { }
	    }

	    Column {
		Layout.fillWidth: true

			CheckBox {
			    // Also set averaging in globalData to the same value!
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

	RowLayout {
	    
	    Tumbler {
		id: tumbler
		    
		Layout.preferredWidth: 50
		Layout.preferredHeight: 200
		model: boat_mpl.allPieces
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

		}
		background: Item {
		    Rectangle {
			opacity: 0.8
			border.color: "black"
			color: "aquamarine"
			width: parent.width
			height: parent.height
		    }
		}
	    }

	    // plots in the boat profile
            FigureToolbar {
		id: boatView
		objectName : "viewboat"
                
		Layout.fillWidth: true
		Layout.fillHeight: true
                
		Layout.minimumWidth: 200
		Layout.minimumHeight: 200
            }
	}
    }
}

