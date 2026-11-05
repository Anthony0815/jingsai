# -*- coding: utf-8 -*-
"""看线上页面当前显示的状态文字，判断用户看到的「失败」是什么。"""
import re
import ssl
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
ctx = ssl.create_default_context()
ctx.options |= 0x4

for url in ["https://anthony0815.github.io/jingsai/", "https://app-ixvf.pocketbay.app/"]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        text = urllib.request.urlopen(req, timeout=60, context=ctx).read().decode("utf-8", "replace")
    except Exception as exc:
        print(url, "-> ERR", exc)
        continue
    print("==", url, "bytes", len(text))
    gen = re.search(r'"generatedAt":\s*"([^"]+)"', text)
    print("  generatedAt:", gen.group(1) if gen else "?")
    for ok, bad in [("抓取失败", "抓取失败"), ("沿用缓存", "沿用缓存"), ("未检测", "未检测"),
                    ("无法访问", "无法访问"), ("失败", "失败")]:
        idx = [m.start() for m in re.finditer(bad, text)]
        print("  %-6s count=%d %s" % (ok, len(idx), idx[:6]))
    # 数据源状态块
    for m in re.finditer(r'"key":"([a-z]+)".{0,80}?"status":"([a-z]+)"', text):
        print("   source", m.group(1), m.group(2))
