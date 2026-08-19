import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// 人数菜单：1 名 / 3 名 / 5 名同学（由后端 showAt 定位后弹出）

Window {
    id: menuWin
    objectName: "menuWin"
    width: 132
    height: 4 + 36 * 3 + 4
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    visible: false
    color: "transparent"

    // 点击菜单以外的任意位置（菜单失焦）自动关闭
    onActiveChanged: {
        if (!active) menuWin.hide()
    }

    function showAt(x, y) {
        var sw = Screen.desktopAvailableWidth
        var sh = Screen.desktopAvailableHeight
        var mx = x
        var my = y
        // 右侧放不下则换到左侧；底部放不下则换到上方；并保证不超出屏幕
        if (mx + menuWin.width > sw) mx = x - menuWin.width - 8
        if (my + menuWin.height > sh) my = y - menuWin.height - 8
        mx = Math.max(0, Math.min(mx, sw - menuWin.width))
        my = Math.max(0, Math.min(my, sh - menuWin.height))
        menuWin.x = mx
        menuWin.y = my
        menuWin.show()
        menuWin.raise()
        menuWin.requestActivate()
    }

    // 后端按钮点击 → 信号 → 本窗口定位弹出
    Connections {
        target: backend
        function onMenuRequested(x, y) { showAt(x, y) }
    }

    Rectangle {
        anchors.fill: parent
        radius: 8
        color: "#F5FFFFFF"
        border.color: "#66888888"
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 2

            Repeater {
                model: [1, 3, 5]
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    radius: 4
                    color: "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: modelData + " 名同学"
                        color: "#222222"
                        font.pixelSize: 14
                    }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: parent.color = "#E3E3E3"
                        onExited: parent.color = "transparent"
                        onClicked: {
                            menuWin.hide()
                            if (backend) backend.requestRoll(modelData)
                        }
                    }
                }
            }
        }
    }
}
