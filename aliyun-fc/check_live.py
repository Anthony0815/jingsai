# -*- coding: utf-8 -*-
"""检查上线页面：数据时间、条目数、关键文案。"""
import re
import ssl
import urllib.request

URLS = ["https://app-ixvf.pocketbay.app/", "https://anthony0815.github.io/jingsai/"]
ctx = ssl.create_default_context()
ctx.options |= 0x4

for url in URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as exc:
        print(url, "FAIL", exc)
        continue
    gen = re.search(r'"generatedAt":\s*"([^"]+)"', html)
    total = re.search(r'"total":\s*(\d+)', html)
    dlu = re.search(r'"dlu":\s*(\d+)', html)
    print("%-42s bytes=%d gen=%s total=%s dlu=%s" % (
        url, len(html), gen.group(1) if gen else "?", total.group(1) if total else "?",
        dlu.group(1) if dlu else "?"))
