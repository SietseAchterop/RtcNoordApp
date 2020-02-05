import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.12
import QtQuick.Dialogs 1.3

ApplicationWindow {
    id: applicationWindow
    visible: true
    width: 900
    height: 600
    title: qsTr("RTCNoord")

    // Component.onCompleted: console.log("Completed Running!")
    Component.onCompleted: draw_mpl.selectCurrent()

    FileDialog {
        id: filedialog
        nameFilters: ["CSV files (*.csv)", "All Files (*.*)"]
	folder: draw_mpl.csvDir
        onAccepted: {
            draw_mpl.createSessionCsv(fileUrl);
        }
    } 

    FileDialog {
        id: sessiondialog
        nameFilters: ["YAML files (*.yaml)", "All Files (*.*)"]
	folder: draw_mpl.sessionDir
        onAccepted: {
            draw_mpl.selectSessionFile(fileUrl)
        }
    } 

    FileDialog {
        id: seconddialog
        nameFilters: ["YAML files (*.yaml)", "All Files (*.*)"]
	folder: draw_mpl.sessionDir
        onAccepted: {
            piece_mpl.selectSecondFile(fileUrl)
        }
    } 

    MessageDialog {
        id: aboutDialog
        icon: StandardIcon.Information
        title: qsTr("About..")
        text: "RtcNoord application."
    }

    Action {
        id: copyAction
        text: qsTr("&Copy")
        shortcut: StandardKey.Copy

	//iconName: "edit-copy"
        enabled: (!!activeFocusItem && !!activeFocusItem["copy"])
        onTriggered: activeFocusItem.copy()
    }

    Action {
        id: cutAction
        text: qsTr("Cu&t")
        shortcut: StandardKey.Cut
        //iconName: "edit-cut"
        enabled: (!!activeFocusItem && !!activeFocusItem["cut"])
        onTriggered: activeFocusItem.cut()
    }

    Action {
        id: pasteAction
        text: qsTr("&Paste")
        shortcut: StandardKey.Paste
        //iconName: "edit-paste"
        enabled: (!!activeFocusItem && !!activeFocusItem["paste"])
        onTriggered: activeFocusItem.paste()
    }

    menuBar: MenuBar {
	contentHeight:20
        Menu {
            title: qsTr("&Session")
            MenuItem {
                text: qsTr("C&reate session (csv)")
                onTriggered: filedialog.open()
            }
            MenuItem {
                text: qsTr("S&elect session")
                onTriggered: sessiondialog.open()
            }
            MenuItem {
                text: qsTr("End program")
                onTriggered: Qt.quit()
            }
        }
        Menu {
            title: qsTr("&Config")
            MenuItem {
                action: cutAction
            }
            MenuItem {
                action: copyAction
            }
            MenuItem {
                action: pasteAction
            }
        }
        Menu {
            title: qsTr("&Help")
            MenuItem {
                text: qsTr("About...")
                onTriggered: aboutDialog.open()
            }
        }
    }


    StackLayout {
        id: stacklayout
        width: parent.width
	height: parent.height
	
        anchors.horizontalCenter: parent.horizontalCenter
	
        currentIndex: tabBar.currentIndex
	
        Pieces {
            id: iets1
        }

        ViewPiece {
            id: iets2
        }

        BoatProfile {
            id: iets3
        }

        CrewProfile {
            id: iets4
        }

	Repeater {
	    model: draw_mpl.nmbrRowers
	    delegate: RowerProfile {
		rindex : index
	    }
	}

        SessionInfo {
            id: iets5
	    objectName:'sessioninfo'
        }

        NogWat{
            id: iets6
        }

    }



    footer: TabBar {
        id: tabBar
        implicitWidth: 800
        currentIndex: stacklayout.currentIndex


        TabButton {
            id: tabButton
	    implicitHeight:20
            text: qsTr("Setup pieces")
        }

        TabButton {
            id: tabButton1
	    implicitHeight:20
            text: qsTr("View piece")
        }

        TabButton {
            id: tabButton2
	    implicitHeight:20
            text: qsTr("Boat")
        }

        TabButton {
            id: tabButton3
	    implicitHeight:20
            text: qsTr("Crew")
        }

	Repeater {
	    id: tab_rr
	    model: draw_mpl.nmbrRowers
            TabButton {
	    implicitHeight:20
		text: { "R " + (index + 1).toString() }
            }
	}

        TabButton {
            id: tabButton4
	    implicitHeight:20
            text: qsTr("Session info")
        }

        TabButton {
            id: tabButton5
	    implicitHeight:20
            text: qsTr("Nog wat ..")
	}
    }

    // En er iets onder
    Text {
        anchors.bottom: parent.bottom
	
	text: draw_mpl.statusText
    }

}

