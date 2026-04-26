pragma Singleton

import QtQuick
import Quickshell

QtObject {

    /** Resolves a symlink target, returns empty string on failure */
    function readlink(path) {
        return new Promise(resolve => {
            const p = Qt.createQmlObject('import Quickshell; Process { }', root);
            p.command = ["bash", "-lc", `readlink -f -- "$1" 2>/dev/null || :`, path];
            p.stdout = Qt.createQmlObject('import Quickshell; StdioCollector {}', p);
            p.stdout.onStreamFinished.connect(() => resolve(p.stdout.text.trim()));
            p.running = true;
        });
    }

    function exists(path) {
        return new Promise(resolve => {
            const p = Qt.createQmlObject('import Quickshell; Process { }', root);
            p.command = ["bash", "-lc", `[ -e "$1" ] && echo yes || echo no`, path];
            p.stdout = Qt.createQmlObject('import Quickshell; StdioCollector {}', p);
            p.stdout.onStreamFinished.connect(() => resolve(p.stdout.text.trim() === "yes"));
            p.running = true;
        });
    }
}
