import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import RinUI
import ClassWidgets.Plugins

// 随机点名主程序设置页（参考 TTS 服务插件设计：PluginPage + SettingCard）
PluginPage {
    id: root
    pluginId: "com.rollcall"
    title: "随机点名"

    property bool visibleValue: true
    property int btnWidthValue: 52
    property int btnHeightValue: 40
    property int animSecondsValue: 3
    property int countValue: 0
    property var rosterPreview: []
    property bool ready: false

    function stepWidth(delta) {
        var v = Math.max(40, Math.min(160, root.btnWidthValue + delta))
        root.btnWidthValue = v
        if (root.ready && backend) backend.setButtonWidth(v)
    }

    function stepHeight(delta) {
        var v = Math.max(30, Math.min(100, root.btnHeightValue + delta))
        root.btnHeightValue = v
        if (root.ready && backend) backend.setButtonHeight(v)
    }

    function stepAnimSeconds(delta) {
        var v = Math.max(1, Math.min(10, root.animSecondsValue + delta))
        root.animSecondsValue = v
        if (root.ready && backend) backend.setAnimationSeconds(v)
    }

    // 只更新数据属性；各控件通过绑定/信号连接自行同步显示
    function loadFromBackend() {
        if (!backend) return
        let cfg = backend.getConfig()
        visibleValue = cfg.window_visible !== undefined ? cfg.window_visible : true
        btnWidthValue = cfg.button_width || 52
        btnHeightValue = cfg.button_height || 40
        animSecondsValue = cfg.animation_seconds || 3
        countValue = backend.getRosterCount()
        rosterPreview = backend.getRoster()
        ready = true
    }

    Component.onCompleted: loadFromBackend()

    Connections {
        target: backend
        function onConfigChanged() { loadFromBackend() }
        function onRosterChanged() {
            countValue = backend.getRosterCount()
            rosterPreview = backend.getRoster()
        }
    }

    FileDialog {
        id: rosterDialog
        title: "选择名单文件（txt 或 Word）"
        nameFilters: ["名单文件 (*.txt *.docx)", "文本文件 (*.txt)", "Word 文档 (*.docx)", "所有文件 (*)"]
        onAccepted: {
            if (backend) backend.importRoster(rosterDialog.selectedFile)
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        Text {
            text: "点名按钮"
            font.bold: true
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_alert_20_regular"
            title: "显示点名按钮"
            description: "打开后桌面显示\"点名\"小按钮（可拖动、置顶），关闭后隐藏。"

            Switch {
                checked: root.visibleValue
                onCheckedChanged: {
                    root.visibleValue = checked
                    if (root.ready) backend.setWindowVisible(checked)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_timer_20_regular"
            title: "按钮大小"
            description: "点名按钮的宽度与高度（像素），点 +/- 调整，实时生效。"

            ColumnLayout {
                spacing: 6

                RowLayout {
                    spacing: 8
                    Text { text: "宽" }
                    Button {
                        text: "−"
                        implicitWidth: 30
                        implicitHeight: 28
                        onClicked: root.stepWidth(-4)
                    }
                    Text {
                        Layout.preferredWidth: 52
                        horizontalAlignment: Text.AlignHCenter
                        text: root.btnWidthValue + " px"
                        font.bold: true
                    }
                    Button {
                        text: "+"
                        implicitWidth: 30
                        implicitHeight: 28
                        onClicked: root.stepWidth(4)
                    }
                }

                RowLayout {
                    spacing: 8
                    Text { text: "高" }
                    Button {
                        text: "−"
                        implicitWidth: 30
                        implicitHeight: 28
                        onClicked: root.stepHeight(-4)
                    }
                    Text {
                        Layout.preferredWidth: 52
                        horizontalAlignment: Text.AlignHCenter
                        text: root.btnHeightValue + " px"
                        font.bold: true
                    }
                    Button {
                        text: "+"
                        implicitWidth: 30
                        implicitHeight: 28
                        onClicked: root.stepHeight(4)
                    }
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_timer_20_regular"
            title: "随机动画时长"
            description: "点名时名字滚动的秒数（1–10 秒），点 +/- 调整，下次点名生效。"

            RowLayout {
                spacing: 8
                Button {
                    text: "−"
                    implicitWidth: 30
                    implicitHeight: 28
                    onClicked: root.stepAnimSeconds(-1)
                }
                Text {
                    Layout.preferredWidth: 60
                    horizontalAlignment: Text.AlignHCenter
                    text: root.animSecondsValue + " 秒"
                    font.bold: true
                }
                Button {
                    text: "+"
                    implicitWidth: 30
                    implicitHeight: 28
                    onClicked: root.stepAnimSeconds(1)
                }
            }
        }

        Text {
            text: "名单"
            font.bold: true
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_clock_20_regular"
            title: "导入名单"
            description: "支持 txt 或 Word（.docx）文件；每行一个名字，可带“1.小明”式序号，导入后自动去除。当前名单：" + root.countValue + " 人"

            RowLayout {
                spacing: 8
                Button {
                    text: "选择文件..."
                    onClicked: rosterDialog.open()
                }
                Button {
                    text: "清空名单"
                    onClicked: {
                        if (backend) backend.clearRoster()
                    }
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_class_20_regular"
            title: "名单预览"
            description: root.rosterPreview.length > 0 ? "已导入 " + root.rosterPreview.length + " 个名字（不含序号）" : "尚未导入名单"

            TextArea {
                id: previewArea
                Layout.fillWidth: true
                Layout.preferredHeight: 140
                readOnly: true
                wrapMode: TextArea.Wrap
                text: root.rosterPreview.join("\n")
            }
            // 空名单时的浅色提示（说明名单整理格式）
            Text {
                anchors.fill: previewArea
                visible: root.rosterPreview.length === 0
                text: "请将名单整理为每行一个名字，\n再点击“选择文件...”导入：\n\n1.小明\n2.小红\n张三\n\n可带序号，导入时自动去除；\n一行多个名字可用逗号/顿号分隔"
                color: "#AAAAAA"
                font.pixelSize: 13
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.Wrap
            }
        }

        Text {
            text: "测试"
            font.bold: true
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_play_20_regular"
            title: "测试抽取"
            description: "立即随机抽取一名同学（使用与点名相同的洗牌队列，不重复）。"

            RowLayout {
                spacing: 8
                Button {
                    text: "抽取一个"
                    onClicked: {
                        if (backend) {
                            var arr = backend.pickBatch(1)
                            pickResult.text = arr.length > 0 ? arr[0] : "名单为空"
                        }
                    }
                }
                Text {
                    id: pickResult
                    text: "（点击抽取查看）"
                    color: "#888888"
                }
            }
            Connections {
                target: backend
                function onRosterChanged() { }
            }
        }
    }
}
