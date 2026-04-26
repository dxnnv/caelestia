pragma Singleton
pragma ComponentBehavior: Bound

import qs.components.misc
import qs.utils
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: root

    property list<var> ddcMonitors: []
    readonly property list<Monitor> monitors: variants.instances
    property bool appleDisplayPresent: false
    readonly property string ddcLockFile: `${Quickshell.env("XDG_RUNTIME_DIR")}/caelestia-ddcutil.lock`
    property var ddcQueue: Promise.resolve()

    function getMonitorForScreen(screen: ShellScreen): var {
        return monitors.find(m => m.modelData === screen);
    }

    function getMonitor(query: string): var {
        if (query === "active") {
            return monitors.find(m => Hypr.monitorFor(m.modelData)?.focused);
        }

        if (query.startsWith("model:")) {
            const model = query.slice(6);
            return monitors.find(m => m.modelData.model === model);
        }

        if (query.startsWith("serial:")) {
            const serial = query.slice(7);
            return monitors.find(m => m.modelData.serialNumber === serial);
        }

        if (query.startsWith("id:")) {
            const id = parseInt(query.slice(3), 10);
            return monitors.find(m => Hypr.monitorFor(m.modelData)?.id === id);
        }

        return monitors.find(m => m.modelData.name === query);
    }

    function increaseBrightness(): void {
        const monitor = getMonitor("active");
        if (monitor)
            monitor.setBrightness(monitor.brightness + 0.1);
    }

    function decreaseBrightness(): void {
        const monitor = getMonitor("active");
        if (monitor)
            monitor.setBrightness(monitor.brightness - 0.1);
    }

    function ddcCommand(args): var {
        return ["flock", "-w", "10", ddcLockFile, "ddcutil"].concat(args.map(a => String(a)));
    }

    function detectDdcMonitors(): void {
        root.runDdc(["detect", "--brief"]).then(r => {
            if (r.code !== 0) {
                console.warn("ddcutil detect failed:", r.stderr || r.stdout);
                return;
            }

            root.ddcMonitors = r.stdout.trim().split("\n\n").filter(d => d.startsWith("Display ")).map(d => ({
                        busNum: d.match(/I2C bus:[ ]*\/dev\/i2c-([0-9]+)/)?.[1] ?? "",
                        connector: d.match(/DRM connector:\s+(.*)/)?.[1]?.replace(/^card\d+-/, "") ?? ""
                    })).filter(d => d.busNum !== "" && d.connector !== "");
        });
    }

    function runDdc(args): var {
        const run = () => ProcessUtil.run(ddcCommand(args));

        // Serialize all ddcutil calls from this shell.
        root.ddcQueue = root.ddcQueue.then(run, run);

        return root.ddcQueue;
    }

    onMonitorsChanged: ddcDetectTimer.restart()

    Timer {
        id: ddcDetectTimer
        interval: 1000
        repeat: false
        onTriggered: root.detectDdcMonitors()
    }

    Variants {
        id: variants

        model: Quickshell.screens

        Monitor {}
    }

    Process {
        running: true
        command: ["sh", "-c", "asdbctl get"] // To avoid warnings if asdbctl is not installed
        stdout: StdioCollector {
            onStreamFinished: root.appleDisplayPresent = text.trim().length > 0
        }
    }

    CustomShortcut {
        name: "brightnessUp"
        description: "Increase brightness"
        onPressed: root.increaseBrightness()
    }

    CustomShortcut {
        name: "brightnessDown"
        description: "Decrease brightness"
        onPressed: root.decreaseBrightness()
    }

    IpcHandler {
        target: "brightness"

        function get(): real {
            return getFor("active");
        }

        // Allows searching by active/model/serial/id/name
        function getFor(query: string): real {
            return root.getMonitor(query)?.brightness ?? -1;
        }

        function set(value: string): string {
            return setFor("active", value);
        }

        // Handles brightness value like brightnessctl: 0.1, +0.1, 0.1-, 10%, +10%, 10%-
        function setFor(query: string, value: string): string {
            const monitor = root.getMonitor(query);
            if (!monitor)
                return "Invalid monitor: " + query;

            let targetBrightness;
            if (value.endsWith("%-")) {
                const percent = parseFloat(value.slice(0, -2));
                targetBrightness = monitor.brightness - (percent / 100);
            } else if (value.startsWith("+") && value.endsWith("%")) {
                const percent = parseFloat(value.slice(1, -1));
                targetBrightness = monitor.brightness + (percent / 100);
            } else if (value.endsWith("%")) {
                const percent = parseFloat(value.slice(0, -1));
                targetBrightness = percent / 100;
            } else if (value.startsWith("+")) {
                const increment = parseFloat(value.slice(1));
                targetBrightness = monitor.brightness + increment;
            } else if (value.endsWith("-")) {
                const decrement = parseFloat(value.slice(0, -1));
                targetBrightness = monitor.brightness - decrement;
            } else if (value.includes("%") || value.includes("-") || value.includes("+")) {
                return `Invalid brightness format: ${value}\nExpected: 0.1, +0.1, 0.1-, 10%, +10%, 10%-`;
            } else {
                targetBrightness = parseFloat(value);
            }

            if (isNaN(targetBrightness))
                return `Failed to parse value: ${value}\nExpected: 0.1, +0.1, 0.1-, 10%, +10%, 10%-`;

            monitor.setBrightness(targetBrightness);

            return `Set monitor ${monitor.modelData.name} brightness to ${+monitor.brightness.toFixed(2)}`;
        }
    }

    component Monitor: QtObject {
        id: monitor

        required property ShellScreen modelData
        readonly property bool isDdc: root.ddcMonitors.some(m => m.connector === modelData.name)
        readonly property string busNum: root.ddcMonitors.find(m => m.connector === modelData.name)?.busNum ?? ""
        readonly property bool isAppleDisplay: root.appleDisplayPresent && modelData.model.startsWith("StudioDisplay")
        property real brightness
        property real pendingBrightness: NaN
        property bool ddcSetting: false

        readonly property Process initProc: Process {
            stdout: StdioCollector {
                onStreamFinished: {
                    if (monitor.isAppleDisplay) {
                        const val = parseInt(text.trim());
                        monitor.brightness = val / 101;
                    } else {
                        const [, , , cur, max] = text.split(" ");
                        monitor.brightness = parseInt(cur) / parseInt(max);
                    }
                }
            }
        }

        function flushDdcBrightness(): void {
            if (ddcSetting || isNaN(pendingBrightness))
                return;

            const value = pendingBrightness;
            pendingBrightness = NaN;

            const rounded = Math.round(value * 100);
            ddcSetting = true;

            root.runDdc(["-b", busNum, "setvcp", "10", rounded]).then(r => {
                if (r.code !== 0)
                    console.warn(`ddcutil setvcp failed for bus ${busNum}:`, r.stderr || r.stdout);

                ddcSetting = false;

                if (!isNaN(pendingBrightness))
                    flushDdcBrightness();
            });
        }

        function setBrightness(value: real): void {
            value = Math.max(0, Math.min(1, value));
            const rounded = Math.round(value * 100);
            if (Math.round(brightness * 100) === rounded)
                return;

            brightness = value;

            if (isAppleDisplay) {
                Quickshell.execDetached(["asdbctl", "set", rounded]);
                return;
            }

            if (isDdc) {
                pendingBrightness = value;
                flushDdcBrightness();
                return;
            }

            Quickshell.execDetached(["brightnessctl", "s", `${rounded}%`]);
        }

        function initBrightness(): void {
            if (initProc.running)
                return;

            if (isAppleDisplay) {
                initProc.command = ["asdbctl", "get"];
                initProc.running = true;
                return;
            }

            if (isDdc) {
                root.runDdc(["-b", busNum, "getvcp", "10", "--brief"]).then(r => {
                    if (r.code !== 0) {
                        console.warn(`ddcutil getvcp failed for bus ${busNum}:`, r.stderr || r.stdout);
                        return;
                    }

                    const parts = r.stdout.trim().split(/\s+/);
                    const cur = parseInt(parts[3]);
                    const max = parseInt(parts[4]);

                    if (!isNaN(cur) && !isNaN(max) && max > 0)
                        monitor.brightness = cur / max;
                });
                return;
            }

            initProc.command = ["sh", "-c", "echo a b c $(brightnessctl g) $(brightnessctl m)"];
            initProc.running = true;
        }

        onBusNumChanged: initBrightness()
        Component.onCompleted: initBrightness()
    }
}
