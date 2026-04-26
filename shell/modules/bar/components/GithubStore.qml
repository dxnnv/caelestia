pragma Singleton
import QtQuick

QtObject {
    id: store
    property var days: []
    property int total: 0
    property string username: ""
    property string lastError: ""
}
