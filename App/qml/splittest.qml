import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import QtQuick.Dialogs 1.3

ApplicationWindow{
    id: app
    visible:true

    SplitView {
        id: splitView
        anchors.fill: parent

	Text {
	    text: 'Pieces links'
	    SplitView.preferredWidth: 200
	}

	Text {
	text: 'Pieces rechts'
	}
    }
}


