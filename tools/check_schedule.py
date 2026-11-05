# -*- coding: utf-8 -*-
"""检查构建产物里「下次自动同步」的取值（客户端计算，用无头浏览器跑一遍）。"""
import re
import subprocess
from pathlib import Path

ROOT = Path(r"D:\大肥鱼\jingsai")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
page = "file:///" + (ROOT / "index.html").as_posix()
p = subprocess.run(
    [EDGE, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-crash-reporter",
     "--virtual-time-budget=6000", "--user-data-dir=" + str(ROOT / "shots" / "edgeprof"),
     "--dump-dom", page],
    capture_output=True, timeout=240,
)
html = p.stdout.decode("utf-8", "replace")
for label, pat in (("nextSync", r'id="nextSync"[^>]*>([^<]+)<'),
                   ("lastSync", r'id="lastSync"[^>]*>([^<]+)<')):
    m = re.search(pat, html)
    print("%-9s = %s" % (label, m.group(1) if m else "X"))
