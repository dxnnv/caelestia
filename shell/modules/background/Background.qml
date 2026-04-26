pragma ComponentBehavior: Bound

import qs.components
import qs.components.containers
import qs.services
import qs.config
import Quickshell
import Quickshell.Wayland
import QtQuick

Loader {
    asynchronous: true
    active: Config.background.enabled

    sourceComponent: Variants {
        model: Quickshell.screens

        StyledWindow {
            id: win

            required property ShellScreen modelData

            screen: modelData
            name: "background"
            WlrLayershell.exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Background
            color: "black"

            anchors.top: true
            anchors.bottom: true
            anchors.left: true
            anchors.right: true

            Wallpaper {
                id: wallpaper
            }

            Loader {
                readonly property var hyprMonitor: Hypr.monitorFor(win.modelData)
                readonly property var activeWs: hyprMonitor ? hyprMonitor.activeWorkspace : null
                readonly property bool shouldBeActive: {
                    if (!Config.background.visualiser.enabled)
                        return false;
                    if (!Config.background.visualiser.autoHide)
                        return true;
                    return activeWs ? activeWs.toplevels.values.every(t => t.lastIpcObject.floating) : false;
                }
                property real offset: shouldBeActive ? 0 : ((win.modelData?.height ?? 0) * 0.2)

                anchors.fill: parent
                anchors.topMargin: offset
                anchors.bottomMargin: -offset
                opacity: shouldBeActive ? 1 : 0
                active: opacity > 0
                asynchronous: true

                sourceComponent: Visualiser {
                    screen: win.modelData
                    wallpaper: wallpaper
                }

                Behavior on offset {
                    Anim {}
                }

                Behavior on opacity {
                    Anim {}
                }
            }

            Loader {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: Appearance.padding.large

                active: Config.background.desktopClock.enabled
                asynchronous: true

                source: "DesktopClock.qml"
            }
        }
    }
}
