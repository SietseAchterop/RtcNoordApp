import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import Backend 1.0

Item {
    RowLayout {
        anchors.fill: parent
	spacing: 0

	ColumnLayout {
            Layout.fillWidth: true

            FigureToolbar {
                id: mplPieces
                objectName : "pieces"
                            
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Layout.minimumWidth: 10
                Layout.minimumHeight: 10
            }
            

	}

      Connections {
            target: sensorModel
            onDataChanged: {
                draw_mpl.update_figure()
            }
      }

        Pane {
            id: right
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.fillHeight: true
	    
            ColumnLayout {
                id: right_vbox
                spacing: 5
                
                Label {
                    id: log_label
                    text: qsTr("Available sensors:")
                }

                ListView {
                    id: series_list_view
                    height: 180

                    Layout.fillWidth: true
                    
                    clip: true
                    
                    model: sensorModel
                    delegate: CheckBox {
                        checked : selected;
			font.pixelSize: 12
                        text: name
                        onClicked: {
                            selected = checked;
                        }
                    }
		    // highlight: Rectangle { color: "lightsteelblue"; radius: 5 }
		    // focus: true
                }

                Label {
                    id: piecelabel
                    text: qsTr("Select pieces")
                }


		
		RowLayout {
		   
		    Button {
			id: npbutton
			property color plotColor : "lightblue"  // '#add8e6'
			text: "New piece"
			onClicked: {
			    draw_mpl.new_piece(piecename.text);
			    if (plotColor == "#add8e6")
				plotColor = 'red'
			    else
				plotColor = 'lightblue'

			}
			background: Rectangle {
			    color: npbutton.plotColor
			}
		    }
		    TextField {
			id: piecename
			selectByMouse: true   // is iets raars mee?
			implicitWidth: 120
			placeholderText: qsTr("Name")
		    }

		}

                ListView {
                    id: create_pieces_view
		    height: 150
		    Layout.fillWidth: true
                    clip: true
                    
                    model: makePiecesModel
                    delegate: Row {
			
			Text {
			    width: 40
			    text: name
			}
			Button {
			    width: 35
			    height: 30
			    icon.name: "window-close"
 			    icon.source: "images/cut.png"
			    onClicked: { draw_mpl.remove_piece(index);
				       }
			}
		    }
                }
		Button {
		    text: 'save sessionInfo'
		    onClicked: draw_mpl.savepieces();
		}
	    }
	}
    }
}
