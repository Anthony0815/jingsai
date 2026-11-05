#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判断「这次构建的页面是否需要发布」——线上指纹和本地一致就跳过，避免每小时刷提交。

    python tools/should_publish.py                 # 与默认线上地址比较
    python tools/should_publish.py --live <url>    # 指定线上地址

输出最后一行固定是 `NEED_PUBLISH=1`（要发）或 `NEED_PUBLISH=0`（不用发），
退出码同样 0 / 3，方便 PowerShell、bash、Actions 里判断。
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

DEFAULT_LIVE = "https://app-ixvf.pocketbay.app/"
LOCAL = Path(__file__).resolve().parent.parent / "index.html"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"


def fingerprint(html: str) -> dict:
    out = {}
    for name in ("build", "data-digest"):
        m = re.search(r'<meta name="%s" content="([^"]*)"' % name, html)
        out[name] = m.group(1) if m else ""
    return out


def fetch(url: str, timeout: int = 45) -> str:
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + "nocache=1",
                                headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default=DEFAULT_LIVE)
    ap.add_argument("--file", default=str(LOCAL))
    args = ap.parse_args()

    local_html = Path(args.file).read_text(encoding="utf-8")
    local_fp = fingerprint(local_html)
    if not local_fp["build"]:
        print("本地页面没有 build 指纹（旧产物），按需要发布处理")
        print("NEED_PUBLISH=1")
        return 0

    try:
        live_fp = fingerprint(fetch(args.live))
    except Exception as exc:
        print("读取线上页面失败（%s: %s），保守起见发布一次" % (exc.__class__.__name__, str(exc)[:80]))
        print("NEED_PUBLISH=1")
        return 0

    print("build  本地=%s 线上=%s" % (local_fp["build"], live_fp["build"] or "(无)"))
    print("data   本地=%s 线上=%s" % (local_fp["data-digest"], live_fp["data-digest"] or "(无)"))
    if local_fp == live_fp:
        print("结论：内容与线上一致，本次不发布")
        print("NEED_PUBLISH=0")
        return 3
    print("结论：内容有变化，需要发布")
    print("NEED_PUBLISH=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
