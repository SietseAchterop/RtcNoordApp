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
                id: mplView
                objectName : "viewpiece"
                            
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Layout.minimumWidth: 10
                Layout.minimumHeight: 10
            }
            


	    Row {
		Text {
		    width: 400
                    Layout.minimumHeight: 50
		    text: 'text:tempo(s), fix session (ro), ..'
		}

		Button {
		    text: "Secondary"
		    onClicked: { seconddialog.open()
			       }
		}

		Button {
		    text: "Video"
		    onClicked: { piece_mpl.videoOpenClose()
				 // evt kleur aanpassen: open of close
			       }
		}

	    }
	}

	Connections {
            target: sensorModel3
            onDataChanged: {
                piece_mpl.update_figure()
            }
	}

	Connections {
            target: sensorModel4
            onDataChanged: {
                piece_mpl.update_figure()
            }
	}


        Pane {
            id: right
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            Layout.fillHeight: true
	    
	    Column {
	    Row {
		ColumnLayout {

                    spacing: 2
                
                    Label {
			id: log_label
			text: draw_mpl.sessionName
                    }

                    ListView {
			id: series_list_view
			height: 180
			width: 150
			Layout.fillWidth: true
                    
			clip: true
                    
			model: sensorModel3
			delegate: CheckBox {
                            checked : selected;
			    font.pixelSize: 12
                            text: name
                            onClicked: {
				selected = checked;
                            }
			}
                    }

		    // items zijn piece namen
		    ComboBox {
			model: draw_mpl.the_pieces
			onActivated: piece_mpl.set_piece(currentText)
		    }
                }


		// The second session
		ColumnLayout {
                    id: right_vbox1
                    spacing: 2
                
		    Text {
			text: piece_mpl.sessionName
		    }

                    ListView {
			id: series_list_view2
			height: 180
			width: 150
			Layout.fillWidth: true
                    
			clip: true
                    
			model: sensorModel4
			delegate: CheckBox {
                            checked : selected;
			    font.pixelSize: 12
                            text: name
                            onClicked: {
				selected = checked;
                            }
			}
                    }

		    ComboBox {
			model: piece_mpl.the_2nd_pieces
			onActivated: piece_mpl.set_2nd_piece(currentText)
		    }
		}
	    }


		Text {
		    width: 20
		    Layout.minimumHeight: 50
		    text: ''
		}

		CheckBox {
		    checked: false
		    text: qsTr("Scaled")
		    onPressed: {
			piece_mpl.set_scaling(checked);
		    }
		}

		Text {
		    width: 20
		    Layout.minimumHeight: 50
		    text: ''
		}

		Text {
		    width: 20
		    Layout.minimumHeight: 50
		    text: 'Video control'
		}

		Text {
		    width: 20
		    Layout.minimumHeight: 50
		    text: ''
		}

		Row {
		    spacing: 10
		    Button {
			width: 40
			icon.name: "niet"
			icon.source: "images/media-seek-backward"
			onClicked: { piece_mpl.frame_seek(-0.2)}
		    }


		    Button {
			width: 40
			icon.name: "niet"
			icon.source: "images/media-playback-start-rtl"
			onClicked: { piece_mpl.frame_back_step()
				   }
		    }

		    Button {
			id: syncbutton
			width: 40
			property color plotColor : "lightblue"  // '#add8e6'
			icon.name: "niet"
			icon.source: "images/media-playback-stop"
			onClicked: {
			    if (plotColor == "#add8e6") {
				piece_mpl.sync_mode(true)
				plotColor = 'red'
			    }
			    else {
				piece_mpl.sync_mode(false)
				plotColor = 'lightblue'
			    }   
			}
			background: Rectangle {
			    color: syncbutton.plotColor
			}
		    }

		    Button {
			width: 40
			icon.name: "niet"
			icon.source: "images/media-playback-start"
			onClicked: { piece_mpl.frame_step()
				   }
		    }

		    Button {
			width: 40
			icon.name: "niet"
			icon.source: "images/media-seek-forward"
			onClicked: { piece_mpl.frame_seek(0.2)
				   }
		    }
		}

	    }
	}
    }
}

