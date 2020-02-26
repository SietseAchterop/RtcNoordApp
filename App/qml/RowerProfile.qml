import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import Backend 1.0

// Profile Rower report

Item {
    id: roweritem
    
    property int rindex: 0

	function modelname (i) {
	// Kan dit niet eleganter?
	switch (i) {
	case 0: return rowerTableModel0;
	    break;
	case 1:	return  rowerTableModel1
	    break;
	case 2: return rowerTableModel2;
	    break;
	case 3:	return  rowerTableModel3
	    break;
	case 4: return rowerTableModel4;
	    break;
	case 5:	return  rowerTableModel5
	    break;
	case 6: return rowerTableModel6;
	    break;
	case 7:	return  rowerTableModel7
	    break;
	}
    }

    ScrollView {
	width: parent.width
	height: parent.height

    Column {

	Row {
	    spacing: 20
	    objectName: 'rrow'
	    TableView {
		id: rowerTableView
		columnWidthProvider: function (column) { if (column == 0)
							   return 180;
							 else if (column == 1)
							         return 70;
   							 else if (column == 2)
							         return 80;
   						              else
							         return 50;}
		rowHeightProvider: function (column) { return 20; }
		model : modelname(rindex)  // this doesn't seem to work here:  'rowerTableModel' + roweritem.rindex
		height: 460
		width: 650  // dit moet anders...
		delegate: Rectangle {
		    // implicitWidth: 100
		    height: 50
		    color: {(index%rowerTableView.rows)%2 ? 'gainsboro' : 'aquamarine'}
		    //  tableView rows en columns gebruiken: om en om andere kleuren
		    Text {
			text: display
		    }
		}
		ScrollIndicator.horizontal: ScrollIndicator { }
		ScrollIndicator.vertical: ScrollIndicator { }
	    }

	    Column {
		spacing: 10
		Text {
		    text: ' '
		    height: 280
		}
		Tumbler {
		    id: rowertumbler
		    
		    height: 80
		    model: ['all', 'start', 't20', 't24', 't28', 't32', 'max', 'average']
		    visibleItemCount: 3
    
		    Component.onCompleted: { rowertumbler.currentIndex = 7 }
		    onCurrentIndexChanged: {
			// ugly
			switch (roweritem.rindex) {
			case 0:
			    rower_mpl0.showPiece(rowertumbler.currentIndex);
			    break;
			case 1:
			    rower_mpl1.showPiece(rowertumbler.currentIndex);
			    break;
			case 2:
			    rower_mpl2.showPiece(rowertumbler.currentIndex);
			    break;
			case 3:
			    rower_mpl3.showPiece(rowertumbler.currentIndex);
			    break;
			case 4:
			    rower_mpl4.showPiece(rowertumbler.currentIndex);
			    break;
			case 5:
			    rower_mpl5.showPiece(rowertumbler.currentIndex);
			    break;
			case 6:
			    rower_mpl6.showPiece(rowertumbler.currentIndex);
			    break;
			case 7:
			    rower_mpl7.showPiece(rowertumbler.currentIndex);
			    break;
			default:
			    break;
			}
		    }

		    contentItem: ListView {
			model: rowertumbler.model
			delegate: rowertumbler.delegate
			
			snapMode: ListView.SnapToItem
			highlightRangeMode: ListView.StrictlyEnforceRange
			preferredHighlightBegin: height / 2 - (height / rowertumbler.visibleItemCount / 2)
			preferredHighlightEnd: height / 2 + (height / rowertumbler.visibleItemCount / 2)
			clip: true
			opacity: 1.0 - 2* (Math.abs(Tumbler.displacement))

			// 0.4 + Math.max(0, 1 - Math.abs(Tumbler.displacement)) * 0.6
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



	    }
	}

	// plots in the rower profile
        FigureToolbar {
            id: rowerView
            objectName : 'viewrower' + roweritem.rindex
	    Component.onCompleted: {
		draw_mpl.rowerprofile(rowerView.qmlGetFigure, rindex)
	    }
                            
	    /*
            Layout.fillWidth: true
            Layout.fillHeight: true
                
            Layout.minimumWidth: 1000
            Layout.minimumHeight: 600
	    */
	    width: 1000
	    height: 600
        }
    }
    }
}
