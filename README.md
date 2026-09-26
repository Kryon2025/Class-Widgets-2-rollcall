<div align="center">
<img src="icon.png" width="15%" alt="随机点名">
<h1>随机点名</h1>

<p>为 Class Widgets 2 增加随机点名功能，辅助课堂教学</p>

[![版本](https://img.shields.io/badge/%E7%89%88%E6%9C%AC-1.2.0--alpha-5A9BFF?style=for-the-badge)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/releases)
[![星标](https://img.shields.io/github/stars/Kryon2025/Class-Widgets-2-rollcall?style=for-the-badge&color=orange&label=%E6%98%9F%E6%A0%87)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/)
[![开源许可](https://img.shields.io/badge/license-MIT-blue.svg?label=%E5%BC%80%E6%BA%90%E8%AE%B8%E5%8F%AF%E8%AF%81&style=for-the-badge)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/blob/main/LICENSE)
[![下载量](https://img.shields.io/github/downloads/Kryon2025/Class-Widgets-2-rollcall/total.svg?label=%E4%B8%8B%E8%BD%BD%E9%87%8F&color=green&style=for-the-badge)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/releases)

</div>

> [!NOTE]
> 当前版本 **1.2.0-alpha**（1.2.0 系列的预览版），要求 Class Widgets 2 的插件 API `~=0.6.0`。
> 在 [插件广场](https://plaza.cw.rinlit.cn/plugins/com.rollcall) 可以一键安装/更新，也可以在 Release 页下载 `.cwplugin` 手动导入。

## 介绍

随机点名是一个**独立悬浮窗式**的点名工具（不是桌面组件），给 Class Widgets 2 补上「课堂随机点名」这一环。

从 **1.2.0** 起，点名可以由两套完全独立的服务来做，在插件设置页里一键切换：

- **内置点名** —— 用本插件自己的悬浮按钮、名单和抽取规则，结果用一个可拖动的结果窗口展示。
- **SecRandom** —— 点名的按钮、名单、规则全部交给 [SecRandom](https://github.com/SECTL/SecRandom)，本插件不再显示自己的按钮，只**在后台监听**它的点名记录，把抽到的名字用 Class Widgets 2 的灵动通知播报出来。

两种方式都能用主程序的**官方灵动通知**播报结果，显示时长可调。

## 功能

### 点名服务：内置点名 / SecRandom

| | 内置点名 | SecRandom |
| --- | --- | --- |
| 点名入口 | 本插件的「点名」悬浮按钮 | SecRandom 自己的按钮 |
| 名单与权重 | 在本插件设置页维护 | 在 SecRandom 里维护 |
| 抽取规则 | 本插件（不重复 / 权重） | SecRandom |
| 结果窗口 | 有（可拖动、可缩放） | 无 |
| 灵动通知播报 | 有 | 有（监听 SecRandom 的点名记录） |
| 需要 SecRandom | 不需要 | 需要已安装并运行 SecRandom |

选择 **SecRandom** 后，本插件的点名按钮会隐藏，「悬浮按钮 / 点名方式 / 抽取规则 / 名单 / 测试」这些设置整块一起隐藏 —— 设置页只留下「点名服务」和「灵动通知显示时长」。切回**内置点名**后它们会原样回来。

### 悬浮按钮

- 无边框、置顶、可拖动；位置自动保存，重启后回到原处。
- 拖动范围被限制在所有屏幕的联合区域内，不会被拖出屏幕后找不回来。
- 菜单打开时拖动按钮不会再导致按钮消失（拖动前会自动收起菜单，并在屏幕内钳制）。
- 大小可自定义（宽 40–160 px，高 30–100 px），改完即时生效。
- **浮窗模式**：圆角半透明 + 悬浮阴影；关掉就是实心方角样式。
- **点击后隐藏**：点名完成后自动收起按钮，适合把按钮当成一次性快捷入口。
- **左键点击** → 人数菜单：**1 名 / 2 名 / 3 名**；上课期间菜单里还会多一个「隐藏」（本节课隐藏，下课后由主程序课表自动恢复显示）。
- **左键拖动** → 移动按钮位置。

> [!IMPORTANT]
> 按钮只响应**左键**，没有右键菜单；所有开关都在「设置 → 随机点名」里。

### 点名表现

- **结果窗口**：名字竖列滚动，结束后纵列定格（配色转金色并带回弹动画）。
  - 滚动过程中按钮为「提前结束」，点一下立即定格。
  - 定格后左侧淡入「再点 1 名 / 2 名 / 3 名」可以接着抽，右侧「结束」收起窗口。
  - 窗口可拖动移动，拖右下角手柄可缩放；位置同样会自动保存。
- **灵动通知**：点名结果通过 **Class Widgets 2 自带的灵动通知**播报（不是本插件自绘的胶囊），标题为「随机点名」，正文是被点到的名字；停留时长可在 2–15 秒之间调整。

### 抽取规则

- **一轮之内不重复**（默认开启）：内部维护一个洗牌队列，同一个人在一轮里不会被抽到两次，抽完自动重洗。
- **概率抽点**：给每位同学单独设置权重（1–1000），权重越大越容易被抽到。开启概率抽点时，「一轮之内不重复」不再生效。

### 名单

- 支持 **txt** 与 **Word（.docx）** 导入，每行一个名字。
- 自动去序号：`1.小明`、`2．小红`、`(3)小王`、`01 张三` 这类写法导入后都会自动去掉序号和序号符号。
- 设置页里可以直接**手动添加**、逐个删除，并在「名单列表」里查看当前名单和每个人的抽中概率。
- 「测试抽取」可以在不弹窗口的情况下先看看抽取效果。

## 使用方法

1. 在 Class Widgets 2 的「设置 → 插件」里导入并启用本插件（`com.rollcall`），或者从[插件广场](https://plaza.cw.rinlit.cn/plugins/com.rollcall)安装。
2. 打开「设置 → 随机点名」，最上面的**点名服务**里选一套：

   **选「内置点名」**：
   1. 在「名单」里导入 txt / Word，或手动添加名字；
   2. 按需调整悬浮按钮、随机动画时长、抽取规则；
   3. 点桌面上的「点名」按钮，选 1 / 2 / 3 名开始点名。

   **选「SecRandom」**：
   1. 先去 SecRandom 里把名单和点名规则配好；
   2. 回来把「灵动通知显示时长」调成想要的秒数；
   3. 直接用 **SecRandom 自己的按钮**点名，本插件会把结果播报出来。
3. 按钮位置不合适？在设置页点「重置按钮位置」即可回到屏幕中间。

## 与 SecRandom 联动说明

- 只读监听，不改动 SecRandom 的任何配置：点名结果从
  `<SecRandom 安装目录>\data\TEMP\roll_call_record_default.json`
  里读，点名前后各读一次，`lastDrawnTime` 变新的那条就是刚被点到的同学；多人同时被点会一起播报。
- SecRandom 的安装目录从注册表
  `HKCU\Software\Classes\secrandom\shell\open\command`
  自动读取，读不到时会退回几个常见的默认安装路径。
- 本插件**不会**打开、接管或遮挡 SecRandom 的窗口 —— 如果你在点名时看到了别的窗口，那是 SecRandom 自己的点名窗口。

## 设置项一览

| 分区 | 设置 | 说明 |
| --- | --- | --- |
| 点名服务 | 用哪套点名 | 内置点名 / SecRandom 二选一 |
| 点名服务 | 灵动通知显示时长 | 2–15 秒，两种点名方式都生效 |
| 悬浮按钮 | 显示点名按钮 | 关掉后按钮隐藏，可从设置页再打开 |
| 悬浮按钮 | 浮窗模式 | 圆角半透明 / 实心方角 |
| 悬浮按钮 | 点击后隐藏 | 点名后自动收起按钮 |
| 悬浮按钮 | 按钮大小 | 宽 40–160，高 30–100（px） |
| 悬浮按钮 | 重置按钮位置 | 把按钮拉回屏幕中间 |
| 点名方式 | 随机动画时长 | 名字滚动 1–10 秒 |
| 抽取规则 | 一轮之内不重复 | 洗牌队列，一轮内不重复抽到同一人 |
| 抽取规则 | 概率抽点 | 按权重加权抽取 |
| 抽取规则 | 抽中概率 | 查看/设置每个人的权重（1–1000） |
| 名单 | 导入名单 / 手动添加 / 名单列表 | 维护点名名单 |
| 测试 | 测试抽取 | 不弹窗口，直接看抽取结果 |

## 数据存储

名单、权重和窗口位置都保存在**主程序的配置目录**下：

```
configs/plugins/com.rollcall/
├── .roll_roster.json     # 名单
├── .roll_weights.json    # 权重
└── .roll_pos.json        # 窗口位置
```

放在这里而不是插件目录里，是为了让**更新/重装插件时名单和权重不会丢**。

## 常见问题

**点了名字，灵动通知没出来？**
先确认「灵动通知显示时长」不是被调到了极小值；再确认主程序的灵动通知本身是开启可用的。结果窗口模式下窗口仍然会正常弹出，灵动通知只是额外播报一遍。

**选了 SecRandom，但点名后什么都没有？**
本插件只读 SecRandom 的点名**记录**，所以需要 SecRandom 确实在往 `data\TEMP\roll_call_record_default.json` 里写记录。可以去该文件确认它的 `lastDrawnTime` 有没有在点名时更新。

**按钮不见了？**
可能是被「点击后隐藏」收起了，或者用菜单里的「隐藏」做了本节课隐藏（下课后会自动回来）。到「设置 → 随机点名 → 显示点名按钮」打开，或点「重置按钮位置」即可。

**切到 SecRandom 后，我的名单和规则设置去哪了？**
只是被隐藏了，数据没有动。切回「内置点名」就会原样出现。

## 更新日志

各版本的变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 自动发布

推送 `v*.*.*` 格式的 tag 即可触发 GitHub Actions：自动用 `cw-plugin-pack` 打包出 `.cwplugin` 与 `.zip`，并用 `cw-plugin-publish` 发布到插件广场、创建 Release。

```bash
git tag v1.2.0-alpha
git push origin v1.2.0-alpha
```

> 发布需要在仓库的 Secrets 里配置 `CWPT_TOKEN`（从[插件广场控制台](https://plaza.cw.rinlit.cn/console)获取）。

## 名单格式示例

```
小明
小红
1.张三
2.李四
3．王五
(6)赵六
```

导入后名单为：小明 / 小红 / 张三 / 李四 / 王五 / 赵六

## 致谢 / Acknowledgements

### 引用资源 / Credits

- [Class Widgets 2](https://github.com/rinlit-233-shiroko/class-widgets-2)
- [Class Widgets 2 SDK](https://github.com/Class-Widgets/class-widgets-sdk)
- [SecRandom](https://github.com/SECTL/SecRandom)（联动方式参考了其点名记录的存储格式）

### 贡献者们 / Contributors

[![Contributors](http://contrib.nn.ci/api?repo=Kryon2025/Class-Widgets-2-rollcall)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/graphs/contributors)

## 版权 / License

本项目基于 MIT 协议开源，详情请参阅 [LICENSE](https://github.com/Kryon2025/Class-Widgets-2-rollcall/blob/main/LICENSE) 文件。

The project is licensed under the MIT license. Please refer to the [LICENSE](https://github.com/Kryon2025/Class-Widgets-2-rollcall/blob/main/LICENSE) file for details.
