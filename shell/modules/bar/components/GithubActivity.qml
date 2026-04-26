import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Io
import qs.components
import qs.config
import qs.modules
import qs.services

Item {
    id: root
    required property Item wrapper

    property string username: ""
    property var weekDays: []
    property int total: 0
    property string lastError: ""
    property int refreshInterval: 1800

    property color colour: Colours.palette.m3secondary

    function redact(s) {
        return (s || "").replace(/bearer\s+[A-Za-z0-9_\-.]+/gi, "bearer [redacted]");
    }

    implicitWidth: btn.implicitWidth
    implicitHeight: btn.implicitHeight

    Button {
        id: btn
        anchors.fill: parent
        background: Rectangle {
            color: "transparent"
            border.color: "transparent"
        }

        contentItem: RowLayout {
            id: row
            spacing: 6
            anchors.verticalCenter: parent.verticalCenter

            Repeater {
                model: root.weekDays
                delegate: Rectangle {
                    required property var modelData

                    width: 12
                    height: 12
                    radius: 2
                    border.width: 1
                    border.color: Qt.rgba(1, 1, 1, 0.08)
                    color: modelData.color || "#2f2f2f"
                    Layout.alignment: Qt.AlignVCenter
                }
            }

            /* Uncomment for total count beside the widget
            StyledText {
                id: text
                verticalAlignment: StyledText.AlignVCenter
                text: root.total
                font.pointSize: Appearance.font.size.smaller
                font.family: Appearance.font.family.mono
                color: root.colour
            }
            */
        }
        // Could do something with this in the future, nothing currently though to keep things decluttered
        // var counts root.lastError !== "" ? ("GitHub: " + root.lastError) : root.weekDays.map(d => `${d.date}: ${d.count}`).join("\n")
    }

    Process {
        id: proc
        stdout: StdioCollector {
            id: out
        }
        stderr: StdioCollector {
            id: err
        }

        command: ["bash", "-lc", `
        set -Eeuo pipefail
        : "\${GITHUB_TOKEN:?Missing GITHUB_TOKEN}"

        # Resolve login via token if GITHUB_USERNAME is unset
        login="\${GITHUB_USERNAME-}"
        if [ -z "$login" ]; then
          vpayload="$(python - <<'PY'
import json; print(json.dumps({"query": "query{viewer{login}}"}))
PY
          )"
          tmpv="$(mktemp)"
          vcode="$(curl -sS -o "$tmpv" -w "%{http_code}" \
                     -H "Authorization: bearer $GITHUB_TOKEN" \
                     -H "Content-Type: application/json" \
                     -X POST https://api.github.com/graphql \
                     --data "$vpayload")"
          case "$vcode" in
            2??) : ;;
            *)   echo "viewer HTTP $vcode: $(head -c 200 "$tmpv")" >&2; rm -f "$tmpv"; exit 22 ;;
          esac
          login="$(python - <<'PY' <"$tmpv"
import json,sys
d=json.load(sys.stdin)
print((d.get("data",{}) or {}).get("viewer",{}).get("login",""))
PY
          )"
          rm -f "$tmpv"
        fi
        [ -n "$login" ] || { echo "no login provided and token did not resolve viewer.login" >&2; exit 2; }

        today="$(date +%F)"
        from="$(date -d '6 days ago' +%F)"
        export LOGIN="$login" FROM="$from" TO="$today"

        payload="$(python - <<'PY'
import os, json
login = os.environ.get("LOGIN","")
start = os.environ.get("FROM","")
end   = os.environ.get("TO","")
query = ("query($login:String!, $from:DateTime!, $to:DateTime!)"
         "{ user(login:$login){ login contributionsCollection(from:$from, to:$to){"
         " contributionCalendar{ weeks{ contributionDays{ date color contributionCount } } } } } }")
print(json.dumps({"query": query,
                  "variables": {"login": login,
                                "from": f"{start}T00:00:00Z",
                                "to":   f"{end}T23:59:59Z"}}))
PY
        )"

        tmp="$(mktemp)"
        code="$(curl -sS -o "$tmp" -w "%{http_code}" \
                 -H "Authorization: bearer $GITHUB_TOKEN" \
                 -H "Content-Type: application/json" \
                 -X POST https://api.github.com/graphql \
                 --data "$payload")"
        case "$code" in
          2??) cat "$tmp" ;;
          *)   echo "http $code: $(head -c 200 "$tmp")" >&2; rm -f "$tmp"; exit 22 ;;
        esac
        rm -f "$tmp"
    `]

        onExited: code => {
            if (code !== 0) {
                const msg = root.redact(err.text || ("fetch failed (exit " + code + ")"));
                root.lastError = msg;
                console.error("[GitHubWidget] " + msg);
                return;
            }
            const raw = out.text.trim();
            try {
                const obj = JSON.parse(raw);
                if (obj.errors) {
                    const m = obj.errors.map(e => e.message).join("; ");
                    root.lastError = m;
                    console.error("[GitHubWidget] " + m);
                    return;
                }
                root.username = (obj.data && obj.data.user && obj.data.user.login) || root.username;

                const weeks = obj.data.user.contributionsCollection.contributionCalendar.weeks || [];
                const days = [];
                weeks.forEach(w => w.contributionDays.forEach(d => days.push({
                            date: d.date,
                            count: d.contributionCount
                        })));

                const now = new Date();
                now.setHours(0, 0, 0, 0);
                const start = new Date(now);
                start.setDate(now.getDate() - 6);
                function fmt(d) {
                    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
                }
                const dates = [];
                for (var i = 0; i < 7; i++) {
                    const t = new Date(start);
                    t.setDate(start.getDate() + i);
                    dates.push(fmt(t));
                }

                var byDate = {};
                days.forEach(function (d) {
                    byDate[d.date] = d;
                });
                var window = dates.map(function (dt) {
                    return byDate[dt] || {
                        date: dt,
                        count: 0
                    };
                });

                var palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"];
                var max = 1;
                for (i = 0; i < window.length; i++)
                    if (window[i].count > max)
                        max = window[i].count;

                for (i = 0; i < window.length; i++) {
                    var c = window[i].count;
                    var idx = (c === 0) ? 0 : Math.min(4, 1 + Math.floor((c * 4) / max));
                    window[i] = {
                        date: window[i].date,
                        count: c,
                        color: palette[idx]
                    };
                }

                root.weekDays = window;
                root.total = window.reduce((a, b) => a + (b.count || 0), 0);
                root.lastError = "";

                GithubStore.days = window;
                GithubStore.total = root.total;
                GithubStore.username = root.username;
                GithubStore.lastError = root.lastError;
            } catch (e) {
                const msg = "parse error: " + e + " | first 200B: " + raw.slice(0, 200);
                root.lastError = msg;
                console.error("[GitHubWidget] " + msg);
            }
        }
    }

    Timer {
        interval: root.refreshInterval * 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: proc.exec(proc.command)
    }
}
