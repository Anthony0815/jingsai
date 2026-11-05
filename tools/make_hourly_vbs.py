# -*- coding: utf-8 -*-
"""生成「每小时同步」启动项（VBS，GBK 编码），登录后无窗口常驻运行守护进程。

    python tools/make_hourly_vbs.py

写到：%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\每小时同步.vbs
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "每小时同步.py"
STARTUP = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
TARGET = STARTUP / "每小时同步.vbs"


def pythonw() -> str:
    """优先用 pythonw.exe（无控制台窗口）。"""
    exe = Path(sys.executable)
    cand = exe.with_name("pythonw.exe")
    return str(cand if cand.exists() else exe)


VBS = (
    'Set sh = CreateObject("WScript.Shell")\r\n'
    'sh.CurrentDirectory = "%s"\r\n'
    'sh.Run """%s"" ""%s""", 0, False\r\n'
) % (ROOT, pythonw(), SCRIPT)

TARGET.write_bytes(VBS.encode("gbk", "replace"))
print("已写入：%s（%d 字节）" % (TARGET, TARGET.stat().st_size))
print("启动命令：%s %s" % (pythonw(), SCRIPT))
