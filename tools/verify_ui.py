# -*- coding: utf-8 -*-
"""校验「即将截止」区块渲染与大连大学抽屉改造（DOM 文本层面）。"""
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ROOT = Path(r"D:\大肥鱼\jingsai")
OUT = Path(r"D:\大肥鱼\jingsai\shots\dom2.txt")


def dump(url, profile):
    cmd = [
        EDGE, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-crash-reporter", "--virtual-time-budget=9000",
        "--user-data-dir=%s" % profile, "--dump-dom", url,
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=180)
    return res.stdout.decode("utf-8", "replace")


def strip_script(html):
    """去掉 <script> 源码，只留渲染后的 DOM 文本，避免把函数体里的字符串当成渲染结果。"""
    return re.sub(r"<script[\s\S]*?</script>", "", html)


base = "file:///D:/%s/index.html" % ROOT.as_posix().replace(" ", "%20").split("D:/")[-1]
base = "file:///D:/%E5%A4%A7%E8%82%A5%E9%B1%BC/jingsai/index.html"

# 1) 普通页面：检查即将截止区块
h1 = strip_script(dump(base, ROOT / "shots" / "ep_dump2"))
soon_open = re.search(r'<section class="soon" id="soon"([^>]*)>', h1)
print("== 首页 ==")
print("soon section tag attrs:", soon_open.group(1).strip() if soon_open else "NOT FOUND")
print("soon-item count:", h1.count("soon-item"))
for m in re.finditer(r'<span class="badge dd ([^"]*)">([^<]+)</span>\s*<strong class="soon-title">([^<]+)', h1):
    print("  soon:", m.group(2).strip(), "|", m.group(3)[:44])
badges = re.findall(r'<span class="badge dd[^"]*">([^<]+)</span>', h1)
print("list dd badges (first 12):", badges[:12])
print("total notices:", h1.count('class="notice"'))

# 2) 大连大学条目抽屉
dlu_url = "https://cxcy.dlu.edu.cn/info/1101/3812.htm"
h2 = strip_script(dump(base + "?view=" + quote(dlu_url, safe=""), ROOT / "shots" / "ep_dump3"))
print("\n== 大连大学抽屉 ==")
for k in ["该通知详情需到大连大学官网查看",
          "点击前往大连大学官网查看原文",
          "该竞赛详情需到双创平台查看",
          "drawer hidden", "xnote"]:
    print(k, "->", h2.find(k))
mm = re.search(r'<section class="drawer"([^>]*)>', h2)
print("drawer attrs:", mm.group(1).strip() if mm else "NOT FOUND")
note = re.search(r'class="drawer-note"[^>]*>([^<]*)<', h2)
print("drawerNote:", note.group(1).strip() if note else "NOT FOUND")
btn = re.search(r'class="xbtn" href="([^"]+)"', h2)
print("xbtn href:", btn.group(1) if btn else "NOT FOUND")

# 3) 省平台条目抽屉（对照）
import json
d = json.loads((ROOT / "data" / "notices.json").read_text(encoding="utf-8"))
up = [i for i in d["items"] if i["sourceKey"] == "upln"][0]
h3 = strip_script(dump(base + "?view=" + quote(up["url"], safe=""), ROOT / "shots" / "ep_dump4"))
print("\n== 省平台抽屉（对照）==")
for k in ["该竞赛详情需到双创平台查看", "点击前往双创平台查看详情", "该通知详情需到大连大学官网查看"]:
    print(k, "->", h3.find(k))

OUT.write_text(h1, encoding="utf-8")
print("\nwritten:", OUT)
