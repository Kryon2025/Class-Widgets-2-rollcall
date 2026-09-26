# -*- coding: utf-8 -*-
r"""SecRandom IPC 客户端（纯标准库，无第三方依赖）。

协议来源：SECTL/SecRandom-CI 的 SecRandom4Ci/Shared/SecRandomIpcSendUrl.cs
    - Windows:    命名管道  \\\\.\\pipe\\<名字>
    - Linux/macOS: unix socket  /tmp/<名字>.sock
    - 编码: UTF-8，一行一个 JSON，以 \n 结尾；响应也是一行 JSON
    - 默认超时: 5 秒

★ 管道名是动态的：实测系统里是 `SecRandom_IPC_SecRandom_3F2A1B0E`，
  末尾 8 位十六进制每次启动都变，所以必须枚举 \\.\pipe\ 发现它，
  不能写死 `SecRandom.secrandom`（那是默认名，实测并未使用）。

前置条件（否则连不上）:
    1. SecRandom >= 2.1.0
    2. 在 SecRandom 的「闪抽 / 即抽」设置里开启 ClassIsland 联动，IPC 服务端才会起

自测:
    python secrandom_ipc.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
import threading

# ── 协议常量 ────────────────────────────────────────────────────────────────
DEFAULT_TIMEOUT = 5.0
URL_SCHEME = "secrandom://"

# 管道名里一定含有的片段（用于枚举时筛选）
PIPE_HINT = "SecRandom"
# 优先匹配的前缀
PIPE_PREFERRED = "SecRandom_IPC_"

# 默认动作名。这几个字符串是从 SecRandom.dll 里扫出来的路由名，
# 但「哪一种对应你要的点名」我没有百分百确认，所以留成可配置项。
ACTION_ROLL_CALL = "roll_call"
ACTION_QUICK_DRAW = "quick_draw"
ACTION_LOTTERY = "lottery"


class SecRandomError(RuntimeError):
    """SecRandom IPC 调用失败。"""


def discover_pipe(debug: bool = False) -> str | None:
    """枚举命名管道，找出 SecRandom 的 IPC 通道全名。"""
    if os.name == "nt":
        try:
            names = os.listdir("\\\\.\\pipe\\")
        except OSError:
            names = []
        if debug:
            print(f"[debug] 管道共 {len(names)} 条")
        cand = [n for n in names if PIPE_HINT in n]
        if debug:
            print(f"[debug] 含 {PIPE_HINT!r} 的: {cand}")
        if not cand:
            return None
        preferred = [n for n in cand if n.startswith(PIPE_PREFERRED)]
        pick = (preferred or cand)[0]
        return "\\\\.\\pipe\\" + pick

    # POSIX
    cand = [p for p in glob.glob("/tmp/*.sock") if PIPE_HINT in os.path.basename(p)]
    return cand[0] if cand else None


def _read_line_with_timeout(fh, timeout: float) -> bytes:
    """在一行上最多等 timeout 秒。Windows 命名管道用不了 select，所以用线程。"""
    box: list[bytes | None] = [None]

    def worker() -> None:
        try:
            box[0] = fh.readline()
        except Exception:
            box[0] = None

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    if box[0] is None:
        raise SecRandomError(
            f"等待 SecRandom 响应超时（{timeout} 秒）。"
            "请确认 SecRandom 已运行、版本 >= 2.1.0，"
            "且已在「闪抽/即抽」设置中启用 ClassIsland 联动。"
        )
    return box[0]


def _call(payload: dict, timeout: float = DEFAULT_TIMEOUT, address: str | None = None) -> dict:
    """发一行 JSON，收回一行 JSON。"""
    address = address or discover_pipe()
    if not address:
        raise SecRandomError(
            "没有找到 SecRandom 的 IPC 通道（已枚举 \\\\.\\pipe\\）。"
            "请确认 SecRandom 已运行、版本 >= 2.1.0，"
            "且已在「闪抽/即抽」设置中启用 ClassIsland 联动。"
        )

    try:
        fh = open(address, "r+b")
    except OSError as e:
        raise SecRandomError(f"无法连接 IPC 通道（{address}）：{e}") from e

    try:
        fh.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        fh.flush()
        raw = _read_line_with_timeout(fh, timeout)
    finally:
        try:
            fh.close()
        except Exception:
            pass

    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8", "ignore"))
    except json.JSONDecodeError as e:
        raise SecRandomError(f"SecRandom 返回的不是合法 JSON：{raw[:200]!r}") from e


def send_url(url: str, timeout: float = DEFAULT_TIMEOUT, address: str | None = None) -> dict:
    """给 SecRandom 发一条命令 URL，返回它的 JSON 响应。"""
    if not url:
        raise SecRandomError("命令 URL 为空")
    return _call({"type": "url", "payload": {"url": url}}, timeout=timeout, address=address)


def build_url(action: str, **params) -> str:
    """拼命令 URL，例如 build_url("roll_call", klass="高一3班")。"""
    url = URL_SCHEME + action.strip("/")
    if params:
        from urllib.parse import urlencode

        url += "?" + urlencode(params)
    return url


def roll_call(action: str = ACTION_ROLL_CALL, **params) -> dict:
    """触发一次点名。action 可配置，默认 roll_call。"""
    return send_url(build_url(action, **params))


def _self_test() -> int:
    addr = discover_pipe(debug=True)
    print(f"\n发现的 IPC 通道: {addr}")
    print(f"命令 URL 协议头: {URL_SCHEME}")
    print()
    if not addr:
        print("✗ 没有找到通道")
        return 1
    try:
        resp = send_url(build_url(ACTION_ROLL_CALL), address=addr)
    except SecRandomError as e:
        print(f"✗ {e}")
        return 1
    print(f"✓ 收到响应: {json.dumps(resp, ensure_ascii=False)[:800]}")
    return 0


if __name__ == "__main__":
    sys.exit(_self_test())
