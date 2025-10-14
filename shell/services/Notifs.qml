pragma Singleton
pragma ComponentBehavior: Bound

import qs.components.misc
import qs.config
import qs.utils
import Caelestia
import Quickshell
import Quickshell.Io
import Quickshell.Io as QsIo
import Quickshell.Services.Notifications
import QtQuick

Singleton {
    id: root

    // --- SwayNC integration ---
    property bool swayncDnd: false
    property int swayncCount: 0

    property var list: []
    readonly property var notClosed: list.filter(n => !n.closed)
    readonly property var popups: list.filter(n => n.popup)

    property bool loaded

    // --- DND Toggle Toasts ---
    onSwayncDndChanged: {
        if (!Config.utilities.toasts.dndChanged)
            return;
        if (swayncDnd)
            Toaster.toast(qsTr("Do not disturb enabled"), qsTr("Popup notifications are now disabled"), "do_not_disturb_on");
        else
            Toaster.toast(qsTr("Do not disturb disabled"), qsTr("Popup notifications are now enabled"), "do_not_disturb_off");
    }

    CustomShortcut {
        name: "clearNotifs"
        description: "Clear all notifications"
        onPressed: {
            for (const notif of root.list.slice())
                notif.close();
        }
    }

    IpcHandler {
        target: "notifs"

        function clear(): void {
            for (const notif of root.list.slice())
                notif.close();
        }

        function isDndEnabled(): bool {
            return root.swayncDnd;
        }
        function toggleDnd(): void {
            root.setDnd(!root.swayncDnd);
        }
        function enableDnd(): void {
            root.setDnd(true);
        }
        function disableDnd(): void {
            root.setDnd(false);
        }
    }

    // --- SwayNC controls ---
    function refreshDnd() {
        dndProc.exec(["swaync-client", "--get-dnd"]);
    }
    function setDnd(on) {
        runProc(["swaync-client", on ? "--dnd-on" : "--dnd-off"]);
        swayncDnd = !!on;
    }
    function refreshCount() {
        cntProc.exec(["swaync-client", "--count"]);
    }
    function openCenter() {
        runProc(["swaync-client", "--open-panel"]);
    }
    function toggleCenter() {
        runProc(["swaync-client", "--toggle-panel"]);
    }

    function runProc(args) {
        Qt.createQmlObject('import Quickshell.Io; Process { }', root).exec(args);
    }

    Timer {
        interval: 2000
        running: true
        repeat: true
        onTriggered: root.refreshCount()
    }

    Component.onCompleted: {
        refreshDnd();
        refreshCount();
    }

    QsIo.Process {
        id: dndProc
    }
    Connections {
        target: dndProc.stdout
        function onRead(data) {
            const s = (data || "").trim();
            if (s === "true" || s === "false")
                root.swayncDnd = (s === "true");
        }
    }

    QsIo.Process {
        id: cntProc
    }
    Connections {
        target: cntProc.stdout
        function onRead(data) {
            const n = parseInt((data || "").trim());
            if (!Number.isNaN(n))
                root.swayncCount = n;
        }
    }

    QsIo.Process {
        id: tap
        command: ["python3", Qt.resolvedUrl("notif_listen.py")]
        running: true
        property string _buf: ""
        onExited: (code, status) => {
            tap.running = true;
        }
    }
    Connections {
        target: tap.stdout
        function onRead(chunk) {
            if (!chunk)
                return;
            tap._buf += chunk;
            const parts = tap._buf.split("\n");
            tap._buf = parts.pop();
            for (const line of parts) {
                const s = line.trim();
                if (!s)
                    continue;
                let n;
                try {
                    n = JSON.parse(s);
                } catch (_) {
                    continue;
                }
                const arr = Array.isArray(n.actions) ? n.actions : [];
                const actions = [];
                for (let i = 0; i + 1 < arr.length; i += 2) {
                    const id = arr[i], text = arr[i + 1];
                    actions.push({
                        identifier: id,
                        text,
                        invoke: () => runProc(["swaync-client", "--action"])
                    });
                }
                const comp = notifComp.createObject(root, {
                    popup: !root.swayncDnd && ![...Visibilities.screens.values()].some(v => v.sidebar),
                    time: new Date(),
                    id: Math.floor(Math.random() * 2147483647).toString(),
                    summary: n.summary,
                    body: n.body,
                    appIcon: n.appIcon,
                    appName: n.appName,
                    image: "",
                    expireTimeout: (n.expireTimeout > 0 ? n.expireTimeout : Config.notifs.defaultExpireTimeout),
                    urgency: NotificationUrgency.Normal,
                    resident: false,
                    hasActionIcons: actions.length > 0,
                    actions
                });
                root.list = [comp, ...root.list];
            }
        }
    }

    component Notif: QtObject {
        id: notif

        property bool popup
        property bool closed
        property var locks: new Set()

        property date time: new Date()
        readonly property string timeStr: {
            const diff = Time.date.getTime() - time.getTime();
            const m = Math.floor(diff / 60000);
            if (m < 1)
                return qsTr("now");
            const h = Math.floor(m / 60);
            const d = Math.floor(h / 24);
            if (d > 0)
                return `${d}d`;
            if (h > 0)
                return `${h}h`;
            return `${m}m`;
        }

        property Notification notification
        property string id
        property string summary
        property string body
        property string appIcon
        property string appName
        property string image
        property real expireTimeout: Config.notifs.defaultExpireTimeout
        property int urgency: NotificationUrgency.Normal
        property bool resident
        property bool hasActionIcons
        property list<var> actions

        readonly property Timer timer: Timer {
            running: true
            interval: notif.expireTimeout > 0 ? notif.expireTimeout : Config.notifs.defaultExpireTimeout
            onTriggered: {
                if (Config.notifs.expire)
                    notif.popup = false;
            }
        }

        readonly property LazyLoader dummyImageLoader: LazyLoader {
            active: false
            PanelWindow {
                implicitWidth: Config.notifs.sizes.image
                implicitHeight: Config.notifs.sizes.image
                color: "transparent"
                mask: Region {}
                Image {
                    anchors.fill: parent
                    source: Qt.resolvedUrl(notif.image)
                    fillMode: Image.PreserveAspectCrop
                    cache: false
                    asynchronous: true
                    opacity: 0
                    onStatusChanged: {
                        if (status !== Image.Ready)
                            return;
                        const cacheKey = notif.appName + notif.summary + notif.id;
                        let h1 = 0xdeadbeef, h2 = 0x41c6ce57, ch;
                        for (let i = 0; i < cacheKey.length; i++) {
                            ch = cacheKey.charCodeAt(i);
                            h1 = Math.imul(h1 ^ ch, 2654435761);
                            h2 = Math.imul(h2 ^ ch, 1597334677);
                        }
                        h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507);
                        h1 ^= Math.imul(h2 ^ (h2 >>> 13), 3266489909);
                        h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507);
                        h2 ^= Math.imul(h1 ^ (h1 >>> 13), 3266489909);
                        const hash = (h2 >>> 0).toString(16).padStart(8, 0) + (h1 >>> 0).toString(16).padStart(8, 0);
                        const cache = `${Paths.notifimagecache}/${hash}.png`;
                        CUtils.saveItem(this, Qt.resolvedUrl(cache), () => {
                            notif.image = cache;
                            notif.dummyImageLoader.active = false;
                        });
                    }
                }
            }
        }

        readonly property Connections conn: Connections {
            target: notif.notification
            function onClosed(): void {
                notif.close();
            }
            function onSummaryChanged(): void {
                notif.summary = notif.notification.summary;
            }
            function onBodyChanged(): void {
                notif.body = notif.notification.body;
            }
            function onAppIconChanged(): void {
                notif.appIcon = notif.notification.appIcon;
            }
            function onAppNameChanged(): void {
                notif.appName = notif.notification.appName;
            }
            function onImageChanged(): void {
                notif.image = notif.notification.image;
                if (notif.notification?.image)
                    notif.dummyImageLoader.active = true;
            }
            function onExpireTimeoutChanged(): void {
                notif.expireTimeout = notif.notification.expireTimeout;
            }
            function onUrgencyChanged(): void {
                notif.urgency = notif.notification.urgency;
            }
            function onResidentChanged(): void {
                notif.resident = notif.notification.resident;
            }
            function onHasActionIconsChanged(): void {
                notif.hasActionIcons = notif.notification.hasActionIcons;
            }
            function onActionsChanged(): void {
                notif.actions = notif.notification.actions.map(a => ({
                            identifier: a.identifier,
                            text: a.text,
                            invoke: () => a.invoke()
                        }));
            }
        }

        function lock(item: Item): void {
            locks.add(item);
        }
        function unlock(item: Item): void {
            locks.delete(item);
            if (closed)
                close();
        }
        function close(): void {
            closed = true;
            if (locks.size === 0 && root.list.includes(this)) {
                root.list = root.list.filter(n => n !== this);
                notification?.dismiss();
                destroy();
            }
        }

        Component.onCompleted: {
            if (!notification)
                return;
            id = notification.id;
            summary = notification.summary;
            body = notification.body;
            appIcon = notification.appIcon;
            appName = notification.appName;
            image = notification.image;
            if (notification?.image)
                dummyImageLoader.active = true;
            expireTimeout = notification.expireTimeout;
            urgency = notification.urgency;
            resident = notification.resident;
            hasActionIcons = notification.hasActionIcons;
            actions = notification.actions.map(a => ({
                        identifier: a.identifier,
                        text: a.text,
                        invoke: () => a.invoke()
                    }));
        }
    }

    Component {
        id: notifComp
        Notif {}
    }
}
