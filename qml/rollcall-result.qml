import QtQuick
import QtQuick.Layouts
import QtQuick.Window

// 点名结果窗口：标准 Windows 系统窗口（标题栏 + 四边四角可拖调整大小）+ 底部按钮
// 名字随机滚动（时长可配置）后定格（多人纵列）

Window {
    id: resultWin
    objectName: "resultWin"
    title: "随机点名结果"
    width: 420
    height: 300
    // 完整系统窗口标志：标题栏/系统菜单/最小化最大化关闭按钮 + 置顶
    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
           | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
           | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
    visible: false
    color: "white"

    property int rollCount: 1
    property var rollList: []
    property bool rolling: false

    // 名字纵列（滚动期随机切换，停止后定格）
    Column {
        id: namesCol
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
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

    // 窗口被关闭/隐藏（如点系统 X）时立即停止滚动，保证下次点名不被吞掉
    onVisibleChanged: {
        if (!visible) resultWin.stopRoll()
    }

    // 拖动结束后防抖保存位置（重启自动恢复）
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
