# -*- coding: utf-8 -*-
"""生成「开机补跑」启动脚本（VBScript，登录后静默执行一次同步兜底）。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "每日同步并推送.ps1"

VBS = (
    'Set sh = CreateObject("WScript.Shell")\r\n'
    'sh.Run "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass '
    '-File ""%s"" -LogonGuard", 0, False\r\n' % SYNC
)

startup = Path(os.path.expandvars(
    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")) / "开机补跑.vbs"
startup.write_bytes(VBS.encode("gbk"))
(ROOT / "开机补跑.vbs").write_bytes(VBS.encode("gbk"))
print("startup:", startup, startup.stat().st_size)
print("repo   :", ROOT / "开机补跑.vbs")
