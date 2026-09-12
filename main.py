"""
随机点名（Class Widgets 2 版）
=============================

交互流程：
1. 桌面浮窗小按钮（只显示"点名"，大小/位置可自定义，可拖动）
   - 左键点击 → 弹出人数菜单（1 / 3 / 5 名）
   - 右键点击 → 快捷菜单（隐藏按钮 / 打开设置）
2. 选择人数后的表现形式（可在设置页切换）：
   - 结果窗口：名字随机滚动后定格（多人纵列，可拖动/缩放，支持"提前结束"）
   - 灵动通知：顶部胶囊从屏幕上方滑入，播报后自动收起
3. "点击后隐藏"可选：适合把按钮当快捷键用的场景

名单：
- 主程序"设置 → 插件 → 随机点名"导入 .txt / .docx，也可在设置页手动增删
- 每行一个名字；支持"1.小明 / (3)王五 / 第5名 张三"式序号自动去除
- 抽取策略：默认洗牌队列不重复（取完自动重洗）；开启"概率抽点"后按每人权重加权抽取
"""

from __future__ import annotations

import json
import random
import re
import sys
import zipfile
from pathlib import Path

from loguru import logger
from pydantic import BaseModel
from PySide6.QtCore import QUrl, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from ClassWidgets.SDK import CW2Plugin, PluginAPI


class RollConfig(BaseModel):
    """插件配置（由主程序持久化）。"""

    window_visible: bool = True    # 按钮显示开关
    button_width: int = 52         # 按钮宽度
    button_height: int = 40        # 按钮高度
    animation_seconds: int = 3     # 点名滚动动画时长（秒）
    float_mode: bool = True        # 浮窗模式：半透明 + 悬浮阴影 + 自由定位
    click_hide: bool = False       # 点击按钮后自动隐藏（再次点击需从设置页恢复）
    no_repeat: bool = True         # 一轮之内不重复抽到同一人
    luck_enabled: bool = False     # 概率抽点：按每人权重加权抽取
    mode: str = "roll"             # roll=结果窗口点名, notify=灵动通知
    notify_duration: int = 4       # 灵动通知停留时长（秒）


# 序号前缀：1. / 1、 / 1） / (1) / 1． / [1] / 第3名 / 5 张三
# 纯数字后必须带标点或空格才算序号，避免把"3班"这类姓名误当序号删除
_ORDER_PREFIX = re.compile(
    r"^\s*(?:\(\d+\)|\[\d+\]|\d+\s*[.．、:：)）]\s*|\d+\s+(?=\S)|第\s*\d+\s*名)\s*"
)

# 行内分隔符：逗号 / 顿号 / 分号 / 制表符 / 连续空格（兼容一行多个名字）
_INLINE_SPLIT = re.compile(r"[,，、;；\t]+|\s{2,}")


def _clean_line(line: str) -> str:
    """去除行首序号（1.小明 → 小明）与首尾空白。"""
    line = line.strip()
    if not line:
        return ""
    m = _ORDER_PREFIX.match(line)
    if m:
        line = line[m.end():].strip()
    return line


def _read_text(path: Path) -> str:
    """读取文本文件：utf-8-sig / utf-8 / utf-16 / gbk 依次尝试。"""
    for enc in ("utf-8-sig", "utf-8", "utf-16", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def _read_docx_text(path: Path) -> str:
    """轻量解析 docx（zip 内的 word/document.xml），按段落还原为多行文本。"""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    paras = re.findall(r"<w:p\b[^>]*>.*?</w:p>", xml, re.S)
    lines = []
    for p in paras:
        # 软换行 <w:br/> 转成含换行的伪文本节点，避免同一段落内多个名字被拼成一个
        p = re.sub(r"<w:br\s*/?>", "<w:t>\\n</w:t>", p)
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S))
        if text:
            lines.append(text)
    return "\n".join(lines)


