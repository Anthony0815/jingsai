#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把模板 + 数据 + 静态资源打包成单文件 index.html（GitHub Pages 直接托管）。

    python tools/build_page.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "tools" / "page_template.tpl"
CSS = ROOT / "assets" / "style.css"
JS = ROOT / "assets" / "app.js"
DATA = ROOT / "data" / "notices.json"
OUT = ROOT / "index.html"

STATIC_BADGE = '<span class="btn ghost static-badge" title="由 GitHub Actions 每日 08:00 自动抓取">每日 08:00 自动更新</span>'

SYNC_NOTE = """<div class="card hint">
        <h2>同步说明</h2>
        <p>本页由 <b>GitHub Actions</b> 每天 <b>北京时间 08:00</b> 自动抓取官方公开页面并重新发布，无需人工干预。</p>
        <p>若某次抓取失败，该来源会继续显示上一次的缓存内容（标记「沿用缓存」），不会出现编造条目。</p>
      </div>"""


def main() -> int:
    snapshot = json.loads(DATA.read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    payload = json.dumps(snapshot, ensure_ascii=False).replace("</", "<\\/")

    html = html.replace('<link rel="stylesheet" href="style.css">',
                        "<style>\n%s\n</style>" % css)
    html = html.replace(
        '<script src="app.js"></script>',
        "<script>window.__EMBEDDED_DATA__ = %s;</script>\n<script>\n%s\n</script>" % (payload, js))

    # 静态托管没有后端：把「立即同步」按钮换成自动更新标识
    html = re.sub(r'<button class="btn primary" id="refreshBtn"[^>]*>.*?</button>',
                  STATIC_BADGE, html, flags=re.S)

    # 同步说明改成 GitHub Actions 版本
    html = re.sub(r'<div class="card hint">.*?</div>\s*</aside>',
                  SYNC_NOTE + "\n    </aside>", html, flags=re.S)

    html = html.replace(
        "</footer>",
        "  <span>数据更新于 %s（北京时间）</span>\n</footer>" % snapshot.get("generatedAt", ""), 1)

    OUT.write_text(html, encoding="utf-8")

    # 静态托管自检：产物不允许残留对外部资源的引用（assets 已全部内联）
    for bad in ('src="app.js"', 'href="style.css"', 'src="../assets/', 'href="../assets/'):
        if bad in html:
            raise SystemExit("构建失败：产物仍引用外部资源 %s" % bad)

    print("index.html 已生成：%d 条通知，%.0f KB" % (
        len(snapshot.get("items", [])), OUT.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
