# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2026 Kryon
#
# SPDX-License-Identifier: MIT
"""SecRandom 点名服务（纯标准库）。

这是「第二种点名方式」的后端。两种通道都已实测确认：

  触发（单向，无依赖）
      注册表 HKCU\\Software\\Classes\\secrandom\\shell\\open\\command
          = F:\\SECTL\\SecRandom\\SecRandom.Desktop.exe --url "%1"
      所以 os.startfile("secrandom://<动作>") 就能让 SecRandom 执行动作。

  取名字（读文件）
      <SecRandom 安装目录>\\data\\TEMP\\roll_call_record_default.json
          { "scopes": { "<scope>": { "records": {
                "<uuid>": {"name": "钟芳玉", "id": "51", "count": 1,
                           "lastDrawnTime": "2026-09-26T23:25:16.9589565+08:00"} } } } }
      点名前后各读一次，lastDrawnTime 变新的那条就是刚被点到的。

自测（只读，不会真的点名）:
    python secrandom_service.py
自测（会真的触发一次点名）:
    python secrandom_service.py --trigger
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ── 可配置项（会被插件设置页覆盖） ──────────────────────────────────────────
SCHEME = "secrandom"                # URL 协议名（注册表里确认过）
DEFAULT_ACTION = "roll_call"        # secrandom:// 后面的动作；候选 roll_call / quick_draw / lottery
RECORD_FILE_NAME = "roll_call_record_default.json"
RECORD_SUBDIR = ("TEMP",)
# 2 代的历史记录：<安装目录>\data\history\roll_call_history\<班级>.json
# 每次抽取都会往里追加一条带 draw_time 的明细，比 TEMP 的「人名 → 次数」可靠
HISTORY_SUBDIR = ("history", "roll_call_history")
POLL_INTERVAL = 0.25                # 轮询间隔（秒）
DEFAULT_TIMEOUT = 6.0               # 等待新记录的超时（秒）

# 兜底安装目录（注册表读不到时用；实际还会扫描各盘根目录）
FALLBACK_INSTALL_DIRS = (
    Path(r"D:\SecRandom"),                    # 2 代默认安装位置
    Path(r"F:\SECTL\SecRandom"),             # 1 代常见位置
    Path(r"C:\Program Files\SecRandom"),
    Path(r"C:\Program Files (x86)\SecRandom"),
    Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\SecRandom")),
)
# 认一个目录是不是 SecRandom 安装目录：有 data\TEMP 或主程序
INSTALL_MARKER_FILES = ("SecRandom.exe", "SecRandom.Desktop.exe")
# 缓存的安装目录（扫描各盘比较慢，不能每次轮询都扫）
_INSTALL_CACHE: list = []
# 缓存的 [(目录, 版本)]（识别版本要读记录文件，同样不能每次轮询都读）
_INSTALLS_CACHE: list = []


class SecRandomError(RuntimeError):
    """SecRandom 服务调用失败。"""


@dataclass
class Pick:
    """一次点名记录。"""

    name: str
    sid: str
    count: int
    drawn_at: str

    @property
    def time(self) -> float:
        """lastDrawnTime 的 Unix 时间戳；解析不了就返回 0。"""
        try:
            return datetime.fromisoformat(self.drawn_at).timestamp()
        except (ValueError, TypeError):
            return 0.0

    def __str__(self) -> str:
        return f"{self.name}(学号 {self.sid})"


# ── 定位 ────────────────────────────────────────────────────────────────────

def looks_like_install(p: Path) -> bool:
    """这个目录像不像 SecRandom 的安装目录。"""
    if not p.is_dir():
        return False
    if (p / "data" / "TEMP").is_dir():
        return True
    return any((p / f).is_file() for f in INSTALL_MARKER_FILES)


# ── 版本与目标 ──────────────────────────────────────────────────────────────
# 实测两代的记录完全不一样，判定方式也不同：
#   2 代（SecRandom.exe）：一次抽取写两处 ——
#       data\history\roll_call_history\<班级>.json
#               每人有 last_drawn_time 和 history[{draw_time, draw_method, …}]，
#               带真实时间戳 → 首选这个，按「最新 draw_time 变新」判断
#       data\TEMP\roll_call_record__<班级>__…json
#               内容是「人名 → 抽中次数」，没有时间戳，而且会被「清除记录」清空
#               → 只有没有历史文件时才退回用它（按次数变多判断）
#   3 代（SecRandom.Desktop.exe）：data\TEMP\roll_call_record_default.json，
#                          每条记录带 lastDrawnTime → 按时间变新判断
VERSION_AUTO = ""
VERSION_2 = "2"
VERSION_3 = "3"
VERSION_LABELS = {VERSION_2: "SecRandom 2 代", VERSION_3: "SecRandom 3 代"}

_TARGET_VERSION = VERSION_AUTO      # 用户选的版本；空＝自动识别
_TARGET_DIR = ""                    # 用户自己指的主程序目录；空＝自动扫描


def set_target(version: str = "", install_dir: str = "") -> None:
    """告诉本模块用哪一代、装在哪。目标真的变了才清缓存重来。

    设置页每次刷新都会调这里，目标没变就不该把已经扫好的缓存清掉。
    """
    global _TARGET_VERSION, _TARGET_DIR
    v = str(version or "").strip()
    v = v if v in (VERSION_2, VERSION_3) else VERSION_AUTO
    d = str(install_dir or "").strip()
    if v == _TARGET_VERSION and d == _TARGET_DIR:
        return
    _TARGET_VERSION, _TARGET_DIR = v, d
    _INSTALL_CACHE[:] = []
    _INSTALLS_CACHE[:] = []
    _SNAPSHOT.clear()


def _normalize_dir(raw) -> Path | None:
    """用户给的可能是一串 URL、exe 路径或目录，统一成目录。"""
    s = str(raw or "").strip().strip('"')
    if not s:
        return None
    if s.lower().startswith("file:///"):
        s = s[8:]
    p = Path(s)
    if p.is_file():
        return p.parent
    if p.is_dir():
        return p
    return None


def detect_version(p: Path) -> str:
    """判断这个安装目录是 2 代还是 3 代；判不出来返回空串。"""
    temp = p / "data" / "TEMP"
    if temp.is_dir():
        try:
            files = sorted(temp.glob("roll_call_record*.json"))
        except OSError:
            files = []
        # 按抽取范围分文件（名字不只 default）→ 2 代
        if any(f.name != RECORD_FILE_NAME for f in files):
            return VERSION_2
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8", errors="ignore"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(data, dict):
                return VERSION_3 if isinstance(data.get("scopes"), dict) else VERSION_2
    if (p / "SecRandom.exe").is_file():
        return VERSION_2
    if (p / "SecRandom.Desktop.exe").is_file():
        return VERSION_3
    return ""


def registry_install_dirs() -> list:
    """注册表里 secrandom:// 协议指向的目录（可能指向已卸载的旧版本）。"""
    out: list = []
    if os.name != "nt":
        return out
    try:
        import winreg  # type: ignore
    except ImportError:
        return out
    key = r"Software\Classes\secrandom\shell\open\command"
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, key) as k:
                cmd, _ = winreg.QueryValueEx(k, "")
        except OSError:
            continue
        exe = str(cmd).strip()
        # 形如: "F:\SECTL\SecRandom\SecRandom.Desktop.exe" --url "%1"
        if exe.startswith('"'):
            exe = exe[1:].split('"', 1)[0]
        else:
            exe = exe.split(" ", 1)[0]
        p = Path(exe)
        if p.is_file():
            out.append(p.parent)
    return out


