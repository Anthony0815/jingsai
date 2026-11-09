#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把模板 + 数据 + 静态资源打包成单文件 index.html（GitHub Pages 直接托管）。

    python tools/build_page.py

产物里会带两个 meta：
    <meta name="build" content="...">       页面代码指纹（模板 + app.js + style.css）
    <meta name="data-digest" content="..."> 通知数据指纹（items 全量）
发布脚本拿这两个值和线上页面比较，一模一样就不重复提交/部署。
"""
from __future__ import annotations

import hashlib
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
        <p>云端每天北京时间 <b>08:00</b> 与 <b>20:00</b> 各自动检查一次，抓取官方公开页面；<b>只有出现新通知或页面本身有更新时才会重新发布</b>，所以「最近同步」显示的是最近一次真正发生变化的时间。</p>
        <p>想立刻看最新内容，点右上角「<b>立即更新</b>」当场重新抓取，无需等待下一次定时任务。</p>
        <p>「立即更新」在浏览器里直接读取官方页面，省双创平台接口禁止跨域，该来源沿用上次发布时抓到的结果（标记「沿用缓存」）。</p>
      </div>"""


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    snapshot = json.loads(DATA.read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")

    build_id = digest(html + "\n" + css + "\n" + js)[:12]
    items = snapshot.get("items", [])
    # 指纹只覆盖「对读者有意义且稳定」的字段：isNew / state / synopsis 这类
    # 每次抓取都会变（或随时间推移会变）的字段不参与，否则每小时都会误判成「有更新」。
    STABLE = ("id", "sourceKey", "category", "title", "url", "date",
              "deadline", "signupStart", "signupEnd")
    stable_items = [{k: it.get(k) for k in STABLE if it.get(k) not in (None, "", [], {})}
                    for it in items]
    data_digest = digest(json.dumps(stable_items, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")))[:16]

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

    # 同步说明改成云端定时版本
    html = re.sub(r'<div class="card hint">.*?</div>\s*</aside>',
                  SYNC_NOTE + "\n    </aside>", html, flags=re.S)

    html = html.replace(
        "</footer>",
        "  <span>数据更新于 %s（北京时间）</span>\n</footer>" % snapshot.get("generatedAt", ""), 1)

    # 发布判定用的指纹
    html = re.sub(r"<head>",
                  '<head>\n  <meta name="build" content="%s">\n  <meta name="data-digest" content="%s">'
                  % (build_id, data_digest), html, count=1)

    OUT.write_text(html, encoding="utf-8")

    # 静态托管自检：产物不允许残留对外部资源的引用（assets 已全部内联）
    for bad in ('src="app.js"', 'href="style.css"', 'src="../assets/', 'href="../assets/'):
        if bad in html:
            raise SystemExit("构建失败：产物仍引用外部资源 %s" % bad)

    print("index.html 已生成：%d 条通知，%.0f KB（build=%s data=%s）" % (
        len(items), OUT.stat().st_size / 1024, build_id, data_digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
