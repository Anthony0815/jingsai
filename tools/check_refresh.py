# -*- coding: utf-8 -*-
"""验证「立即更新」按钮：以 ?refresh=1 打开本地构建页，读刷新提示与同步时间。"""
import re
import subprocess
import sys
from pathlib import Path

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ROOT = Path(r"D:\大肥鱼\jingsai")
URL = "file:///D:/%E5%A4%A7%E8%82%A5%E9%B1%BC/jingsai/index.html?refresh=1"

cmd = [
    EDGE, "--headless=new", "--no-sandbox", "--disable-gpu",
    "--disable-crash-reporter", "--hide-scrollbars",
    "--virtual-time-budget=60000",
    "--user-data-dir=%s" % (ROOT / "shots" / "ep_refresh"),
    "--dump-dom", URL,
]
res = subprocess.run(cmd, capture_output=True, timeout=300)
html = res.stdout.decode("utf-8", "replace")
print("dom len:", len(html))

hint = re.search(r'id="refreshHint"[^>]*>([^<]*)<', html)
print("refreshHint:", hint.group(1).strip() if hint else "NOT FOUND")

last = re.search(r'id="lastSync"[^>]*>([^<]*)<', html)
print("lastSync:", last.group(1).strip() if last else "NOT FOUND")

cnt = re.search(r'id="totalCount"[^>]*>([^<]*)<', html)
print("totalCount:", cnt.group(1).strip() if cnt else "NOT FOUND")

badge = re.search(r'id="newCount"[^>]*>([^<]*)<', html)
print("newCount:", badge.group(1).strip() if badge else "NOT FOUND")

for k in ["dd-hot", "soon-item", 'data-tab="dlu"']:
    print(k, "count:", html.count(k))
