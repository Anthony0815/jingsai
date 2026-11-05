# -*- coding: utf-8 -*-
"""每小时同步守护：登录后常驻，整点跑一次「每日同步并推送.ps1」。

- 内容没变化时，脚本自己会跳过发布（只抓取 + 比对指纹），所以整点跑很轻。
- 单实例：用 logs/hourly.lock 里的 PID 判断，已在跑就退出。
- 电脑睡眠/关机期间不跑，醒来后下一个整点继续（不会补跑错过的每一小时）。

用法：
    pythonw tools/每小时同步.py        # 由启动项调用，无窗口
    python  tools/每小时同步.py --once # 立刻跑一次就退出（调试用）
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)
LOG = LOGS / "hourly.log"
LOCK = LOGS / "hourly.lock"
PS1 = ROOT / "每日同步并推送.ps1"


def log(msg: str) -> None:
    line = "[%s] %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def other_instance_running() -> bool:
    if not LOCK.exists():
        return False
    try:
        pid = int(LOCK.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        return False
    if pid <= 0 or pid == os.getpid():
        return False
    out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                         capture_output=True, text=True, errors="replace")
    return str(pid) in (out.stdout or "")


def run_sync() -> None:
    log("整点触发同步")
    t0 = time.time()
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(PS1)],
        cwd=str(ROOT), capture_output=True)
    tail = (proc.stdout or b"").decode("utf-8", "replace").strip().splitlines()
    for line in tail[-6:]:
        log("  " + line)
    log("同步结束：exit=%s 用时 %.1fs" % (proc.returncode, time.time() - t0))


def next_tick(offset_seconds: int = 20) -> float:
    """下一个整点之后 offset 秒的时间戳。"""
    now = dt.datetime.now()
    tick = (now.replace(minute=0, second=0, microsecond=0)
            + dt.timedelta(hours=1, seconds=offset_seconds))
    return tick.timestamp()


def main() -> int:
    if "--once" in sys.argv:
        LOCK.write_text(str(os.getpid()), encoding="utf-8")
        run_sync()
        return 0

    if other_instance_running():
        log("已有守护进程在跑，本次退出")
        return 0
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    log("每小时同步守护已启动（PID %d）" % os.getpid())

    # 启动时若距离上次同步超过 1 小时，先补一次
    try:
        mark = (ROOT / "data" / ".last-sync").read_text(encoding="utf-8-sig").strip()
        last = dt.datetime.strptime(mark[:19], "%Y-%m-%d %H:%M:%S")
        if (dt.datetime.now() - last).total_seconds() > 3600:
            log("距上次同步已超过 1 小时，先补一次")
            run_sync()
    except Exception as exc:
        log("读取上次同步时间失败（%s），跳过启动补跑" % exc.__class__.__name__)

    while True:
        wait = max(30.0, next_tick() - time.time())
        log("下次触发：%s（%.0f 分钟后）" % (
            dt.datetime.fromtimestamp(next_tick()).strftime("%Y-%m-%d %H:%M:%S"), wait / 60))
        time.sleep(wait)
        try:
            run_sync()
        except Exception as exc:  # 任何异常都不能让守护退出
            log("同步异常：%s: %s" % (exc.__class__.__name__, exc))


if __name__ == "__main__":
    sys.exit(main())
