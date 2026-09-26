# -*- coding: utf-8 -*-
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
POLL_INTERVAL = 0.25                # 轮询间隔（秒）
DEFAULT_TIMEOUT = 6.0               # 等待新记录的超时（秒）

# 兜底安装目录（注册表读不到时用）
FALLBACK_INSTALL_DIRS = (
    Path(r"F:\SECTL\SecRandom"),
    Path(r"C:\Program Files\SecRandom"),
    Path(r"C:\Program Files (x86)\SecRandom"),
)


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

def find_install_dir() -> Path | None:
    """从注册表的 URL 协议处理器里读出 SecRandom 安装目录。"""
    if os.name == "nt":
        try:
            import winreg  # type: ignore

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Classes\secrandom\shell\open\command",
            ) as k:
                cmd, _ = winreg.QueryValueEx(k, "")
            # 形如: "F:\SECTL\SecRandom\SecRandom.Desktop.exe" --url "%1"
            exe = cmd.strip()
            if exe.startswith('"'):
                exe = exe[1:].split('"', 1)[0]
            else:
                exe = exe.split(" ", 1)[0]
            p = Path(exe)
            if p.is_file():
                return p.parent
        except Exception:
            pass

    for d in FALLBACK_INSTALL_DIRS:
        if d.is_dir():
            return d
    return None


def data_dir() -> Path:
    d = find_install_dir()
    if not d:
        raise SecRandomError(
            "找不到 SecRandom 安装目录。"
            "请确认 SecRandom 已安装并注册了 secrandom:// 协议。"
        )
    return d / "data"


def record_file() -> Path:
    return data_dir().joinpath(*RECORD_SUBDIR) / RECORD_FILE_NAME


# ── 读记录 ──────────────────────────────────────────────────────────────────

def read_all_picks() -> list[Pick]:
    """读出记录文件里的全部点名记录（不排序）。"""
    p = record_file()
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return []
    out: list[Pick] = []
    scopes = data.get("scopes") or {}
    if not isinstance(scopes, dict):
        return []
    for scope in scopes.values():
        records = (scope or {}).get("records") or {}
        if not isinstance(records, dict):
            continue
        for rec in records.values():
            if not isinstance(rec, dict) or "name" not in rec:
                continue
            out.append(
                Pick(
                    name=str(rec.get("name") or ""),
                    sid=str(rec.get("id") or ""),
                    count=int(rec.get("count") or 0),
                    drawn_at=str(rec.get("lastDrawnTime") or ""),
                )
            )
    return out


def read_last_picks() -> list[Pick]:
    """读出最近这一次点名的【全部】人。

    SecRandom 一次抽多人时，这些记录的 lastDrawnTime 完全相同，
    所以取最大的时间戳，把所有同一时刻的人都返回。
    """
    picks = read_all_picks()
    if not picks:
        return []
    newest = max(p.time for p in picks)
    return [p for p in picks if abs(p.time - newest) < 0.01 and p.drawn_at]


def read_last_pick() -> Pick | None:
    """读出所有 scope 里 lastDrawnTime 最新的那一条（单人接口，保留兼容）。"""
    p = record_file()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return None

    best: Pick | None = None
    scopes = data.get("scopes") or {}
    if not isinstance(scopes, dict):
        return None
    for scope in scopes.values():
        records = (scope or {}).get("records") or {}
        if not isinstance(records, dict):
            continue
        for rec in records.values():
            if not isinstance(rec, dict) or "name" not in rec:
                continue
            item = Pick(
                name=str(rec.get("name") or ""),
                sid=str(rec.get("id") or ""),
                count=int(rec.get("count") or 0),
                drawn_at=str(rec.get("lastDrawnTime") or ""),
            )
            if best is None or item.time > best.time:
                best = item
    return best


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
