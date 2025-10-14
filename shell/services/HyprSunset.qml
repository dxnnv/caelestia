pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: hyprsunsetToggle

    property bool active: false

    Process {
        id: checkProc
        onExited: code => {
            hyprsunsetToggle.active = (code === 0);
        }
    }

    function refresh() {
        checkProc.exec(["pgrep", "-x", "hyprsunset"]);
    }

    function start(temp) {
        const args = ["hyprsunset"];
        if (temp)
            args.push("-t", String(temp));
        Quickshell.execDetached(args);
        active = true;
    }

    function stop() {
        Quickshell.execDetached(["pkill", "-x", "hyprsunset"]);
        active = false;
    }

    function toggle(temp) {
        refresh();
        Qt.callLater(() => {
            if (active)
                stop();
            else
                start(temp);
        });
    }

    Timer {
        interval: 5000
        running: true
        repeat: true
        onTriggered: hyprsunsetToggle.refresh()
    }

    Component.onCompleted: refresh()
}
