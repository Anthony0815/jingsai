#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把模板 + 数据 + 静态资源打包成单文件 index.html（GitHub Pages 直接托管）。

    python tools/build_page.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# 默认在仓库根目录构建；云端函数（阿里云 FC）等只写 /tmp 的环境用环境变量覆盖
ROOT = Path(os.environ.get("SITE_ROOT") or Path(__file__).resolve().parent.parent)
TEMPLATE = ROOT / "tools" / "page_template.tpl"
CSS = ROOT / "assets" / "style.css"
JS = ROOT / "assets" / "app.js"
DATA = Path(os.environ.get("DATA_FILE") or ROOT / "data" / "notices.json")
OUT = Path(os.environ.get("OUT_HTML") or ROOT / "index.html")

SYNC_NOTE = """<div class="card hint">
        <h2>同步说明</h2>
        <p>云端由 <b>GitHub Actions</b> 每天 <b>北京时间 08:00</b> 自动抓取官方公开页面并重新发布；点右上角「<b>立即更新</b>」可当场重新抓取，无需等待下一次定时任务。</p>
        <p>「立即更新」在浏览器里直接读取官方页面，省双创平台接口禁止跨域，该来源沿用上次发布时抓到的结果（标记「沿用缓存」）。</p>
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

    # 静态托管没有后端，但「立即更新」改为浏览器端实时抓取，按钮保留
    html = re.sub(r'<button class="btn primary" id="refreshBtn"[^>]*>.*?</button>',
                  '<button class="btn primary" id="refreshBtn" type="button" '
                  'title="立即抓取官方页面并刷新本页">立即更新</button>', html, flags=re.S)

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
