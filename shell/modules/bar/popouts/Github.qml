pragma ComponentBehavior: Bound
import qs.components
import qs.config
import qs.services
import QtQuick
import QtQuick.Layouts

Item {
    id: root
    required property var wrapper
    property var days: []
    property int total: 0
    property string username: ""
    property string lastError: ""

    implicitWidth: layout.implicitWidth + Appearance.padding.normal * 2
    implicitHeight: layout.implicitHeight + Appearance.padding.normal * 3

    ColumnLayout {
        id: layout
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        spacing: Appearance.spacing.normal

        StyledText {
            text: root.username && root.username.length ? `@${root.username}` : "GitHub"
            font.weight: 600
        }

        StyledText {
            text: root.lastError && root.lastError.length ? `Error: ${root.lastError}` : `Last 7 days: ${root.total} commits`
            color: root.lastError && root.lastError.length ? Colours.palette.m3error : Colours.palette.m3secondary
        }

        StyledRect {
            Layout.topMargin: Appearance.spacing.normal
            radius: Appearance.rounding.normal
            color: Colours.palette.m3primaryContainer
            implicitHeight: ctaRow.implicitHeight + Appearance.padding.small * 2
            implicitWidth: ctaRow.implicitWidth + Appearance.padding.normal * 2

            StateLayer {
                color: Colours.palette.m3onPrimaryContainer
                function onClicked() {
                    root.wrapper.hasCurrent = false;
                    Qt.openUrlExternally("https://github.com/" + (root.username || ""));
                }
            }

            RowLayout {
                id: ctaRow
                anchors.centerIn: parent
                spacing: Appearance.spacing.smaller

                StyledText {
                    Layout.leftMargin: Appearance.padding.smaller
                    text: "Open profile"
                    color: Colours.palette.m3onPrimaryContainer
                }

                MaterialIcon {
                    text: "chevron_right"
                    color: Colours.palette.m3onPrimaryContainer
                    font.pointSize: Appearance.font.size.large
                }

                Item {
                    Layout.fillWidth: true
                }
            }
        }
    }
}
