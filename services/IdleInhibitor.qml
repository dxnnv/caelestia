pragma Singleton

import Quickshell
import Quickshell.Io
import Caelestia.Internal as Internal

Singleton {
    id: root

    property var window: defaultWindow
    property alias enabled: props.enabled
    readonly property alias enabledSince: props.enabledSince

    onEnabledChanged: {
        if (enabled)
            props.enabledSince = new Date();
    }

    PersistentProperties {
        id: props
        property bool enabled
        property date enabledSince
        reloadableId: "idleInhibitor"
    }

    PanelWindow {
        id: defaultWindow

        implicitWidth: 0
        implicitHeight: 0
        visible: false
        color: "transparent"
        mask: Region {}
    }

    Internal.IdleInhibitor {
        enabled: props.enabled && !!root.window
        window: root.window
    }

    IpcHandler {
        target: "idleInhibitor"

        function isEnabled(): bool {
            return props.enabled;
        }

        function toggle(): void {
            props.enabled = !props.enabled;
        }

        function enable(): void {
            props.enabled = true;
        }

        function disable(): void {
            props.enabled = false;
        }
    }
}
