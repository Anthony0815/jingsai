# -*- coding: utf-8 -*-
"""检查 GitHub Pages 最近构建与线上页面指纹。"""
import json
import os
import re
import subprocess
import urllib.request

def token() -> str:
    p = subprocess.run(["git", "credential", "fill"], cwd=r"D:\大肥鱼\jingsai",
                       input=b"protocol=https\nhost=github.com\n\n",
                       capture_output=True, env=os.environ)
    m = re.search(rb"password=(.+)", p.stdout)
    return (m.group(1) if m else b"").decode("utf-8", "replace").strip()

TK = token()
HDR = {"Authorization": "Bearer " + TK, "Accept": "application/vnd.github+json",
       "User-Agent": "dsh-check"}

def api(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

try:
    builds = api("https://api.github.com/repos/Anthony0815/jingsai/pages/builds?per_page=3")
    for b in builds:
        print("build", b.get("status"), b.get("created_at"), b.get("commit", "")[:8],
              (b.get("error") or {}).get("message", ""))
except Exception as e:
    print("builds api fail:", type(e).__name__, e)

req = urllib.request.Request("https://anthony0815.github.io/jingsai/?v=e2",
                             headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
with urllib.request.urlopen(req, timeout=60) as r:
    html = r.read().decode("utf-8", "replace")
seen = re.search(r'name="build" content="([^"]+)"', html)
print("gh-pages build =", seen.group(1) if seen else "X",
      "| daily tick:", "2026-11-06 08:00:00" in html,
      "| size KB:", round(len(html.encode()) / 1024))
