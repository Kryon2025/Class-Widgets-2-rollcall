import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// 点名小按钮：只显示"点名"，可拖动，点击弹出人数菜单

Window {
    id: buttonWin
    objectName: "buttonWin"
    width: backend.buttonWidth
    height: backend.buttonHeight
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
    visible: backend.windowVisible
    color: "transparent"

    // 拖动 / 点击判定
    property int _dragX: 0
    property int _dragY: 0
    property bool _dragging: false

    Rectangle {
        anchors.fill: parent
        radius: Math.min(width, height) * 0.25
        color: "#CC333333"
        border.color: "#66FFFFFF"
        border.width: 1

        Text {
            anchors.centerIn: parent
            text: "点名"
            color: "white"
            font.bold: true
            font.pixelSize: Math.max(12, Math.min(20, parent.height * 0.45))
        }

        MouseArea {
            anchors.fill: parent
            onPressed: {
                _dragX = mouse.x
                _dragY = mouse.y
                _dragging = false
            }
            onPositionChanged: {
                var dx = mouse.x - _dragX
                var dy = mouse.y - _dragY
                if (Math.abs(dx) > 4 || Math.abs(dy) > 4) _dragging = true
                if (_dragging) {
                    var nx = buttonWin.x + dx
                    var ny = buttonWin.y + dy
                    // 钳制在屏幕可用区域内，避免拖出屏幕后找不到按钮
                    var scr = Screen.availableVirtualGeometry
                    buttonWin.x = Math.max(scr.x, Math.min(nx, scr.x + scr.width - buttonWin.width))
                    buttonWin.y = Math.max(scr.y, Math.min(ny, scr.y + scr.height - buttonWin.height))
                }
            }
            onReleased: {
                if (!_dragging && backend) backend.showMenu(buttonWin.x + buttonWin.width + 4, buttonWin.y)
            }
        }
    }

    // 拖动结束后防抖保存位置（重启自动恢复）
    Timer {
        id: posSaveTimer
        interval: 500
        onTriggered: {
            if (backend) backend.saveWindowPos("buttonWin", buttonWin.x, buttonWin.y)
        }
    }
    onXChanged: posSaveTimer.restart()
    onYChanged: posSaveTimer.restart()
}
