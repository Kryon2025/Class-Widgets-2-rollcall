import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import RinUI
import ClassWidgets.Plugins

// 随机点名主程序设置页（PluginPage + SettingCard 结构，参考 TTS 服务插件）
PluginPage {
    id: root
    pluginId: "com.rollcall"
    title: "随机点名"

    property bool visibleValue: true
    property bool floatValue: true
    property bool clickHideValue: false
    property bool noRepeatValue: true
    property bool luckValue: false
    property string modeValue: "roll"
    property int notifySecondsValue: 4
    property int btnWidthValue: 52
    property int btnHeightValue: 40
    property int animSecondsValue: 3
    property int countValue: 0
    property var rosterPreview: []
    property var weightsMap: ({})
    property string newName: ""
    property string pickResultText: "（点击抽取查看）"
    property bool ready: false
    property bool isSecrandom: false   // 当前是否把点名交给 SecRandom

    function step(field, delta, lo, hi) {
        var v = Math.max(lo, Math.min(hi, root[field] + delta))
        root[field] = v
        return v
    }

    function stepWidth(d) { if (root.ready && backend) backend.setButtonWidth(root.step("btnWidthValue", d, 40, 160)) }
    function stepHeight(d) { if (root.ready && backend) backend.setButtonHeight(root.step("btnHeightValue", d, 30, 100)) }
    function stepAnim(d) { if (root.ready && backend) backend.setAnimationSeconds(root.step("animSecondsValue", d, 1, 10)) }
    function stepNotify(d) { if (root.ready && backend) backend.setNotifyDuration(root.step("notifySecondsValue", d, 2, 15)) }

    function loadFromBackend() {
        if (!backend) return
        let cfg = backend.getConfig()
        visibleValue = cfg.window_visible !== undefined ? cfg.window_visible : true
        floatValue = cfg.float_mode !== undefined ? cfg.float_mode : true
        clickHideValue = cfg.click_hide !== undefined ? cfg.click_hide : false
        noRepeatValue = cfg.no_repeat !== undefined ? cfg.no_repeat : true
        luckValue = cfg.luck_enabled !== undefined ? cfg.luck_enabled : false
        modeValue = cfg.mode || "roll"
        root.isSecrandom = (cfg.service === "secrandom")
        notifySecondsValue = cfg.notify_duration || 4
        btnWidthValue = cfg.button_width || 52
        btnHeightValue = cfg.button_height || 40
        animSecondsValue = cfg.animation_seconds || 3
        refreshRoster()
        ready = true
    }

    function refreshRoster() {
        if (!backend) return
        countValue = backend.getRosterCount()
        rosterPreview = backend.getRoster()
        weightsMap = backend.getWeights()
    }

    function addCurrent() {
        var n = root.newName.trim()
        if (n === "" || !backend) return
        backend.addName(n)
        root.newName = ""
    }

    Component.onCompleted: loadFromBackend()

    Connections {
        target: backend
        function onConfigChanged() { loadFromBackend() }
        function onRosterChanged() { refreshRoster() }
    }

    FileDialog {
        id: rosterDialog
        title: "选择名单文件（txt 或 Word）"
        nameFilters: ["名单文件 (*.txt *.docx)", "文本文件 (*.txt)", "Word 文档 (*.docx)", "所有文件 (*)"]
        onAccepted: if (backend) backend.importRoster(rosterDialog.selectedFile)
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        // ── 点名服务（先选这个，其它设置跟着它显示/隐藏）────
        Text { text: "点名服务"; font.bold: true }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_people_20_regular"
            title: "用哪套点名"
            description: root.isSecrandom
                ? "当前：SecRandom。本插件的按钮已隐藏 —— 请打开 SecRandom 设置，它自己就有点名按钮。"
                : "当前：内置点名。使用本插件自己的点名按钮，以及下面全部设置。"
            RowLayout {
                spacing: 8
                Button {
                    text: "内置点名"
                    highlighted: !root.isSecrandom
                    onClicked: if (backend) backend.setService("builtin")
                }
                Button {
                    text: "SecRandom"
                    highlighted: root.isSecrandom
                    onClicked: if (backend) backend.setService("secrandom")
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            visible: root.isSecrandom
            icon.name: "ic_fluent_alert_20_regular"
            title: "点名交给 SecRandom"
            description: "本插件不再显示点名按钮，下面所有设置也已隐藏。请用 SecRandom 自己的按钮点名（名单和规则都在 SecRandom 里设置）；本插件会在后台监听它的点名记录，被点到的名字由 ClassWidgets2 的灵动通知播报。"
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_alert_20_regular"
            title: "灵动通知显示时长"
            description: "点名结果用 ClassWidgets2 灵动通知播报时停留的秒数（2–15 秒），两种点名方式都生效。"
            RowLayout {
                spacing: 8
                Button { text: "−"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepNotify(-1) }
                Text {
                    Layout.preferredWidth: 60
                    horizontalAlignment: Text.AlignHCenter
                    text: root.notifySecondsValue + " 秒"
                    font.bold: true
                }
                Button { text: "+"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepNotify(1) }
            }
        }

        // ── 以下全部是「内置点名」的设置，选 SecRandom 时整体隐藏 ──
        ColumnLayout {
            id: builtinBlock
            Layout.fillWidth: true
            spacing: 4
            visible: !root.isSecrandom

        // ── 悬浮按钮 ────────────────────────────────────────
        Text { text: "悬浮按钮"; font.bold: true }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_alert_20_regular"
            title: "显示点名按钮"
            description: "打开后桌面显示“点名”小按钮（可拖动、置顶），关闭后隐藏。"
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
            icon.name: "ic_fluent_layer_20_regular"
            title: "浮窗模式"
            description: "开启后按钮为圆角半透明浮窗（悬浮质感）；关闭为实心方角按钮。"
            Switch {
                checked: root.floatValue
                onCheckedChanged: {
                    root.floatValue = checked
                    if (root.ready) backend.setFloatMode(checked)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_eye_off_20_regular"
            title: "点击后隐藏"
            description: "点名完成后自动收起按钮（适合把按钮当一次性快捷入口，下次启动仍会显示）。"
            Switch {
                checked: root.clickHideValue
                onCheckedChanged: {
                    root.clickHideValue = checked
                    if (root.ready) backend.setClickHide(checked)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_resize_20_regular"
            title: "按钮大小"
            description: "点名按钮的宽度与高度（像素），点 +/- 调整，实时生效。"
            ColumnLayout {
                spacing: 6
                RowLayout {
                    spacing: 8
                    Text { text: "宽" }
                    Button { text: "−"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepWidth(-4) }
                    Text {
                        Layout.preferredWidth: 52
                        horizontalAlignment: Text.AlignHCenter
                        text: root.btnWidthValue + " px"
                        font.bold: true
                    }
                    Button { text: "+"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepWidth(4) }
                }
                RowLayout {
                    spacing: 8
                    Text { text: "高" }
                    Button { text: "−"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepHeight(-4) }
                    Text {
                        Layout.preferredWidth: 52
                        horizontalAlignment: Text.AlignHCenter
                        text: root.btnHeightValue + " px"
                        font.bold: true
                    }
                    Button { text: "+"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepHeight(4) }
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_arrow_reset_20_regular"
            title: "重置按钮位置"
            description: "把“点名”按钮移回桌面中心（结果窗口一并回到默认位置）。"
            Button {
                text: "重置到桌面中心"
                onClicked: if (backend) backend.resetWindowPos()
            }
        }

        // ── 点名方式 ────────────────────────────────────────
        Text { text: "点名方式"; font.bold: true }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_timer_20_regular"
            title: "随机动画时长"
            description: "点名时名字滚动的秒数（1–10 秒），点 +/- 调整，下次点名生效。"
            RowLayout {
                spacing: 8
                Button { text: "−"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepAnim(-1) }
                Text {
                    Layout.preferredWidth: 60
                    horizontalAlignment: Text.AlignHCenter
                    text: root.animSecondsValue + " 秒"
                    font.bold: true
                }
                Button { text: "+"; implicitWidth: 30; implicitHeight: 28; onClicked: root.stepAnim(1) }
            }
        }

        // ── 抽取规则 ────────────────────────────────────────
        Text { text: "抽取规则"; font.bold: true }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_arrow_repeat_all_20_regular"
            title: "一轮之内不重复"
            description: "开启后使用洗牌队列：同一个人在一轮内不会被抽到两次，全部抽完后自动重新洗牌。"
            Switch {
                checked: root.noRepeatValue
                onCheckedChanged: {
                    root.noRepeatValue = checked
                    if (root.ready) backend.setNoRepeat(checked)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_dice_20_regular"
            title: "概率抽点"
            description: "开启后按每人的权重加权抽取（权重越大越容易被抽到），此时“不重复”规则不生效。"
            Switch {
                checked: root.luckValue
                onCheckedChanged: {
                    root.luckValue = checked
                    if (root.ready) backend.setLuckEnabled(checked)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_slide_settings_20_regular"
            title: "抽中概率"
            description: root.countValue > 0
                         ? "为每位同学设置权重（1–1000，默认 100）。仅在开启“概率抽点”后生效。"
                         : "名单为空，请先在下方导入名单。"

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                visible: root.countValue > 0

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        Layout.fillWidth: true
                        text: "共 " + root.countValue + " 人"
                        color: "#AAAAAA"
                        font.pixelSize: 12
                    }
                    Button {
                        text: "全部恢复默认"
                        implicitHeight: 28
                        onClicked: if (backend) backend.resetWeights()
                    }
                }

                Flickable {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(260, 34 * Math.max(1, root.countValue))
                    contentHeight: weightColumn.height
                    clip: true
                    ScrollBar.vertical: ScrollBar { }

                    Column {
                        id: weightColumn
                        width: parent.width
                        spacing: 2

                        Repeater {
                            model: root.rosterPreview

                            delegate: RowLayout {
                                required property string modelData
                                width: weightColumn.width
                                spacing: 8

                                Text {
                                    Layout.preferredWidth: 96
                                    elide: Text.ElideRight
                                    text: modelData
                                    font.pixelSize: 12
                                }

                                Slider {
                                    id: wSlider
                                    Layout.fillWidth: true
                                    from: 1
                                    to: 1000
                                    stepSize: 10
                                    value: root.weightsMap[modelData] !== undefined
                                           ? root.weightsMap[modelData] : 100
                                    onMoved: if (backend) backend.setWeight(modelData, value)
                                }

                                Text {
                                    Layout.preferredWidth: 44
                                    horizontalAlignment: Text.AlignRight
                                    text: Math.round(wSlider.value)
                                    color: "#AAAAAA"
                                    font.pixelSize: 12
                                }

                                Button {
                                    implicitWidth: 30
                                    implicitHeight: 26
                                    text: "✕"
                                    onClicked: if (backend) backend.removeName(modelData)
                                }
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: root.luckValue ? "权重已启用" : "权重已设置，但当前未开启“概率抽点”"
                    color: "#888888"
                    font.pixelSize: 11
                }
            }
        }

        // ── 名单 ────────────────────────────────────────────
        Text { text: "名单"; font.bold: true }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_clock_20_regular"
            title: "导入名单"
            description: "支持 txt 或 Word（.docx）；每行一个名字，可带“1.小明”式序号，导入后自动去除。当前名单：" + root.countValue + " 人"
            RowLayout {
                spacing: 8
                Button { text: "选择文件..."; onClicked: rosterDialog.open() }
                Button { text: "清空名单"; onClicked: if (backend) backend.clearRoster() }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_add_20_regular"
            title: "手动添加"
            description: "输入姓名后回车或点“添加”，可逐个补充名单（自动去重）。"
            RowLayout {
                spacing: 8
                TextField {
                    Layout.fillWidth: true
                    placeholderText: "输入姓名"
                    text: root.newName
                    onTextEdited: root.newName = text
                    onAccepted: root.addCurrent()
                }
                Button {
                    text: "添加"
                    onClicked: root.addCurrent()
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_class_20_regular"
            title: "名单列表"
            description: root.rosterPreview.length > 0
                         ? "已导入 " + root.rosterPreview.length + " 个名字，点右侧 ✕ 可删除个别同学。"
                         : "尚未导入名单。"

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                Flickable {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 180
                    contentHeight: rosterColumn.height
                    clip: true
                    visible: root.rosterPreview.length > 0
                    ScrollBar.vertical: ScrollBar { }

                    Column {
                        id: rosterColumn
                        width: parent.width
                        spacing: 2

                        Repeater {
                            model: root.rosterPreview
                            delegate: RowLayout {
                                required property string modelData
                                width: rosterColumn.width
                                spacing: 8

                                Text {
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    text: modelData
                                    font.pixelSize: 12
                                }
                                Button {
                                    implicitWidth: 34
                                    implicitHeight: 26
                                    text: "删除"
                                    onClicked: if (backend) backend.removeName(modelData)
                                }
                            }
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: root.rosterPreview.length === 0
                    text: "请将名单整理为每行一个名字，再导入：\n\n1.小明\n2.小红\n张三\n\n可带序号，导入时自动去除；\n一行多个名字可用逗号 / 顿号分隔"
                    color: "#AAAAAA"
                    font.pixelSize: 13
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                }
            }
        }

        // ── 测试 ────────────────────────────────────────────
        Text { text: "测试"; font.bold: true }

        SettingCard {
            Layout.fillWidth: true
            icon.name: "ic_fluent_play_20_regular"
            title: "测试抽取"
            description: "立即随机抽取一名同学（使用与点名相同的抽取规则）。"
            RowLayout {
                spacing: 8
                Button {
                    text: "抽取一个"
                    onClicked: {
                        if (!backend) return
                        var arr = backend.pickBatch(1)
                        root.pickResultText = arr.length > 0 ? arr[0] : "名单为空"
                    }
                }
                Text {
                    text: root.pickResultText
                    color: "#888888"
                }
            }
        }
        }
    }
}
