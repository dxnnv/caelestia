pragma ComponentBehavior: Bound

import qs.components
import qs.components.controls
import qs.services
import qs.config
import qs.utils
import QtQuick
import Caelestia
import Quickshell.Io
import QtQuick.Layouts
import Quickshell

Item {
    id: root

    required property Brightness.Monitor monitor
    required property var visibilities

    required property real volume
    required property bool muted
    required property real sourceVolume
    required property bool sourceMuted
    required property real brightness

    property real lastVolume: (volume > 0 ? volume : 0.5)
    property real lastSourceVolume: (sourceVolume > 0 ? sourceVolume : 0.5)

    implicitWidth: layout.implicitWidth + Appearance.padding.large * 2
    implicitHeight: layout.implicitHeight + Appearance.padding.large * 2

    function clamp(x) {
        return Math.max(0, Math.min(1, x));
    }

    ColumnLayout {
        id: layout

        anchors.centerIn: parent
        spacing: Appearance.spacing.normal

        // Speaker volume
        CustomMouseArea {
            implicitWidth: Config.osd.sizes.sliderWidth
            implicitHeight: Config.osd.sizes.sliderHeight

            function onWheel(event: WheelEvent) {
                if (event.angleDelta.y > 0)
                    Audio.incrementVolume();
                else if (event.angleDelta.y < 0)
                    Audio.decrementVolume();
            }

            FilledSlider {
                anchors.fill: parent

                icon: Icons.getVolumeIcon(value, root.muted)
                value: root.volume
                onMoved: {
                    if (value > 0)
                        root.lastVolume = value;
                    Audio.setVolume(value);
                }

                enableIconTap: true
                onIconTapped: {
                    if (root.muted || root.volume === 0) {
                        Audio.setVolume(root.clamp(root.lastVolume || 0.5));
                    } else {
                        root.lastVolume = root.volume > 0 ? root.volume : (root.lastVolume || 0.5);
                        Audio.setVolume(0);
                    }
                }
            }
        }

        // Microphone volume
        WrappedLoader {
            shouldBeActive: Config.osd.enableMicrophone && (!Config.osd.enableBrightness || !root.visibilities.session)

            sourceComponent: CustomMouseArea {
                implicitWidth: Config.osd.sizes.sliderWidth
                implicitHeight: Config.osd.sizes.sliderHeight

                function onWheel(event: WheelEvent) {
                    if (event.angleDelta.y > 0)
                        Audio.incrementSourceVolume();
                    else if (event.angleDelta.y < 0)
                        Audio.decrementSourceVolume();
                }

                FilledSlider {
                    anchors.fill: parent

                    icon: Icons.getMicVolumeIcon(value, root.sourceMuted)
                    value: root.sourceVolume
                    onMoved: {
                        if (value > 0)
                            root.lastSourceVolume = value;
                        Audio.setSourceVolume(value);
                    }

                    enableIconTap: true
                    onIconTapped: {
                        if (root.sourceMuted || root.sourceVolume === 0) {
                            Audio.setSourceVolume(root.clamp(root.lastSourceVolume || 0.5));
                        } else {
                            root.lastSourceVolume = root.sourceVolume > 0 ? root.sourceVolume : (root.lastSourceVolume || 0.5);
                            Audio.setSourceVolume(0);
                        }
                    }
                }
            }
        }

        // Brightness
        WrappedLoader {
            shouldBeActive: Config.osd.enableBrightness

            sourceComponent: CustomMouseArea {
                implicitWidth: Config.osd.sizes.sliderWidth
                implicitHeight: Config.osd.sizes.sliderHeight

                function onWheel(event: WheelEvent) {
                    const monitor = root.monitor;
                    if (!monitor)
                        return;
                    if (event.angleDelta.y > 0)
                        monitor.setBrightness(monitor.brightness + 0.1);
                    else if (event.angleDelta.y < 0)
                        monitor.setBrightness(monitor.brightness - 0.1);
                }

                FilledSlider {
                    anchors.fill: parent

                    icon: `brightness_${(Math.round(value * 6) + 1)}`
                    value: root.brightness
                    onMoved: root.monitor?.setBrightness(value)

                    enableIconTap: true
                    onIconTapped: HyprSunset.toggle(5000)
                }
            }
        }
    }

    component WrappedLoader: Loader {
        required property bool shouldBeActive

        Layout.preferredHeight: shouldBeActive ? Config.osd.sizes.sliderHeight : 0
        opacity: shouldBeActive ? 1 : 0
        active: opacity > 0
        asynchronous: true
        visible: active

        Behavior on Layout.preferredHeight {
            Anim {
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }

        Behavior on opacity {
            Anim {}
        }
    }
}
