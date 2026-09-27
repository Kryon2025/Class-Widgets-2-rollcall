# 第三方组件与许可声明 / Third-Party Notices

本插件自身以 **MIT License** 发布，Copyright (c) 2026 Kryon，**许可正文见 [LICENSE](LICENSE)**。

本文件只放**不属于 MIT 正文**的内容：与 SecRandom 的联动方式、参考过的上游项目及其许可声明。

> **为什么单独一份文件，而不写进 `LICENSE`？**
> GitHub 及各类合规工具（Licensee / SPDX / FOSSA 等）是拿 `LICENSE` 文件去**逐字匹配**已知
> 许可证文本的。一旦在 MIT 正文后追加别的段落，仓库会被识别成 `Other / NOASSERTION`，
> 顶部不再显示 MIT 徽章。GitHub 官方文档对此的说明是：
> *"To have your license detected, simplify your LICENSE file and note the complexity somewhere else,
> such as your repository's README file."*
> （<https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository>）
> 因此本仓库采用通行做法：`LICENSE` 只放逐字许可正文，复杂情况写在这里，README 里给出摘要与链接。

各源文件头部的机器可读标识（[REUSE](https://reuse.software/) / SPDX 写法）：

```text
# SPDX-FileCopyrightText: 2026 Kryon
#
# SPDX-License-Identifier: MIT
```

---

## 1. 与 SecRandom 的联动方式

本插件提供「SecRandom」点名方式，通过下面两种**公开接口**与该软件联动，
**不复制、不分发其任何代码或二进制文件**，安装包内没有它的任何文件。

### 1.1 点名记录文件（读取结果，默认流程）

读取 SecRandom 自己维护的记录文件，**仅取值，不写入、不修改**：

```text
<SecRandom 安装目录>\data\TEMP\roll_call_record*.json          （2 代 / 3 代点名记录）
<SecRandom 安装目录>\data\history\roll_call_history\*.json     （2 代历史记录）
```

读到的内容：班级名、学生姓名 / 学号、抽中时间等。本插件默认的运行时流程**只做这一件事**。

### 1.2 URL 协议 / 命名管道（可选，默认不使用）

SecRandom 安装时注册到系统的协议：

```text
HKEY_CURRENT_USER\Software\Classes\secrandom\shell\open\command
    = <SecRandom 安装目录>\SecRandom.Desktop.exe --url "%1"
```

本插件附带的可选脚本 `secrandom_ipc.py` 会按该协议（或等价的命名管道）发送动作 URL，
供测试与手动触发使用；插件在点名过程中**不会**主动触发 SecRandom。

---

## 2. SECTL / SecRandom —— GNU GPLv3

- 项目地址：<https://github.com/SECTL/SecRandom>
- 许可证：**GNU General Public License v3.0**（GPLv3）
- 版权：Copyright (c) 2025-2026 SECTL
- 上游说明（摘自其 README）：

  > SecRandom 以 GNU GPLv3 协议发布！您可以修改和再发布源代码，但再发布的衍生作品也必须遵循 GNU GPLv3

**与本插件的关系**

- 本插件**不包含、不链接、不修改** SecRandom 的任何代码或二进制文件。
- 读取另一个程序生成的数据文件属于正常的互操作行为，**不构成对 SecRandom 的衍生作品**，
  因此本插件以 MIT 发布不受 GPLv3 传染。
- 本插件内置的「随机点名」为独立实现（Python 标准库 `random.choice` / `random.choices`
  加用户在设置页手填的 1–100 静态权重），**不是** SecRandom 的「历史平衡 / 动态权重」算法，
  也未从 SecRandom 源码移植任何逻辑。
- 若今后有任何 SecRandom 的代码（含 `SecRandom4Ci.Interface` 等）被内联进本插件，
  本插件必须一并改为以 GPLv3 发布。

---

## 3. SECTL / SecRandom-CI —— MIT（参考了其协议实现）

- 项目地址：<https://github.com/SECTL/SecRandom-CI>
- 许可证：**MIT License**，Copyright (c) 2025 黎泽懿
- 说明：本插件的命名管道客户端（`secrandom_ipc.py`）参考了该项目对 SecRandom 通信协议的实现，
  并用 Python **重新编写**，**未复制其源代码**。参考过的上游文件：

  - `SecRandom4Ci/Shared/SecRandomIpcSendUrl.cs`
  - `SecRandom4Ci.Interface/Services/ISecRandomService.cs`
  - `SecRandom4Ci.Interface/Models/CallResult.cs`
  - `SecRandom4Ci.Interface/Models/NotificationData.cs`
  - `SecRandom4Ci.Interface/Models/Student.cs`
  - `SecRandom4Ci/Plugin.cs`

按 MIT 的要求，保留该项目的版权与许可声明：

```text
MIT License

Copyright (c) 2025 黎泽懿

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. ClassIsland / ClassIsland —— GNU GPLv3

- 项目地址：<https://github.com/ClassIsland/ClassIsland>
- 许可证：**GNU GPLv3**
- 本插件**不包含、不链接**它的任何代码。开发阶段仅阅读其公开文档与上述 SecRandom-CI 的源码，
  用于理解「SecRandom ↔ ClassIsland」的联动方式。本插件运行在 Class Widgets 2 上，
  与 ClassIsland 之间没有代码依赖关系。

---

## 5. Class Widgets 2

- 本插件的宿主程序。本插件通过其插件接口（`api.config` / `api.notification` 等）工作，
  界面与逻辑均为独立实现。Class Widgets 2 及其名称、图标归其各自所有者所有。

---

## 6. 名称与商标

「SecRandom」「ClassIsland」「Class Widgets」等名称、图标、标识归各自所有者所有；
本插件对它们的提及仅用于**说明兼容性与联动方式**。本插件与上述项目及其团队
**没有任何隶属、合作或背书关系**，也未获得其官方认证。

---

## 7. 本插件自身

- 许可证：**MIT License**，Copyright (c) 2026 Kryon —— 正文见 [LICENSE](LICENSE)
- 主页 / 问题反馈：<https://github.com/Kryon2025/Class-Widgets-2-rollcall>
- 维护说明：本插件按现状提供，不承诺长期维护或持续修复缺陷（MIT 正文本身即免除担保责任）。
