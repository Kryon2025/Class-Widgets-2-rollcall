import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// 点名小按钮（浮窗）
// 左键点击 → 人数菜单；左键拖动 → 移动位置；右键 → 快捷设置面板
//
// 注意 1：本窗口的 visible 完全由 Python 侧控制，QML 不做绑定，
//         否则切换配置时会把已收起的按钮重新弹出来。
// 注意 2：**不要**使用 Qt.WindowDoesNotAcceptFocus。该标志（WS_EX_NOACTIVATE）
//         会让窗口收不到鼠标点击，按钮既拖不动也点不出菜单。
// 注意 3：两个菜单都用 popupType: Popup.Window —— 按钮窗口只有 60x44，
//         Item 类型的 Popup 会被窗口边界裁掉；Window 类型可超出且由 Qt 自动
//         处理屏幕边缘，不需要自己算坐标。

Window {
    id: buttonWin
    objectName: "buttonWin"
    width: 60
    height: 44
    // Qt.Tool 不显示任务栏（与桌面一言一致）；不要用 WindowDoesNotAcceptFocus
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"

    // 拖动 / 点击判定
    property real _grabX: 0
    property real _grabY: 0
    property real _startGX: 0
    property real _startGY: 0
    property bool _dragging: false

    Rectangle {
        id: face
        anchors.fill: parent
        radius: Math.min(width, height) * ((backend && backend.floatMode) ? 0.34 : 0.22)
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#E6405A8F" }
            GradientStop {
                position: 1.0
                color: (backend && backend.floatMode) ? "#D92A3B63" : "#CC333333"
            }
        }
        border.width: (backend && backend.floatMode) ? 1 : 0
        border.color: "#59FFFFFF"
        opacity: (mouse.pressed && !buttonWin._dragging) ? 0.82 : 1.0

        Behavior on opacity { NumberAnimation { duration: 90 } }
        Behavior on radius { NumberAnimation { duration: 130 } }

        Text {
            id: label
            anchors.centerIn: parent
            text: "点名"
            color: "white"
            font.bold: true
            font.pixelSize: Math.max(11, Math.min(20, face.height * 0.42))
            style: Text.Outline
            styleColor: "#33000000"
        }

        MouseArea {
            id: mouse
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            cursorShape: buttonWin._dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor

            onPressed: function (m) {
                // 菜单打开时先收起：Popup.Window 会抓取鼠标，干扰拖动坐标换算
                if (countPanel.opened) countPanel.close()
                if (quickPanel.opened) quickPanel.close()
                var g = mouse.mapToGlobal(m.x, m.y)
                buttonWin._grabX = g.x - buttonWin.x
                buttonWin._grabY = g.y - buttonWin.y
                buttonWin._startGX = g.x
                buttonWin._startGY = g.y
                buttonWin._dragging = false
            }

            onPositionChanged: function (m) {
                var g = mouse.mapToGlobal(m.x, m.y)
                if (!buttonWin._dragging
                    && (Math.abs(g.x - buttonWin._startGX) > 3 || Math.abs(g.y - buttonWin._startGY) > 3))
                    buttonWin._dragging = true
                if (buttonWin._dragging) {
                    // 绝对定位：窗口 = 鼠标全局坐标 - 按下时的抓取偏移，跟手、无累积误差
                    // 再限制在虚拟桌面内，防止异常坐标把按钮拖出可视区域（表现为「按钮消失」）
                    var nx = g.x - buttonWin._grabX
                    var ny = g.y - buttonWin._grabY
                    var vw = Screen.virtualWidth
                    var vh = Screen.virtualHeight
                    if (vw > 0 && vh > 0) {
                        nx = Math.max(Screen.virtualX, Math.min(nx, Screen.virtualX + vw - buttonWin.width))
                        ny = Math.max(Screen.virtualY, Math.min(ny, Screen.virtualY + vh - buttonWin.height))
                    }
                    buttonWin.x = nx
                    buttonWin.y = ny
                }
            }

            onReleased: function (m) {
                if (buttonWin._dragging) {
                    posSaveTimer.restart()
                    return
                }
                if (m.button === Qt.RightButton)
                    quickPanel.open()
                else
                    countPanel.open()
            }
        }
    }

    // ── 人数菜单（左键）──────────────────────────────────────
    Popup {
        id: countPanel
        popupType: Popup.Window
        width: 224
        padding: 10
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        x: buttonWin.width + 4
        y: 0

        function choose(n) {
            close()
            if (backend)
                backend.requestRoll(n)
        }

        // 打开后再定位：靠屏幕边缘时翻转到按钮另一侧，避免重叠或超出屏幕
        onOpened: {
            try {
                var scr = Screen.availableVirtualGeometry
                if (scr.width > 0 && buttonWin.x + buttonWin.width + 4 + width > scr.x + scr.width)
                    x = -width - 4
                else
                    x = buttonWin.width + 4
                if (scr.height > 0 && buttonWin.y + height > scr.y + scr.height)
                    y = buttonWin.height - height
                else
                    y = 0
            } catch (e) {}
        }

        background: Rectangle {
            radius: 14
            color: "#F21E1E1E"
            border.width: 1
            border.color: "#33FFFFFF"
        }

        contentItem: ColumnLayout {
            spacing: 5

            Text {
                text: "抽取人数"
                color: "#8CFFFFFF"
                font.pixelSize: 10
                Layout.leftMargin: 4
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: [1, 2, 3]

                    delegate: Rectangle {
                        required property int modelData

                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        radius: 10
                        color: cmouse.pressed ? "#505A8F"
                               : (cmouse.containsMouse ? "#40405A8F" : "#1AFFFFFF")
                        border.width: 1
                        border.color: cmouse.containsMouse ? "#805A9BFF" : "#22FFFFFF"
                        scale: cmouse.pressed ? 0.96 : 1.0

                        Behavior on color { ColorAnimation { duration: 90 } }
                        Behavior on scale { NumberAnimation { duration: 90 } }

                        Text {
                            anchors.centerIn: parent
                            text: modelData + " 名"
                            color: cmouse.containsMouse ? "#FFFFFF" : "#E6FFFFFF"
                            font.bold: true
                            font.pixelSize: 14
                        }

                        MouseArea {
                            id: cmouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: countPanel.choose(modelData)
                        }
                    }
                }
            }
        }
    }

    // ── 快捷设置面板（右键）──────────────────────────────────
    Popup {
        id: quickPanel
        popupType: Popup.Window
        width: 208
        padding: 10
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        x: buttonWin.width + 6
        y: 0

        onOpened: {
            try {
                var scr = Screen.availableVirtualGeometry
                if (scr.width > 0 && buttonWin.x + buttonWin.width + 6 + width > scr.x + scr.width)
                    x = -width - 6
                else
                    x = buttonWin.width + 6
                if (scr.height > 0 && buttonWin.y + height > scr.y + scr.height)
                    y = buttonWin.height - height
                else
                    y = 0
            } catch (e) {}
        }

        background: Rectangle {
            radius: 12
            color: "#F21E1E1E"
            border.width: 1
            border.color: "#33FFFFFF"
        }

        contentItem: ColumnLayout {
            spacing: 6

            Text {
                text: "快捷设置"
                color: "#9FFFFFFF"
                font.pixelSize: 11
                Layout.bottomMargin: 2
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text { text: "浮窗模式"; color: "white"; font.pixelSize: 12; Layout.fillWidth: true }
                Switch {
                    checked: backend ? backend.floatMode : true
                    onToggled: if (backend) backend.setFloatMode(checked)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text { text: "点击后隐藏"; color: "white"; font.pixelSize: 12; Layout.fillWidth: true }
                Switch {
                    checked: backend ? backend.clickHide : false
                    onToggled: if (backend) backend.setClickHide(checked)
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Button {
                    Layout.fillWidth: true
                    text: "收起按钮"
                    onClicked: {
                        quickPanel.close()
                        if (backend) backend.hideButton()
                    }
                }
                Button {
                    Layout.fillWidth: true
                    text: "设置页"
                    onClicked: {
                        quickPanel.close()
                        if (backend) backend.openSettings()
                    }
                }
            }
        }
    }

    // 拖动结束后防抖保存位置（后端会顺带把越界的位置拉回屏幕内）
    Timer {
        id: posSaveTimer
        interval: 400
        onTriggered: {
            if (backend)
                backend.saveWindowPos("buttonWin", buttonWin.x, buttonWin.y)
        }
    }
}
