# -*- coding: utf-8 -*-
"""校验：抽屉优先渲染抓取时存下来的正文；没有正文时回落到跨域提示。"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = str(ROOT / "shots" / "edgeprof")


def dom_of(url: str) -> str:
    page = "file:///" + (ROOT / "index.html").as_posix() + "?view=" + url
    p = subprocess.run(
        [EDGE, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-crash-reporter",
         "--virtual-time-budget=15000", "--user-data-dir=" + PROFILE, "--dump-dom", page],
        capture_output=True, timeout=240,
    )
    return p.stdout.decode("utf-8", "replace")


def strip_scripts(html: str) -> str:
    return re.sub(r"(?is)<script.*?</script>", " ", html)


data = json.loads((ROOT / "data" / "notices.json").read_text(encoding="utf-8"))
items = data["items"]
dlu = next(x for x in items if x.get("sourceKey") == "dlu" and x.get("body"))
upln = next(x for x in items if x.get("sourceKey") == "upln")

ok = True

html = strip_scripts(dom_of(dlu["url"]))
snippet = dlu["body"].split("\n")[0][:24]
checks = [
    ("DLU 抽屉已打开", 'class="drawer"' in html or "drawer-body" in html),
    ("正文首行命中: " + snippet, snippet in html),
    ("正文来源说明", "正文抓取自官方页面" in html or "正文来自上一次抓取的缓存" in html),
    ("跨域提示不再出现", "正文预览暂时读不到" not in html),
]
for name, passed in checks:
    print(("PASS " if passed else "FAIL ") + name)
    ok = ok and passed

html2 = strip_scripts(dom_of(upln["url"]))
checks2 = [
    ("upln 仍显示跨域提示", "该竞赛详情需到双创平台查看" in html2),
    ("upln 按钮可跳官网", "点击前往双创平台查看详情" in html2),
]
for name, passed in checks2:
    print(("PASS " if passed else "FAIL ") + name)
    ok = ok and passed

print("RESULT", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
