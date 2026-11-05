# -*- coding: utf-8 -*-
"""测一批公开 CORS 代理对省教育厅列表页的可用性（含 ACAO 头检查）。"""
import ssl
import time
import urllib.parse
import urllib.request

TARGET = "https://jyt.ln.gov.cn/jyt/gk/zxtz/index.shtml"
ENC = urllib.parse.quote(TARGET, safe="")
RAW_ENC = urllib.parse.quote(TARGET, safe="")

CANDIDATES = [
    ("allorigins-raw", "https://api.allorigins.win/raw?url=" + ENC, "raw"),
    ("allorigins-get", "https://api.allorigins.win/get?url=" + ENC, "json"),
    ("codetabs", "https://api.codetabs.com/v1/proxy/?quest=" + ENC, "raw"),
    ("corslol", "https://api.cors.lol/?url=" + ENC, "raw"),
    ("whateverorigin", "http://www.whateverorigin.org/get?url=" + ENC, "json"),
    ("thingproxy", "https://thingproxy.freeboard.io/fetch/" + TARGET, "raw"),
    ("corsproxy-io", "https://corsproxy.io/?url=" + ENC, "raw"),
    ("allorigins-raw2", "https://api.allorigins.win/raw?charset=UTF-8&url=" + ENC, "raw"),
]

ctx = ssl.create_default_context()
ctx.options |= 0x4
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"

for name, url, kind in CANDIDATES:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        r = urllib.request.urlopen(req, timeout=40, context=ctx)
        body = r.read()
        dt = time.time() - t0
        acao = r.headers.get("Access-Control-Allow-Origin", "-")
        txt = body.decode("utf-8", "replace")
        has_list = "jyt/gk/zxtz/20" in txt or "index.shtml" in txt
        print("%-16s %s len=%-7d %.1fs ACAO=%-4s listlike=%s" % (
            name, r.status, len(body), dt, acao, has_list))
    except Exception as exc:
        print("%-16s FAIL %-22s %.1fs %s" % (
            name, type(exc).__name__, time.time() - t0, str(exc)[:70]))
