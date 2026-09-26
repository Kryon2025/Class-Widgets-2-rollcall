import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// 点名结果窗口（卡片模式）：名字滚动后定格，支持"提前结束"。
// 由 backend.rollRequested(count) 触发；backend.stopRequested() 可提前结束。

Window {
    id: resultWin
    objectName: "resultWin"
    width: 420
    height: 300
    minimumWidth: 280
    minimumHeight: 160
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"
    visible: false

    property var picked: []        // 本次真正抽中的名字
    property var shown: []         // 屏幕上正在显示的名字（滚动中会闪烁）
    property bool rolling: false
    property bool settled: false
    property real grabX: 0         // 拖动抓取偏移
    property real grabY: 0

    // ── 通用按钮样式（半透明胶囊；primary 用主题色）──────────
    component PillButton: Button {
        id: ctrl
        property bool primary: false
        leftPadding: 14
        rightPadding: 14
        implicitHeight: 34

        background: Rectangle {
            radius: 10
            color: ctrl.hovered
                   ? (ctrl.primary ? "#B3405A8F" : "#33FFFFFF")
                   : (ctrl.primary ? "#E6405A8F" : "#1FFFFFFF")
            border.width: 1
            border.color: ctrl.primary ? "#80405A8F" : "#2AFFFFFF"
            Behavior on color { ColorAnimation { duration: 120 } }
        }
        contentItem: Text {
            text: ctrl.text
            color: "white"
            font.pixelSize: 13
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    // ── 滚动动画 ────────────────────────────────────────────
    Timer {
        id: flicker
        interval: 60
        repeat: true
        onTriggered: {
            var pool = backend ? backend.roster : []
            if (!pool || pool.length === 0)
                return
            var out = []
            for (var i = 0; i < Math.max(1, resultWin.picked.length); i++)
                out.push(pool[Math.floor(Math.random() * pool.length)])
            resultWin.shown = out
        }
    }

    Timer {
        id: settle
        repeat: false
        onTriggered: resultWin.finish()
    }

    function finish() {
        flicker.stop()
        settle.stop()
        resultWin.rolling = false
        resultWin.settled = true
        resultWin.shown = resultWin.picked
        if (backend) backend.onPicked(resultWin.picked)
    }

    function dismiss() {
        flicker.stop()
        settle.stop()
        resultWin.rolling = false
        resultWin.visible = false
    }

    function startRoll(count) {
        flicker.stop()
        settle.stop()
        resultWin.settled = false
        resultWin.rolling = false

        var picked = backend ? backend.pickBatch(count) : []
        resultWin.picked = picked
        resultWin.shown = picked

        // 先显示窗口，避免任何异常导致"点了没反应"
        resultWin.visible = true

        if (!picked || picked.length === 0) {
            resultWin.shown = ["名单为空，请先导入"]
            resultWin.settled = true
            return
        }

        resultWin.rolling = true
        flicker.start()
        settle.interval = (backend ? Math.max(1, backend.animationSeconds) : 3) * 1000
        settle.restart()
    }

    Behavior on opacity { NumberAnimation { duration: 200 } }
    opacity: visible ? 1 : 0

    // ── 卡片外观 ────────────────────────────────────────────
    Rectangle {
        id: card
        anchors.fill: parent
        radius: 18
        color: "#F21A1A24"
        border.width: 1
        border.color: "#40FFFFFF"

        // 拖动（绝对定位，跟手）
        MouseArea {
            id: dragArea
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton
            cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
            onPressed: function (m) {
                var g = dragArea.mapToGlobal(m.x, m.y)
                resultWin.grabX = g.x - resultWin.x
                resultWin.grabY = g.y - resultWin.y
            }
            onPositionChanged: function (m) {
                var g = dragArea.mapToGlobal(m.x, m.y)
                resultWin.x = g.x - resultWin.grabX
                resultWin.y = g.y - resultWin.grabY
            }
            onReleased: if (backend) backend.saveWindowPos("resultWin", resultWin.x, resultWin.y)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12

            // 标题行
            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: resultWin.rolling ? "点名中…" : (resultWin.settled ? "点名结果" : "随机点名")
                    color: "#B3FFFFFF"
                    font.pixelSize: 13
                    font.bold: true
                    Layout.fillWidth: true
                }
                Text {
                    text: "拖动移动 · 右下角缩放"
                    color: "#59FFFFFF"
                    font.pixelSize: 10
                }
            }

            // 名字区域
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Column {
                    anchors.centerIn: parent
                    spacing: resultWin.shown.length > 1 ? 8 : 0

                    Repeater {
                        model: resultWin.shown
                        delegate: Text {
                            required property string modelData
                            horizontalAlignment: Text.AlignHCenter
                            text: modelData
                            color: resultWin.settled && !resultWin.rolling ? "#FFE08A" : "white"
                            font.bold: true
                            font.pixelSize: resultWin.shown.length > 3 ? 34 : 48
                            style: Text.Outline
                            styleColor: "#40000000"
                            // 结束时从略大弹回原尺寸，形成定格回弹
                            scale: resultWin.settled && !resultWin.rolling ? 1.0 : 1.05
                            Behavior on scale {
                                NumberAnimation { duration: 260; easing.type: Easing.OutBack }
                            }
                        }
                    }
                }
            }

            // 按钮行：点名中只有「提前结束」；结束后右移并淡入再点按钮
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 40

                Row {
                    id: againRow
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8
                    // 用 opacity 做渐隐；始终可见但透明时禁用点击，
                    // 这样点「再点」时能平滑淡出而不是瞬间消失
                    opacity: resultWin.settled && !resultWin.rolling ? 1 : 0
                    enabled: resultWin.settled && !resultWin.rolling
                    Behavior on opacity { NumberAnimation { duration: 220 } }

                    Repeater {
                        model: [1, 2, 3]
                        delegate: PillButton {
                            required property int modelData
                            text: "再点" + modelData + "名"
                            onClicked: if (backend) backend.requestRoll(modelData)
                        }
                    }
                }

                PillButton {
                    id: endBtn
                    anchors.verticalCenter: parent.verticalCenter
                    // 点名中居中（名字正下方）；结束后移到最右
                    x: (resultWin.settled && !resultWin.rolling) ? parent.width - width
                                                                : (parent.width - width) / 2
                    // 始终对 x 做动画：结束后右移、点「再点」时再左移回来
                    Behavior on x { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
                    text: resultWin.rolling ? "提前结束" : "结束"
                    primary: !resultWin.rolling
                    onClicked: {
                        if (resultWin.rolling)
                            resultWin.finish()
                        else
                            resultWin.dismiss()
                    }
                }
            }
        }

        // 右下角缩放手柄
        MouseArea {
            width: 18
            height: 18
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            cursorShape: Qt.SizeFDiagCursor
            property real rx: 0
            property real ry: 0
            property real hx: 0
            property real hy: 0
            onPressed: function (m) { rx = resultWin.width; ry = resultWin.height; hx = m.x; hy = m.y }
            onPositionChanged: function (m) {
                resultWin.width = Math.max(resultWin.minimumWidth, rx + (m.x - hx))
                resultWin.height = Math.max(resultWin.minimumHeight, ry + (m.y - hy))
            }
            onReleased: if (backend) backend.saveWindowPos("resultWin", resultWin.x, resultWin.y)

            Rectangle {
                anchors.fill: parent
                anchors.margins: 3
                color: "transparent"
                border.width: 2
                border.color: "#59FFFFFF"
                radius: 2
            }
        }
    }

    Connections {
        target: backend
        function onRollRequested(count) { resultWin.startRoll(count) }
        function onStopRequested() { if (resultWin.rolling) resultWin.finish() }
    }
}
