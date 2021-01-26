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
	case 1:	return rowerTableModel1
	    break;
	case 2: return rowerTableModel2;
	    break;
	case 3:	return rowerTableModel3
	    break;
	case 4: return rowerTableModel4;
	    break;
	case 5:	return rowerTableModel5
	    break;
	case 6: return rowerTableModel6;
	    break;
	case 7:	return rowerTableModel7
	    break;
	}
    }

    ColumnLayout {
	    anchors.fill: parent
            Layout.fillWidth: true

	Text {
	    text: 'Rower: ' + rower_mpl0.rowerData[rindex][0] 
	    height: 50
	}

	RowLayout {
	    objectName: 'rrow'
	    TableView {
		id: rowerTableView
		model : modelname(rindex)  // this doesn't seem to work here:  'rowerTableModel' + roweritem.rindex

		Layout.fillWidth: true
		Layout.fillHeight: true
                
		Layout.minimumWidth: 200
		Layout.minimumHeight: 200

		delegate: Rectangle {
		    implicitHeight: 20
		    implicitWidth: if (index == 0) return 180; else return 65;
		    //height: 50
		    color: {(index%rowerTableView.rows)%2 ? 'gainsboro' : 'aquamarine'}
		    //  tableView rows en columns gebruiken: om en om andere kleuren
		    Text {
			text: display
		    }
		}

	    }

	    // plots in the rower profile
            FigureToolbar {
		id: stretcherView
		objectName : 'stretcher' // + roweritem.rindex
		Component.onCompleted: {
		    draw_mpl.stretcherprofile(stretcherView.qmlGetFigure, rindex)
		}
                            
		Layout.fillWidth: true
		Layout.fillHeight: true
                
		Layout.minimumWidth: 120
		Layout.minimumHeight: 120
            }

	}

	RowLayout {

	    ColumnLayout {
		spacing: 10
		
		Text {
		    text: ''
		    height: 10
		}
		Tumbler {
		    id: rowertumbler
		    
		    height: 80
		    model: boat_mpl.allPieces
		    visibleItemCount: 1
    
		    Component.onCompleted: { rowertumbler.currentIndex = 1 }
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


	    // plots in the rower profile
            FigureToolbar {
		id: rowerView
		objectName : 'viewrower'  // + roweritem.rindex
		Component.onCompleted: {
		    draw_mpl.rowerprofile(rowerView.qmlGetFigure, rindex)
		}
                            
		Layout.fillWidth: true
		Layout.fillHeight: true
                
		Layout.minimumWidth: 200
		Layout.minimumHeight: 200
            }
	}
    }
}
