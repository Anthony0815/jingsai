# -*- coding: utf-8 -*-
"""诊断大连大学站点：本地直连、CORS 头、经公共代理访问。"""
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LIST = "https://cxcy.dlu.edu.cn/kcsj/cxcyjs.htm"
DETAIL = "https://cxcy.dlu.edu.cn/info/1101/3812.htm"

ctx = ssl.create_default_context()
ctx.options |= 0x4


def probe(label, url, headers=None, timeout=40):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        body = r.read()
        dt = time.time() - t0
        h = {k.lower(): v for k, v in r.headers.items()}
        print("%-26s %s len=%-6d %.1fs ACAO=%s" % (
            label, r.status, len(body), dt, h.get("access-control-allow-origin", "-")))
        return body
    except urllib.error.HTTPError as e:
        print("%-26s HTTP %s %.1fs %s" % (label, e.code, time.time() - t0, e.reason))
    except Exception as e:
        print("%-26s FAIL %-18s %.1fs %s" % (label, type(e).__name__, time.time() - t0, str(e)[:70]))
    return None


print("== 1. 本机直连（等同于本机 Python 抓取）==")
probe("direct list", LIST)
probe("direct detail", DETAIL)

print("\n== 2. 模拟浏览器跨域请求（带 Origin 头）==")
probe("list with Origin", LIST, {"User-Agent": UA, "Origin": "https://anthony0815.github.io"})
probe("detail with Origin", DETAIL, {"User-Agent": UA, "Origin": "https://anthony0815.github.io"})

print("\n== 3. 经公共 CORS 代理访问详情页（站内预览走的就是这条路）==")
enc = urllib.parse.quote(DETAIL, safe="")
for name, url in [
    ("cors.lol", "https://api.cors.lol/?url=" + enc),
    ("allorigins", "https://api.allorigins.win/raw?url=" + enc),
    ("codetabs", "https://api.codetabs.com/v1/proxy/?quest=" + enc),
]:
    probe(name, url, timeout=45)
