import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12

Item {
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
