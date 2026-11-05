# -*- coding: utf-8 -*-
"""校验大连大学抽屉的新文案（正文预览暂时读不到 / 打开官方原文）。"""
import re
import subprocess
import urllib.parse

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE = "file:///D:/%E5%A4%A7%E8%82%A5%E9%B1%BC/jingsai/index.html"
DLU = "https://cxcy.dlu.edu.cn/info/1101/3812.htm"
PROFILE = r"D:\大肥鱼\jingsai\shots\ep_dlu3"


def dump(url):
    cmd = [
        EDGE, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--disable-crash-reporter", "--virtual-time-budget=9000",
        "--user-data-dir=" + PROFILE, "--dump-dom", url,
    ]
    html = subprocess.run(cmd, capture_output=True, timeout=200).stdout.decode("utf-8", "replace")
    return re.sub(r"<script[\s\S]*?</script>", "", html)


h = dump(BASE + "?view=" + urllib.parse.quote(DLU, safe=""))
print("== 大连大学抽屉 ==")
for k in ["正文预览暂时读不到", "打开官方原文", "该通知详情需到大连大学官网查看",
          "该竞赛详情需到双创平台查看"]:
    print(" %-16s -> %s" % (k, h.find(k)))

btn = re.search(r'class="xbtn" href="([^"]+)"[^>]*>([^<]+)<', h)
print(" xbtn:", (btn.group(1), btn.group(2)) if btn else "NOT FOUND")

note = re.search(r'class="drawer-note"[^>]*>([^<]*)<', h)
print(" note:", note.group(1).strip() if note else "NOT FOUND")
