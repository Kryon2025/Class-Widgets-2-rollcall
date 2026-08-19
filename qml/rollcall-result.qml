import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// 点名结果窗口：无边框 + 自绘标题栏（拖动窗口）+ 右下角缩放手柄 + 底部按钮
// 名字随机滚动 3 秒（可配置）后定格（多人纵列）

Window {
    id: resultWin
    objectName: "resultWin"
    title: "随机点名结果"
    width: 420
    height: 300
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    visible: false
    color: "transparent"

    property int rollCount: 1
    property var rollList: []
    property bool rolling: false

    Rectangle {
        anchors.fill: parent
        radius: 6
        color: "white"
        border.color: "#CCCCCC"
        border.width: 1

        // 自绘标题栏：拖动窗口 + 关闭
        Rectangle {
            id: titleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 32
            radius: 6

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                text: "随机点名结果"
                color: "#333333"
                font.bold: true
                font.pixelSize: 13
            }

            Rectangle {
                id: closeBtn
                width: 28
                height: 28
                anchors.right: parent.right
                anchors.rightMargin: 3
                anchors.verticalCenter: parent.verticalCenter
                radius: 4
                color: "transparent"

                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: "#555555"
                    font.pixelSize: 14
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: parent.color = "#DDDDDD"
                    onExited: parent.color = "transparent"
                    onClicked: {
                        resultWin.stopRoll()
                        resultWin.hide()
                    }
                }
            }

            // 标题栏拖动
            property int _dragX: 0
            property int _dragY: 0
            MouseArea {
                anchors.fill: parent
                onPressed: {
                    titleBar._dragX = mouse.x
                    titleBar._dragY = mouse.y
                }
                onPositionChanged: {
                    resultWin.x = resultWin.x + mouse.x - titleBar._dragX
                    resultWin.y = resultWin.y + mouse.y - titleBar._dragY
                }
            }
        }

        // 名字纵列（滚动期随机切换，停止后定格）
        Column {
            id: namesCol
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: titleBar.bottom
            anchors.bottom: btnBar.top
            anchors.leftMargin: 24
            anchors.rightMargin: 24
            anchors.topMargin: 12
            anchors.bottomMargin: 8
            spacing: 6

            Repeater {
                id: nameRepeater
                model: resultWin.rollList
                delegate: Text {
                    width: namesCol.width
                    text: modelData
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    font.pixelSize: resultWin.rollCount <= 1 ? 56 :
                                    resultWin.rollCount <= 3 ? 44 : 34
                    font.bold: true
                    color: "#222222"
                }
            }
        }

        // 底部按钮行：再次抽取 1/2/3 名 + 确定
        RowLayout {
            id: btnBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 10
            spacing: 8

            Repeater {
                model: [1, 2, 3]
                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    radius: 5
                    color: "#EEEEEE"
                    border.color: "#CCCCCC"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "再抽" + modelData + "名"
                        color: "#222222"
                        font.pixelSize: 13
                    }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: parent.color = "#DDDDDD"
                        onExited: parent.color = "#EEEEEE"
                        onClicked: {
                            if (backend) backend.requestRoll(modelData)
                        }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 72
                Layout.preferredHeight: 32
                radius: 5
                color: "#4090FF"
                border.color: "#3380EE"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "确定"
                    color: "white"
                    font.bold: true
                    font.pixelSize: 13
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: parent.color = "#3580EE"
                    onExited: parent.color = "#4090FF"
                    onClicked: {
                        resultWin.stopRoll()
                        resultWin.hide()
                    }
                }
            }
        }

        // 右下角缩放手柄（拖动调整窗口大小）
        Rectangle {
            id: resizeHandle
            width: 18
            height: 18
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            color: "transparent"

            // 两条斜线示意
            Rectangle {
                width: 10; height: 2; rotation: -45
                anchors.right: parent.right; anchors.rightMargin: 2
                anchors.bottom: parent.bottom; anchors.bottomMargin: 6
                color: "#999999"
            }
            Rectangle {
                width: 6; height: 2; rotation: -45
                anchors.right: parent.right; anchors.rightMargin: 5
                anchors.bottom: parent.bottom; anchors.bottomMargin: 2
                color: "#BBBBBB"
            }

            property int _sx: 0
            property int _sy: 0
            MouseArea {
                anchors.fill: parent
                onPressed: {
                    resizeHandle._sx = mouse.x
                    resizeHandle._sy = mouse.y
                }
                onPositionChanged: {
                    var dw = mouse.x - resizeHandle._sx
                    var dh = mouse.y - resizeHandle._sy
                    resultWin.width = Math.max(320, resultWin.width + dw)
                    resultWin.height = Math.max(240, resultWin.height + dh)
                }
            }
        }
    }

    // 滚动：60ms 随机换一批名字
    Timer {
        id: rollTimer
        interval: 60
        repeat: true
        onTriggered: {
            var roster = backend.roster
            if (roster.length === 0) return
            var arr = []
            for (var i = 0; i < resultWin.rollCount; i++) {
                arr.push(roster[Math.floor(Math.random() * roster.length)])
            }
            resultWin.rollList = arr
        }
    }

    // 由 backend.animationSeconds 决定滚动时长（秒，可配置）
    Timer {
        id: stopTimer
        interval: backend.animationSeconds * 1000
        onTriggered: {
            rollTimer.stop()
            resultWin.rolling = false
            resultWin.rollList = backend.pickBatch(resultWin.rollCount)
        }
    }

    // 由后端 rollRequested 信号触发（人数由信号参数传递）
    function startRoll(count) {
        if (rolling) return
        rollCount = Math.max(1, Math.min(5, count))
        if (backend.roster.length === 0) {
            rollList = ["请先在插件设置中导入名单"]
            show()
            raise()
            return
        }
        rolling = true
        show()
        raise()
        rollTimer.start()
        stopTimer.start()
    }

    function stopRoll() {
        rollTimer.stop()
        stopTimer.stop()
        rolling = false
    }

    Connections {
        target: backend
        function onRollRequested(n) { startRoll(n) }
    }

    // 拖动/缩放结束后防抖保存位置（重启自动恢复）
    Timer {
        id: posSaveTimer
        interval: 500
        onTriggered: {
            if (backend) backend.saveWindowPos("resultWin", resultWin.x, resultWin.y)
        }
    }
    onXChanged: posSaveTimer.restart()
    onYChanged: posSaveTimer.restart()
}
