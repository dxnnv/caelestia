pragma Singleton
import QtQuick
import Qt.labs.settings as Labs

Labs.Settings {
    id: s
    category: "caelestia"
    property string hiddenAppsJson: "[]"

    property var list: JSON.parse(s.hiddenAppsJson)

    function _commit(arr) {
        list = arr;
        s.hiddenAppsJson = JSON.stringify(arr);
    }

    function add(id) {
        if (list.includes(id))
            return;
        _commit(list.concat(id));
    }

    function remove(id) {
        _commit(list.filter(x => x !== id));
    }

    function has(id) {
        return list.includes(id);
    }
}