def scan_install_dirs() -> list:
    """扫各盘根目录（以及常见的程序目录）找 SecRandom 装在哪。"""
    out: list = []
    for letter in "CDEFGHIJ":
        base = Path(letter + ":\\")
        if not base.exists():
            continue
        try:
            children = list(base.iterdir())
        except OSError:
            continue
        for q in children:
            if not q.is_dir():
                continue
            low = q.name.lower()
            if "secrandom" in low:
                out.append(q)
            elif low in ("sectl", "software", "apps", "programs",
                         "program files", "program files (x86)"):
                try:
                    out.extend(c for c in q.iterdir()
                               if c.is_dir() and "secrandom" in c.name.lower())
                except OSError:
                    pass
    for env in ("LOCALAPPDATA", "APPDATA", "ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env)
        if not base:
            continue
        for sub in ("SecRandom", r"Programs\SecRandom"):
            cand = Path(base) / sub
            if cand.is_dir():
                out.append(cand)
    return out


def find_install_dirs(refresh: bool = False) -> list:
    """找出所有像样的 SecRandom 安装目录（1 代、2 代可以同时存在）。"""
    if _INSTALL_CACHE and not refresh:
        return list(_INSTALL_CACHE)
    found: list = []
    for p in (registry_install_dirs() + list(FALLBACK_INSTALL_DIRS)
              + scan_install_dirs()):
        try:
            if looks_like_install(p) and p not in found:
                found.append(p)
        except OSError:
            continue
    if found:
        _INSTALL_CACHE[:] = found
    return list(found)


def find_install_dir() -> Path | None:
    """第一个能用的安装目录（保留旧接口）。"""
    dirs = find_install_dirs()
    return dirs[0] if dirs else None


def data_dir() -> Path:
    d = find_install_dir()
    if not d:
        raise SecRandomError(
            "找不到 SecRandom 安装目录。"
            "请确认 SecRandom 已安装（1 代 F:\\SECTL\\SecRandom、"
            "2 代 D:\\SecRandom 都会自动识别）。"
        )
    return d / "data"


def installs(refresh: bool = False) -> list:
    """[(安装目录, 版本)] —— 版本为 "2" / "3"，判不出来是空串。

    结果跟安装目录一起缓存：轮询是每 0.25 秒一次，不能每次都去解析记录文件。
    """
    if _INSTALLS_CACHE and not refresh:
        return list(_INSTALLS_CACHE)
    out = [(d, detect_version(d)) for d in find_install_dirs(refresh=refresh)]
    _INSTALLS_CACHE[:] = out
    return list(out)


def active_install_dirs() -> list:
    """真正要监听的那些安装目录。

    选了版本就只留那一代（另一代连扫都不扫，省掉没必要的开销）；
    用户自己指定了目录就以它为准。
    """
    chosen = _normalize_dir(_TARGET_DIR)
    if chosen is not None:
        if looks_like_install(chosen):
            return [chosen]
        return []
    if not _TARGET_VERSION:
        return find_install_dirs()
    return [d for d, v in installs() if v == _TARGET_VERSION]


def _history_dir(d: Path) -> Path | None:
    """这个安装目录的历史记录目录，但**只有 2 代**才用（3 代照旧看 TEMP）。

    两代的历史文件结构完全不同（2 代按人名作键、字段是 history/last_drawn_time；
    3 代按 uuid 作键、字段是 histories/record_name），所以只对 2 代启用。
    """
    if _TARGET_VERSION == VERSION_3:
        return None
    try:
        ver = dict(installs()).get(d) or detect_version(d)
    except Exception:
        return None
    if ver != VERSION_2:
        return None
    return (d / "data").joinpath(*HISTORY_SUBDIR)


def record_files() -> list:
    """当前目标下要看的点名记录文件。

    2 代优先用 data 目录下 history/roll_call_history 里的 <班级>.json —— 那里每次抽取都会
    多出一条带 draw_time 的明细，比 TEMP 的「人名 → 抽中次数」可靠（TEMP 会被
    「清除记录」清空，也没有时间戳）；这个安装目录没有历史文件时再退回 TEMP。
    3 代照旧看 data 目录下 TEMP 里的 roll_call_record_default.json。
    """
    out: list = []
    for d in active_install_dirs():
        hist = _history_dir(d)
        picked: list = []
        if hist is not None and hist.is_dir():
            try:
                picked = [p for p in sorted(hist.glob("*.json")) if p.is_file()]
            except OSError:
                picked = []
        if not picked:
            temp = d / "data" / "TEMP"
            if temp.is_dir():
                try:
                    picked = [p for p in sorted(temp.glob("roll_call_record*.json"))
                              if p.is_file()]
                except OSError:
                    picked = []
        out.extend(picked)
    return out


def target_summary() -> str:
    """给设置页显示的一句话：用的哪一代、扫到在哪、有几个。"""
    raw = str(_TARGET_DIR or "").strip()
    chosen = _normalize_dir(raw)
    lines: list = []
    if raw and chosen is None:
        return ("手动指定：%s（这个路径不存在或不是文件夹，"
                "已退回自动扫描）" % raw)
    if chosen is not None:
        ver = detect_version(chosen)
        label = VERSION_LABELS.get(ver, "认不出是哪一代")
        lines.append("手动指定：%s（%s）" % (chosen, label))
        if not looks_like_install(chosen):
            lines.append("这个目录里没看到 data\\TEMP，可能选错了")
        return "；".join(lines)

    found = installs()
    if _TARGET_VERSION:
        hit = [d for d, v in found if v == _TARGET_VERSION]
        if hit:
            return "自动扫描：%s（%s）" % ("；".join(str(d) for d in hit),
                                        VERSION_LABELS[_TARGET_VERSION])
        other = [f"{VERSION_LABELS.get(v, '未知')} {d}" for d, v in found]
        if other:
            return ("没找到 %s；本机有：%s"
                    % (VERSION_LABELS[_TARGET_VERSION], "，".join(other)))
        return "没找到 SecRandom（可点右边按钮手动指定主程序）"

    if not found:
        return "没找到 SecRandom（可点右边按钮手动指定主程序）"
    return "自动识别：" + "，".join(
        "%s %s" % (VERSION_LABELS.get(v, "未知版本"), d) for d, v in found)


def record_file() -> Path:
    """主安装目录的记录文件路径（保留旧接口，用于自测显示）。"""
    return data_dir().joinpath(*RECORD_SUBDIR) / RECORD_FILE_NAME


# ── 读记录 ──────────────────────────────────────────────────────────────────

def _read_file(p: Path):
    """解析一个记录文件。

    返回 (格式, [(指纹, Pick)], 指纹表)。两种格式：
      1 代  {"scopes": {"<范围>": {"records": {"<uuid>": {name,id,count,lastDrawnTime}}}}}
            → 指纹 = "<范围>|<uuid>"，值 = lastDrawnTime 时间戳
      2 代  {"吴智宇": 1, "陈若溪": 1, ...}
            → 指纹 = 名字，值 = 抽中次数（没有时间戳，只能按次数变多判断）
    """
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return "", [], {}
    if not isinstance(data, dict):
        return "", [], {}

    scopes = data.get("scopes")
    if isinstance(scopes, dict):
        items: list = []
        marks: dict = {}
        for sname, scope in scopes.items():
            records = (scope or {}).get("records") or {}
            if not isinstance(records, dict):
                continue
            for uid, rec in records.items():
                if not isinstance(rec, dict) or "name" not in rec:
                    continue
                pick = Pick(
                    name=str(rec.get("name") or ""),
                    sid=str(rec.get("id") or ""),
                    count=int(rec.get("count") or 0),
                    drawn_at=str(rec.get("lastDrawnTime") or ""),
                )
                key = "%s|%s" % (sname, uid)
                items.append((key, pick))
                marks[key] = pick.time
        return "v1", items, marks

    students = data.get("students")
    if isinstance(students, dict):
        items = []
        marks = {}
        for name, rec in students.items():
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(rec, dict):
                continue
            nm = str(rec.get("name") or name).strip()
            hist = rec.get("history")
            stamps = [str(h.get("draw_time") or "") for h in hist
                      if isinstance(h, dict)] if isinstance(hist, list) else []
            last = str(rec.get("last_drawn_time") or "")
            stamps = [s for s in stamps if s] or ([last] if last else [])
            if not stamps:
                continue                  # 从没抽到过，没有时间可判
            pick = Pick(name=nm, sid="",
                        count=int(rec.get("total_count") or len(stamps) or 0),
                        drawn_at=max(stamps))   # 同一格式，字典序＝时间序
            items.append((nm, pick))
            marks[name] = pick.time
        return "v3", items, marks

    items = []
    marks = {}
    for name, cnt in data.items():
        if not isinstance(name, str) or not name.strip():
            continue
        if isinstance(cnt, bool) or not isinstance(cnt, (int, float)):
            continue
        items.append((name, Pick(name=name, sid="", count=int(cnt), drawn_at="")))
        marks[name] = float(cnt)
    return "v2", items, marks


# 上一次看到的指纹：文件路径 → (格式, 指纹表)
_SNAPSHOT: dict = {}


def read_new_picks() -> list[Pick]:
    """读出【这一次新出现】的点名结果，两个版本的安装一起看。

    第一次见到某个文件时只记基线、不返回任何东西，所以插件刚启动
    （或刚开始监听）时不会把历史记录当成刚点到的名字播报出来。
    之后只要某人的指纹变大（3 代是 lastDrawnTime、2 代历史记录是 draw_time、
    2 代 TEMP 是抽中次数），或者文件里冒出从没见过的记录，都算「刚抽到」。
    """
    out: list[Pick] = []
    now_iso = datetime.now().astimezone().isoformat()
    for p in record_files():
        kind, items, marks = _read_file(p)
        if not kind:
            continue
        key = str(p)
        old_kind, old_marks = _SNAPSHOT.get(key, ("", {}))
        _SNAPSHOT[key] = (kind, marks)
        if old_kind != kind or not old_marks:
            continue                      # 第一次见：只建立基线
        for mark, pick in items:
            before = old_marks.get(mark)
            # 指纹变了就是「刚抽到」，从没见过的记录也算：
            #   3 代每次抽取新写一条 uuid 记录，老 uuid 的值不会变；
            #   2 代首次抽到某人时，文件里才会多出这个名字。
            if before is not None and marks[mark] <= before + 1e-6:
                continue
            if kind == "v2":
                if marks[mark] < 1:
                    continue              # 计数还是 0 = 只是被列进文件，没抽到
                # 2 代没有时间戳：用发现时刻代替，供上层比较新旧
                pick.drawn_at = now_iso
            out.append(pick)
    return out


def read_all_picks() -> list[Pick]:
    """读出全部点名记录（所有安装、所有范围，不排序）。"""
    out: list[Pick] = []
    for p in record_files():
        _kind, items, _marks = _read_file(p)
        out.extend(pick for _key, pick in items)
    return out


def read_last_pick() -> Pick | None:
    """所有安装、所有范围里最新的一条（1 代按时间，2 代按文件修改时间）。"""
    best: Pick | None = None
    for p in record_files():
        kind, items, _marks = _read_file(p)
        if not items:
            continue
        if kind == "v2":
            # 2 代没有时间戳，用文件修改时间参与比较
            try:
                stamp = p.stat().st_mtime
            except OSError:
                stamp = 0.0
            items = [(k, Pick(name=pk.name, sid=pk.sid, count=pk.count,
                              drawn_at=datetime.fromtimestamp(stamp)
                              .astimezone().isoformat()))
                     for k, pk in items]
        for _key, pick in items:
            if best is None or pick.time > best.time:
                best = pick
    return best


# 上层一直在用的名字：语义＝「这次新点到的」（首次调用只建基线）
read_last_picks = read_new_picks


# ── 触发 ────────────────────────────────────────────────────────────────────

def build_url(action: str = DEFAULT_ACTION, **params) -> str:
    url = f"{SCHEME}://{(action or DEFAULT_ACTION).strip('/')}"
    if params:
        from urllib.parse import urlencode

        url += "?" + urlencode(params)
    return url


def trigger(action: str = DEFAULT_ACTION, **params) -> str:
    """让 SecRandom 执行一次动作（单向，不等结果）。返回用掉的 URL。"""
    url = build_url(action, **params)
    if os.name == "nt":
        try:
            os.startfile(url)  # type: ignore[attr-defined]
        except OSError as e:
            raise SecRandomError(f"无法唤起 SecRandom（{url}）：{e}") from e
    else:
        subprocess.Popen(["xdg-open", url])  # pragma: no cover
    return url


def draw(
    action: str = DEFAULT_ACTION,
    timeout: float = DEFAULT_TIMEOUT,
    poll: float = POLL_INTERVAL,
    **params,
) -> Pick | None:
    """触发一次点名，并等回新的那条记录。拿不到就返回 None。

    以「触发前最后一条记录的时间」为基准，只有出现更新的记录才算这次的结果。
    """
    before = read_last_pick()
    baseline = before.time if before else 0.0

    trigger(action, **params)

    deadline = time.monotonic() + max(timeout, 0.1)
    while time.monotonic() < deadline:
        time.sleep(poll)
        now = read_last_pick()
        if now is not None and now.time > baseline:
            return now
    return None


# ── 自测 ────────────────────────────────────────────────────────────────────

def _self_test(do_trigger: bool) -> int:
    d = find_install_dir()
    print(f"SecRandom 安装目录: {d}")
    if not d:
        print("✗ 没找到安装目录（注册表与兜底路径都没命中）")
        return 1

    print(f"数据目录:          {data_dir()}")
    rf = record_file()
    print(f"点名记录文件:      {rf}   存在={rf.is_file()}")
    if rf.is_file():
        print(f"                   {rf.stat().st_size} 字节")
    print()

    cur = read_last_pick()
    print(f"当前最新记录: {cur if cur else '（读不到）'}")
    if cur:
        print(f"    时间戳 = {cur.time}  ({cur.drawn_at})")
    print()

    if not do_trigger:
        print("（只读自测结束。要真的触发一次点名请加 --trigger）")
        return 0

    url = build_url(DEFAULT_ACTION)
    print(f"触发: {url}")
    got = draw()
    if got is None:
        print("✗ 超时：没有等到更新的记录。")
        print("  可能原因：动作名不对（试试 quick_draw / lottery），")
        print("  或 SecRandom 未运行，或它没有把这个动作写进记录文件。")
        return 1
    print(f"✓ 这次点到的是: {got}")
    return 0


if __name__ == "__main__":
    sys.exit(_self_test("--trigger" in sys.argv))
