# -*- coding: utf-8 -*-
"""用无头 Edge dump DOM 到文件，校验页面元素（无 node/playwright 可用）。"""
import subprocess
import sys
from pathlib import Path

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = Path(r"D:\大肥鱼\jingsai\shots\dom.txt")

url = sys.argv[1] if len(sys.argv) > 1 else "file:///D:/大肥鱼/jingsai/index.html"
profile = Path(r"D:\大肥鱼\jingsai\shots\ep_dump")

cmd = [
    EDGE,
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-crash-reporter",
    "--virtual-time-budget=9000",
    "--user-data-dir=%s" % profile,
    "--dump-dom",
    url,
]
res = subprocess.run(cmd, capture_output=True, timeout=180)
html = res.stdout.decode("utf-8", "replace")
OUT.write_text(html, encoding="utf-8")
print("url:", url)
print("len:", len(html))
print("stderr:", res.stderr.decode("utf-8", "replace")[:300])

keys = [
    "noticeList",
    "即将截止",
    "dd-hot",
    "dd-warn",
    'data-mode="static"',
    "该通知详情需到大连大学官网查看",
    "点击前往大连大学官网查看原文",
    "该竞赛详情需到双创平台查看",
]
for k in keys:
    print(k, "->", html.find(k))