def _extract_names(content: str) -> list[str]:
    """按行提取名单：去序号、过滤空行与 # 注释行，兼容一行多个名字。"""
    names = []
    for line in content.splitlines():
        line = _clean_line(line)
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in _INLINE_SPLIT.split(line) if p.strip()]
        names.extend(parts if parts else [line])
    return names


class Plugin(CW2Plugin):
    """随机点名：小按钮 + 菜单 + 结果窗口 + 主程序设置页。"""

    configChanged = Signal()
    rosterChanged = Signal()

    def __init__(self, api: PluginAPI):
        super().__init__(api)
        self._config = RollConfig()
        self._roster: list[str] = []
        self._weights: dict[str, int] = {}
        self._shuffled: list[str] = []
        self._index = 0
        self._engine: QQmlApplicationEngine | None = None
        self._windows: list = []
        self._roster_file = Path(__file__).resolve().parent / ".roll_roster.json"
        self._weights_file = Path(__file__).resolve().parent / ".roll_weights.json"
        self._pos_file = Path(__file__).resolve().parent / ".roll_pos.json"
        self._pos = self._default_pos()
        self._load_roster()
        self._load_weights()
        self._load_pos()

    # ── 生命周期 ──────────────────────────────────────────────

    def on_load(self):
        super().on_load()
        try:
            self.api.config.register_plugin_model(self.pid, self._config)
            logger.info("[rollcall] 配置模型注册成功")
        except Exception as e:
            logger.warning(f"[rollcall] 注册配置模型失败: {e}")
        self._register_settings_page()
        if self._config.window_visible:
            self._create_windows()

    def on_unload(self):
        self._destroy_windows()
        super().on_unload()

    # ── 设置页 backend（主程序设置页注入 backend）──────────────

    @Slot(result=dict)
    def getConfig(self) -> dict:
        return self._config.model_dump()

    @Slot(bool)
    def setWindowVisible(self, value: bool) -> None:
        """按钮显示开关（关闭时连同菜单、结果窗口一并隐藏）。"""
        self._config.window_visible = bool(value)
        self._save_config()
        if self._config.window_visible:
            self._create_windows()
        elif self._windows:
            for w in self._windows:
                w.setVisible(False)
        self.configChanged.emit()

    @Slot(int)
    def setButtonWidth(self, value: int) -> None:
        self._config.button_width = max(40, min(160, int(value)))
        self._save_config()
        win = self._find_window("buttonWin")
        if win is not None:
            win.setWidth(self._config.button_width)
        self.configChanged.emit()

    @Slot(int)
    def setButtonHeight(self, value: int) -> None:
        self._config.button_height = max(30, min(100, int(value)))
        self._save_config()
        win = self._find_window("buttonWin")
        if win is not None:
            win.setHeight(self._config.button_height)
        self.configChanged.emit()

    @Slot(int)
    def setAnimationSeconds(self, value: int) -> None:
        """点名滚动动画时长（秒），下次点名生效。"""
        self._config.animation_seconds = max(1, min(10, int(value)))
        self._save_config()
        self.configChanged.emit()

    @Slot(bool)
    def setFloatMode(self, value: bool) -> None:
        """浮窗模式：按钮带悬浮阴影与半透明底，关闭后为纯色实心按钮。"""
        self._config.float_mode = bool(value)
        self._save_config()
        self.configChanged.emit()

    @Slot(bool)
    def setClickHide(self, value: bool) -> None:
        """点击按钮后自动隐藏（可作为一次性快捷入口使用）。"""
        self._config.click_hide = bool(value)
        self._save_config()
        self.configChanged.emit()

    @Slot(bool)
    def setNoRepeat(self, value: bool) -> None:
        self._config.no_repeat = bool(value)
        self._save_config()
        self.configChanged.emit()

    @Slot(bool)
    def setLuckEnabled(self, value: bool) -> None:
        """概率抽点开关（按每人权重加权抽取）。"""
        self._config.luck_enabled = bool(value)
        self._save_config()
        self.configChanged.emit()

    @Slot(str)
    def setMode(self, value: str) -> None:
        """点名表现形式：固定为结果窗口（灵动通知已移除）。"""
        self._config.mode = "roll"
        self._save_config()
        self.configChanged.emit()

    @Slot(int)
    def setNotifyDuration(self, value: int) -> None:
        self._config.notify_duration = max(2, min(15, int(value)))
        self._save_config()
        self.configChanged.emit()

    def _find_window(self, obj_name: str):
        for w in self._windows:
            if w.property("objectName") == obj_name:
                return w
        return None

    # ── 名单管理 ─────────────────────────────────────────────

    @Slot(str)
    def importRoster(self, path: str) -> None:
        """从 txt / docx 导入名单（自动去序号）。path 可能是 file:/// URL。"""
        local = QUrl(path).toLocalFile() if path else ""
        p = Path(local or path)
        if not p.exists():
            logger.warning(f"[rollcall] 名单文件不存在: {path!r} -> {p}")
            return
        try:
            if p.suffix.lower() == ".docx":
                content = _read_docx_text(p)
            else:
                content = _read_text(p)
            names = _extract_names(content)
        except Exception as e:
            logger.error(f"[rollcall] 解析名单失败: {e}")
            return
        if not names:
            logger.warning(f"[rollcall] 名单解析为空: {path}")
            return
        self._roster = names
        self._reset_shuffle()
        self._save_roster()
        self.rosterChanged.emit()
        logger.info(f"[rollcall] 已导入 {len(names)} 个名字")

    @Slot(str)
    def addName(self, name: str) -> None:
        """在设置页手动添加一个名字（去序号、去重）。"""
        cleaned = _clean_line(str(name))
        if not cleaned or cleaned in self._roster:
            return
        self._roster.append(cleaned)
        self._weights.setdefault(cleaned, 100)
        self._reset_shuffle()
        self._save_roster()
        self._save_weights()
        self.rosterChanged.emit()

    @Slot(str)
    def removeName(self, name: str) -> None:
        """从名单中删除某人（同时清理其权重）。"""
        if name not in self._roster:
            return
        self._roster = [n for n in self._roster if n != name]
        self._weights.pop(name, None)
        self._reset_shuffle()
        self._save_roster()
        self._save_weights()
        self.rosterChanged.emit()

    @Slot(result=int)
    def getRosterCount(self) -> int:
        return len(self._roster)

    @Slot(result=list)
    def getRoster(self) -> list:
        return list(self._roster)

    @Slot(result=dict)
    def getWeights(self) -> dict:
        """返回 {姓名: 权重}，未设置的默认 100。"""
        return {n: int(self._weights.get(n, 100)) for n in self._roster}

    @Slot(str, int)
    def setWeight(self, name: str, value: int) -> None:
        """设置某人的抽中权重（1 ~ 1000，越大越容易被抽到）。"""
        if name not in self._roster:
            return
        self._weights[name] = max(1, min(1000, int(value)))
        self._save_weights()
        self.rosterChanged.emit()

    @Slot()
    def resetWeights(self) -> None:
        """把所有名字的权重恢复为默认值 100。"""
        self._weights = {n: 100 for n in self._roster}
        self._save_weights()
        self.rosterChanged.emit()

    @Slot()
    def clearRoster(self) -> None:
        self._roster = []
        self._shuffled = []
        self._index = 0
        self._weights = {}
        self._save_roster()
        self._save_weights()
        self.rosterChanged.emit()

    @Slot(int, result=list)
    def pickBatch(self, count: int) -> list:
        """抽取 count 个名字。

        - 概率抽点开启：按权重加权、不放回抽取
        - 不重复开启：走洗牌队列（取完自动重洗）
        - 都关闭：纯随机、可能重复
        """
        if not self._roster:
            return []
        n = max(1, min(10, int(count)))
        if self._config.luck_enabled:
            pool = list(self._roster)
            weights = [max(1, int(self._weights.get(x, 100))) for x in pool]
            out: list[str] = []
            for _ in range(min(n, len(pool))):
                i = random.choices(range(len(pool)), weights=weights, k=1)[0]
                out.append(pool.pop(i))
                weights.pop(i)
            return out
        if not self._config.no_repeat:
            return [random.choice(self._roster) for _ in range(n)]
        out = []
        for _ in range(n):
            if self._index >= len(self._shuffled):
                self._reset_shuffle()
            if not self._shuffled:
                break
            out.append(self._shuffled[self._index])
            self._index += 1
        return out

    # ── 跨窗口桥接（按钮 → 结果窗口）─────────────────────────

    rollRequested = Signal(int)
    stopRequested = Signal()

    @Slot(int)
    def requestRoll(self, count: int) -> None:
        """菜单选择人数后启动结果窗口/灵动通知滚动点名。"""
        if self._config.click_hide:
            # 只收起按钮本身：结果窗口/灵动通知仍要显示
            btn = self._find_window("buttonWin")
            if btn is not None:
                btn.setVisible(False)
        self.rollRequested.emit(max(1, min(5, int(count))))

    @Slot()
    def stopRoll(self) -> None:
        """提前结束滚动动画（结果窗口的"提前结束"按钮）。"""
        self.stopRequested.emit()

    @Slot()
    def hideButton(self) -> None:
        """隐藏悬浮按钮（右键菜单 / 点击后隐藏共用）。"""
        self.setWindowVisible(False)

    @Slot(result=bool)
    def openSettings(self) -> bool:
        """尝试打开主程序内的插件设置页。

        当前 SDK 只提供 register/unregister，没有 open，因此这里按名称探测；
        任何一步失败都返回 False，由 QML 降级显示按钮内置的快捷设置面板。
        """
        ui = getattr(self.api, "ui", None)
        for name in ("open_settings_page", "openSettingsPage", "show_settings_page"):
            fn = getattr(ui, name, None)
            if not callable(fn):
                continue
            try:
                fn(self.pid)
                return True
            except TypeError:
                try:
                    fn()
                    return True
                except Exception as e:
                    logger.warning(f"[rollcall] 打开设置页失败({name}): {e}")
            except Exception as e:
                logger.warning(f"[rollcall] 打开设置页失败({name}): {e}")
        logger.info("[rollcall] 主程序暂不支持打开设置页，改用按钮内置面板")
        return False

    # ── 窗口可读属性 ─────────────────────────────────────────

    def _get_window_visible(self) -> bool:
        return self._config.window_visible

    windowVisible = Property(bool, _get_window_visible, notify=configChanged)

    def _get_button_width(self) -> int:
        return self._config.button_width

    buttonWidth = Property(int, _get_button_width, notify=configChanged)

    def _get_button_height(self) -> int:
        return self._config.button_height

    buttonHeight = Property(int, _get_button_height, notify=configChanged)

    def _get_animation_seconds(self) -> int:
        return self._config.animation_seconds

    animationSeconds = Property(int, _get_animation_seconds, notify=configChanged)

    def _get_float_mode(self) -> bool:
        return self._config.float_mode

    floatMode = Property(bool, _get_float_mode, notify=configChanged)

    def _get_click_hide(self) -> bool:
        return self._config.click_hide

    clickHide = Property(bool, _get_click_hide, notify=configChanged)

    def _get_luck_enabled(self) -> bool:
        return self._config.luck_enabled

    luckEnabled = Property(bool, _get_luck_enabled, notify=configChanged)

    def _get_mode(self) -> str:
        return self._config.mode

    mode = Property(str, _get_mode, notify=configChanged)

    def _get_notify_duration(self) -> int:
        return self._config.notify_duration

    notifyDuration = Property(int, _get_notify_duration, notify=configChanged)

    def _get_roster(self) -> list:
        return list(self._roster)

    roster = Property("QVariantList", _get_roster, notify=rosterChanged)

    # ── 悬浮窗口（按钮 / 菜单 / 结果，同一引擎）────────────────

    def _create_windows(self) -> None:
        if self._engine is not None:
            # 引擎已存在：只切换可见性，避免重复加载 QML
            for w in self._windows:
                w.setVisible(w.property("objectName") == "buttonWin")
            btn = self._find_window("buttonWin")
            if btn is not None:
                self._apply_window_pos(btn, self._pos["button_x"], self._pos["button_y"])
            return
        try:
            engine = QQmlApplicationEngine()
            engine.addImportPath(str(Path(sys.executable).parent / "src" / "qml"))
            engine.rootContext().setContextProperty("backend", self)
            qml_dir = Path(__file__).resolve().parent / "qml"
            for name in ("rollcall-button.qml", "rollcall-result.qml"):
                engine.load(QUrl.fromLocalFile(str(qml_dir / name)))
            loaded = len(engine.rootObjects())
            if loaded < 2:
                logger.error(f"[rollcall] 悬浮窗 QML 加载不完整：{loaded}/2")
                engine.deleteLater()
                self._engine = None
                return
            self._engine = engine
            self._windows = list(engine.rootObjects())
            for w in self._windows:
                if w.property("objectName") == "buttonWin":
                    w.setWidth(self._config.button_width)
                    w.setHeight(self._config.button_height)
                    self._apply_window_pos(w, self._pos["button_x"], self._pos["button_y"])
                    w.setVisible(self._config.window_visible)
                elif w.property("objectName") == "resultWin":
                    self._apply_window_pos(w, self._pos["result_x"], self._pos["result_y"])
                    w.setVisible(False)
                else:
                    w.setVisible(False)
            logger.info(f"[rollcall] 悬浮窗已创建（{len(self._windows)} 个）")
        except Exception as e:
            logger.error(f"[rollcall] 创建悬浮窗失败: {e}")
            if engine is not None:
                engine.deleteLater()
            self._engine = None

    def _virtual_geometry(self):
        """返回所有屏幕的联合可用区域；失败时退回主屏。"""
        screens = QGuiApplication.screens()
        if not screens:
            return QGuiApplication.primaryScreen().availableGeometry()
        geo = screens[0].availableGeometry()
        for s in screens[1:]:
            geo = geo.united(s.availableGeometry())
        return geo

    def _apply_window_pos(self, win, x: int, y: int) -> None:
        """设置窗口位置并把位置限制在**所有屏幕**的联合区域内。

        使用虚拟桌面范围而非主屏，多显示器下按钮不会被强行拽回主屏。
        """
        try:
            geo = self._virtual_geometry()
            w = max(40, int(win.width()))
            h = max(30, int(win.height()))
            x = max(geo.left(), min(int(x), geo.right() - 8))
            y = max(geo.top(), min(int(y), geo.bottom() - 8))
            # 至少保证标题区（按钮本身）大部分可见
            x = min(x, geo.right() - min(w, 24))
            y = min(y, geo.bottom() - min(h, 16))
            win.setPosition(x, y)
        except Exception as e:
            logger.warning(f"[rollcall] 恢复窗口位置失败: {e}")

    @Slot(str, int, int)
    def saveWindowPos(self, name: str, x: int, y: int) -> None:
        """拖动结束后由 QML 防抖调用。

        QML 负责跟手，越界修正放在这里：用 QGuiApplication 的屏幕联合区域，
        多显示器下比 QML 的 Screen attached property 可靠。窗口不会被拖出屏幕。
        """
        win = self._find_window(name)
        if win is not None:
            self._apply_window_pos(win, int(x), int(y))
            x, y = int(win.x()), int(win.y())
        if name == "buttonWin":
            self._pos["button_x"], self._pos["button_y"] = int(x), int(y)
        elif name == "resultWin":
            self._pos["result_x"], self._pos["result_y"] = int(x), int(y)
        else:
            return
        self._save_pos()

    @Slot()
    def resetWindowPos(self):
        """把点名按钮重置回桌面中心（结果窗口一并回到默认位置）。"""
        self._pos = self._default_pos()
        btn = self._find_window("buttonWin")
        if btn is not None:
            self._apply_window_pos(btn, self._pos["button_x"], self._pos["button_y"])
        res = self._find_window("resultWin")
        if res is not None:
            self._apply_window_pos(res, self._pos["result_x"], self._pos["result_y"])
        self._save_pos()
        self.configChanged.emit()

    def _default_pos(self) -> dict:
        """初始位置：屏幕中心（按钮 52x40、结果窗口 420x300）。"""
        try:
            geo = QGuiApplication.primaryScreen().availableGeometry()
            return {
                "button_x": geo.left() + (geo.width() - 52) // 2,
                "button_y": geo.top() + (geo.height() - 40) // 2,
                "result_x": geo.left() + (geo.width() - 420) // 2,
                "result_y": geo.top() + (geo.height() - 300) // 2,
            }
        except Exception:
            return {"button_x": 100, "button_y": 100, "result_x": 200, "result_y": 150}

    def _load_pos(self) -> None:
        """读取独立位置文件（窗口位置不依赖主程序配置模型）。"""
        try:
            if self._pos_file.exists():
                data = json.loads(self._pos_file.read_text(encoding="utf-8"))
                for k in self._pos:
                    if k in data and isinstance(data[k], int):
                        self._pos[k] = data[k]
        except Exception:
            pass

    def _save_pos(self) -> None:
        try:
            self._pos_file.write_text(
                json.dumps(self._pos, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"[rollcall] 保存窗口位置失败: {e}")

    def _destroy_windows(self) -> None:
        if self._engine is not None:
            try:
                self._engine.deleteLater()
            except Exception:
                pass
            self._engine = None
            self._windows = []

    # ── 持久化 ───────────────────────────────────────────────

    def _reset_shuffle(self) -> None:
        self._shuffled = list(self._roster)
        random.shuffle(self._shuffled)
        self._index = 0

    def _save_config(self) -> None:
        try:
            self.api.config.save()
        except Exception as e:
            logger.warning(f"[rollcall] 保存配置失败: {e}")

    def _load_roster(self) -> None:
        try:
            if self._roster_file.exists():
                data = json.loads(self._roster_file.read_text(encoding="utf-8"))
                # 只接受非空字符串，避免损坏数据产生空项/非字符串项
                self._roster = [n.strip() for n in (data or [])
                                if isinstance(n, str) and n.strip()]
                self._reset_shuffle()
        except Exception:
            self._roster = []

    def _save_roster(self) -> None:
        try:
            self._roster_file.write_text(
                json.dumps(self._roster, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"[rollcall] 保存名单失败: {e}")

    def _load_weights(self) -> None:
        """读取权重文件；只保留仍在名单中且为数字的权重。"""
        try:
            if self._weights_file.exists():
                data = json.loads(self._weights_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._weights = {
                        k: int(v) for k, v in data.items()
                        if isinstance(k, str) and isinstance(v, (int, float))
                    }
        except Exception:
            self._weights = {}

    def _save_weights(self) -> None:
        try:
            self._weights_file.write_text(
                json.dumps(self._weights, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"[rollcall] 保存权重失败: {e}")

    # ── 设置页 ───────────────────────────────────────────────

    def _register_settings_page(self) -> None:
        try:
            self.api.ui.register_settings_page(
                qml_path=str(Path(__file__).resolve().parent / "qml" / "settings.qml"),
                title="随机点名",
                icon="ic_fluent_alert_20_regular",
            )
            logger.info("[rollcall] 设置页注册成功")
        except Exception as e:
            logger.warning(f"[rollcall] 注册设置页失败: {e}")
