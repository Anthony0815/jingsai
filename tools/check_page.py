# -*- coding: utf-8 -*-
"""检查构建后的页面：条目数、状态栏时间、是否有 JS 报错痕迹。"""
import re
import subprocess
from pathlib import Path

ROOT = Path(r"D:\大肥鱼\jingsai")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
(ROOT / "shots").mkdir(exist_ok=True)
page = "file:///" + (ROOT / "index.html").as_posix()

p = subprocess.run(
    [EDGE, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-crash-reporter",
     "--virtual-time-budget=8000", "--user-data-dir=" + str(ROOT / "shots" / "ep"),
     "--dump-dom", page],
    capture_output=True, timeout=300)
html = p.stdout.decode("utf-8", "replace")
(ROOT / "shots" / "dom_check.txt").write_text(html, encoding="utf-8")

print("DOM 长度:", len(html))
for label, pat in (("notices", r'class="notice"'),
                   ("nextSync", r'id="nextSync"[^>]*>([^<]*)<'),
                   ("lastSync", r'id="lastSync"[^>]*>([^<]*)<'),
                   ("total", r'id="totalCount"[^>]*>([^<]*)<')):
    if "(" in pat:
        m = re.search(pat, html)
        print("%-9s = %s" % (label, m.group(1) if m else "X"))
    else:
        print("%-9s 出现 %d 次" % (label, len(re.findall(pat, html))))
