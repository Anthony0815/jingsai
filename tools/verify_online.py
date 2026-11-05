# -*- coding: utf-8 -*-
"""线上两端校验：新功能标记 + 数据条数 + 同步时间。"""
import json
import re
import ssl
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
URLS = [
    "https://anthony0815.github.io/jingsai/",
    "https://app-ixvf.pocketbay.app/",
]
KEYS = [
    "即将截止",
    "该通知详情需到大连大学官网查看",
    "点击前往大连大学官网查看原文",
    'data-tab="dlu"',
    "dd-hot",
    "drawerDlu",
]
ctx = ssl.create_default_context()
ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

for url in URLS:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        raw = urllib.request.urlopen(req, timeout=60, context=ctx).read()
    except Exception as exc:
        print(url, "-> ERR", type(exc).__name__, exc)
        continue
    text = raw.decode("utf-8", "replace")
    gen = re.search(r'"generatedAt":\s*"([^"]+)"', text)
    tot = re.search(r'"total":\s*(\d+)', text)
    dlu = re.search(r'"dlu":\s*(\d+)', text)
    print(url, "-> HTTP ok", "bytes", len(raw),
          "gen", gen.group(1) if gen else "?",
          "total", tot.group(1) if tot else "?",
          "dlu", dlu.group(1) if dlu else "?")
    for k in KEYS:
        print("   ", k, "->", "yes" if k in text else "NO")
