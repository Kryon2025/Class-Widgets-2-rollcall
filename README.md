<div align="center">
<img src="icon.png" width="15%" alt="随机点名">
<h1>随机点名</h1>

<p>为 Class Widgets 2 增加随机点名功能，辅助课堂教学</p>

[![版本](https://img.shields.io/badge/%E7%89%88%E6%9C%AC-2.0.0--alpha-5A9BFF?style=for-the-badge)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/releases)
[![星标](https://img.shields.io/github/stars/Kryon2025/Class-Widgets-2-rollcall?style=for-the-badge&color=orange&label=%E6%98%9F%E6%A0%87)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/)
[![开源许可](https://img.shields.io/badge/license-MIT-blue.svg?label=%E5%BC%80%E6%BA%90%E8%AE%B8%E5%8F%AF%E8%AF%81&style=for-the-badge)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/blob/main/LICENSE)
[![下载量](https://img.shields.io/github/downloads/Kryon2025/Class-Widgets-2-rollcall/total.svg?label=%E4%B8%8B%E8%BD%BD%E9%87%8F&color=green&style=for-the-badge)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/releases)

</div>

> [!NOTE]
> 当前版本 **2.0.0-alpha**（2.0.0 系列的预览版），要求 Class Widgets 2 的插件 API `~=0.6.0`。
> 在 [插件广场](https://plaza.cw.rinlit.cn/plugins/com.rollcall) 可以一键安装/更新，也可以在 Release 页下载 `.cwplugin` 手动导入。

## 介绍

随机点名是一个**独立悬浮窗式**的点名工具，为 Class Widgets 2 提供「课堂随机点名」。

从 **2.0.0-alpha** 起，点名可以由两套独立的服务来做，在插件设置页最上面的「使用什么服务」里一键切换（SecRandom 还分 2 代 / 3 代）：

- **随机点名** —— 用本插件自己的悬浮按钮、名单和抽取规则，结果用一个可拖动的结果窗口展示。
- **SecRandom** —— 点名的按钮、名单、规则全部交给 [SecRandom](https://github.com/SECTL/SecRandom)，本插件不再显示自己的按钮，只**在后台监听**它的点名记录，把抽到的名字用 Class Widgets 2 的灵动通知播报出来。在「使用什么服务」里点「SecRandom 2」或「SecRandom 3」即可。

两种方式都能用主程序的**官方灵动通知**播报结果，显示时长可调。

## 功能

### 点名服务：随机点名 / SecRandom 2 / SecRandom 3

| | 随机点名 | SecRandom |
| --- | --- | --- |
| 点名入口 | 本插件的「点名」悬浮按钮 | SecRandom 自己的按钮 |
| 名单与权重 | 在本插件设置页维护 | 在 SecRandom 里维护 |
| 结果窗口 | 有（可拖动、可缩放） | 在 SecRandom 里设置 |
| 灵动通知播报 | 有 | 有（监听 SecRandom 的点名记录） |
| 需要 SecRandom | 不需要 | 需要已安装并运行 SecRandom |

### 悬浮按钮

- 无边框、置顶、可拖动。
- 拖动范围被限制在所有屏幕的联合区域内，不会被拖出屏幕后找不回来。
- 菜单打开时拖动按钮不会再导致按钮消失（拖动前会自动收起菜单，并在屏幕内钳制）。
- 大小可自定义（宽 40–160 px，高 30–100 px）。
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
- **隐藏状态照样播报**：灵动通知挂在主程序的**小组件层**上，那一层被「隐藏小组件」收起时通知没有落脚点，所以播报前会**临时把它恢复显示**，等通知播报完毕再自动还原成原先的隐藏状态（按钮被「点击后隐藏」「本节课隐藏」收起时也一样会临时露出来）。

### 抽取规则

- **一轮之内不重复**（默认开启）：内部维护一个洗牌队列，同一个人在一轮里不会被抽到两次，抽完自动重洗。
- **概率抽点**：给每位同学单独设置权重比例（**1–100**，默认 100），权重越大越容易被抽到。开启概率抽点时，「一轮之内不重复」不再生效。

### 名单

- 支持 **txt** 与 **Word（.docx）** 导入，每行一个名字。
- 自动去序号：`1.小明`、`2．小红`、`(3)小王`、`01 张三` 这类写法导入后都会自动去掉序号和序号符号。
- 设置页里可以直接**手动添加**、逐个删除，并在「名单列表」里查看当前名单和每个人的抽中概率。
- 「测试抽取」可以在不弹窗口的情况下先看看抽取效果。

## 使用方法

1. 在 Class Widgets 2 的「设置 → 插件」里导入并启用本插件（`com.rollcall`），或者从[插件广场](https://plaza.cw.rinlit.cn/plugins/com.rollcall)安装。
2. 打开「设置 → 随机点名」，在最上面的「使用什么服务」里选一套：

   **选「随机点名」**：
   1. 在「名单」里导入 txt / Word，或手动添加名字；
   2. 按需调整悬浮按钮、随机动画时长、抽取规则（概率抽点的权重比例是 1–100）；
   3. 点桌面上的「点名」按钮，选 1 / 2 / 3 名开始点名。

   **选「SecRandom 2」或「SecRandom 3」**（2 代的主程序是 `SecRandom.exe`，3 代是 `SecRandom.Desktop.exe`）：
   1. 先去 SecRandom 里把名单和点名规则配好；
   2. 回来把「灵动通知显示时长」调成想要的秒数；
   3. 直接用 **SecRandom 自己的按钮**点名，本插件会把结果播报出来。
3. 按钮位置不合适？在设置页点「重置按钮位置」即可回到屏幕中间。

## 与 SecRandom 联动说明

- 设置页里的「SecRandom 2」对应下面的 **2 代**，「SecRandom 3」对应 **3 代**。
- **选哪一代就只盯哪一代**：选「SecRandom 2」时只读 2 代的记录文件，3 代那边连扫都不扫，选「SecRandom 3」同理；切换版本或位置会立刻重建基线，不会把旧记录当成刚点到的名字播报出来。
- **两代的位置分开存**：「SecRandom 位置」这张卡跟着上面选中的那一代走（标题会写成「SecRandom 2 的位置」/「SecRandom 3 的位置」），在这里选主程序只影响这一代，不会把另一代也带跑偏；留空就是自动扫描。
- **3 代怎么判**（`SecRandom.Desktop.exe`，如 `F:\SECTL\SecRandom`）：看 `data\TEMP\roll_call_record_default.json`，每条带 `lastDrawnTime` → 按时间变新判断。
- **2 代怎么判**（`SecRandom.exe`，如 `D:\SecRandom`）：优先看 `data\history\roll_call_history\<班级>.json` —— 那里每人有 `last_drawn_time`，而且每次抽取都会追加一条带 `draw_time` 的明细 → 按最新的 `draw_time` 变新判断（TEMP 那份记录会被 SecRandom 的「清除记录」清空，历史记录则留着）。这个目录里没有历史文件时，才退回 `data\TEMP\roll_call_record__<班级>__….json`（内容是「人名 → 抽中次数」、没有时间戳 → 按**次数变多**判断）。**新记录也算数**：文件里冒出从没见过的记录（3 代的新记录、2 代首次抽到某人）同样算「刚抽到」；只是被列进文件、计数还是 0 的不算。
- 安装目录：先读 `secrandom://` 协议指向的路径，再扫各盘根目录（`D:\SecRandom`、`F:\SECTL\SecRandom`、`%LOCALAPPDATA%\Programs\SecRandom` 等），最后用「有没有 `data\TEMP`」来确认。**扫到的位置直接显示在设置页上**，也可以点「选择主程序…」自己指定（只作用于选中的那一代）—— 装在哪都行，不必在某个固定盘。
- 全程**只读**，不改动 SecRandom 的任何配置；刚启动（刚开始监听）时只建立基线，不会把历史记录当成刚点到的名字播报出来，也不会把同一次点名重复播报。
- 本插件**不会**打开、接管或遮挡 SecRandom 的窗口 —— 如果你在点名时看到了别的窗口，那是 SecRandom 自己的点名窗口。

## 设置项一览

| 分区 | 设置 | 说明 |
| --- | --- | --- |
| 点名服务 | 使用什么服务 | 随机点名 / SecRandom 2 / SecRandom 3 三选一 |
| 点名服务 | 灵动通知显示时长 | 2–15 秒，两种点名方式都生效 |
| 点名服务 | SecRandom 位置 | 跟着选中的那一代走（标题带 2 / 3，卡片里写明这一代的主程序：2 代是 `SecRandom.exe`、3 代是 `SecRandom.Desktop.exe`），两代各存各的；可「重新扫描」或「选择主程序…」手动指定 |
| 悬浮按钮 | 显示点名按钮 | 关掉后按钮隐藏，可从设置页再打开 |
| 悬浮按钮 | 浮窗模式 | 圆角半透明 / 实心方角 |
| 悬浮按钮 | 点击后隐藏 | 点名后自动收起按钮 |
| 悬浮按钮 | 按钮大小 | 宽 40–160，高 30–100（px） |
| 悬浮按钮 | 重置按钮位置 | 把按钮拉回屏幕中间 |
| 点名方式 | 随机动画时长 | 名字滚动 1–10 秒 |
| 抽取规则 | 一轮之内不重复 | 洗牌队列，一轮内不重复抽到同一人 |
| 抽取规则 | 概率抽点 | 按权重加权抽取 |
| 抽取规则 | 抽中概率 | 查看/设置每个人的权重比例（1–100） |
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

## 常见问题


**按钮不见了？**
可能是被「点击后隐藏」收起了，或者用菜单里的「隐藏」做了本节课隐藏（下课后会自动回来）。到「设置 → 随机点名 → 显示点名按钮」打开，或点「重置按钮位置」即可。

**切到 SecRandom 后，我的名单和规则设置去哪了？**
只是被隐藏了，数据没有动。切回「随机点名」就会原样出现。

## 更新日志

各版本的变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 自动发布

推送 `v*.*.*` 格式的 tag 即可触发 GitHub Actions：自动用 `cw-plugin-pack` 打包出 `.cwplugin` 与 `.zip`，并用 `cw-plugin-publish` 发布到插件广场、创建 Release。

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

### 贡献者们 / Contributors

[![Contributors](http://contrib.nn.ci/api?repo=Kryon2025/Class-Widgets-2-rollcall)](https://github.com/Kryon2025/Class-Widgets-2-rollcall/graphs/contributors)

## 第三方组件与声明

本插件运行时只和 SecRandom **交换数据文件**，不碰它的代码，因此自身可以继续用 MIT 发布。要点：

- **SecRandom**（[SECTL/SecRandom](https://github.com/SECTL/SecRandom)，**GPLv3**，© 2025-2026 SECTL）：本插件**不包含、不链接、不修改**它的任何代码，只在运行时**读取它自己写出的点名记录**（`data\TEMP\roll_call_record*.json`、`data\history\roll_call_history\*.json`），也不触发它的抽取、不改它的配置。内置的加权抽取是独立实现（`random.choices` + 用户手填的 1–100 静态权重），不是它的动态权重算法。
- **SecRandom-CI**（[SECTL/SecRandom-CI](https://github.com/SECTL/SecRandom-CI)，**MIT**，© 2025 黎泽懿）：本插件的命名管道客户端（`secrandom_ipc.py`）是照它公开的协议实现**用 Python 重写**的，未复制其源码；按 MIT 要求保留其版权与许可声明。
- **ClassIsland**（[ClassIsland/ClassIsland](https://github.com/ClassIsland/ClassIsland)，**GPLv3**）：本插件不包含、不链接它的代码，只在开发阶段阅读其文档以理解联动协议。
- 「SecRandom」「ClassIsland」「Class Widgets」等名称与图标归各自所有者；本插件与上述项目**没有隶属或背书关系**。

完整说明与各许可证全文见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。

## 版权 / License

本项目基于 **MIT License** 开源，Copyright (c) 2026 Kryon。**许可正文见 [LICENSE](LICENSE)** —— 该文件只放**逐字**的 MIT 正文，这样 GitHub、Licensee、SPDX / FOSSA 等工具才能把仓库识别成 MIT（正文后混入其它文本会被识别成 `Other / NOASSERTION`）。

- 与 SecRandom、ClassIsland 等项目的联动方式与第三方许可声明：见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
- 每个源文件头部都带 `SPDX-FileCopyrightText` 与 `SPDX-License-Identifier: MIT` 标识（REUSE / SPDX 写法）。
- 本项目按现状提供，不承诺长期维护或持续修复缺陷 —— MIT 正文本身即已免除担保责任。

The project is licensed under the MIT License, Copyright (c) 2026 Kryon. See [LICENSE](LICENSE) for the full license text and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for third-party notices.
