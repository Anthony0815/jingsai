# -*- coding: utf-8 -*-
"""对比三个来源：本机直连 / 带 Origin / 经公共代理，看谁能被浏览器读取。"""
import ssl
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
ORIGIN = "https://anthony0815.github.io"

TARGETS = [
    ("省教育厅·最新通知", "https://jyt.ln.gov.cn/jyt/gk/zxtz/index.shtml"),
    ("辽工大·竞赛通知", "https://cxcy.lnut.edu.cn/scjs/jstz.htm"),
    ("大连大学·竞赛通知", "https://cxcy.dlu.edu.cn/kcsj/cxcyjs.htm"),
]

ctx = ssl.create_default_context()
ctx.options |= 0x4


def hit(label, url, headers=None, timeout=40):
    t0 = time.time()
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers=headers or {"User-Agent": UA}),
            timeout=timeout, context=ctx)
        h = {k.lower(): v for k, v in r.headers.items()}
        body = r.read()
        print("  %-14s %s len=%-6d %.1fs ACAO=%s" % (
            label, r.status, len(body), time.time() - t0,
            h.get("access-control-allow-origin", "缺失")))
    except Exception as e:
        print("  %-14s FAIL %-16s %.1fs %s" % (
            label, type(e).__name__, time.time() - t0, str(e)[:50]))


for name, url in TARGETS:
    print("\n== %s ==" % name)
    hit("本机直连", url)
    hit("浏览器式请求", url, {"User-Agent": UA, "Origin": ORIGIN})
    enc = urllib.parse.quote(url, safe="")
    hit("代理 cors.lol", "https://api.cors.lol/?url=" + enc, timeout=30)
    hit("代理 allorigins", "https://api.allorigins.win/raw?url=" + enc, timeout=45)
