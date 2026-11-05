# -*- coding: utf-8 -*-
"""把仓库里的抓取/构建代码打包成阿里云 FC 可直接上传的 zip。

    python D:\\大肥鱼\\aliyun-fc\\build_pkg.py

产物：D:\\大肥鱼\\aliyun-fc\\aliyun-fc-site-sync.zip
包内结构（handler = index.handler）：
    index.py
    scraper/scrape.py
    tools/build_page.py
    tools/page_template.tpl
    assets/app.js
    assets/style.css
"""
import os
import zipfile

FC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(FC_DIR), "jingsai")
OUT = os.path.join(FC_DIR, "aliyun-fc-site-sync.zip")

FILES = [
    ("index.py", os.path.join(FC_DIR, "index.py")),
    ("scraper/scrape.py", os.path.join(REPO, "scraper", "scrape.py")),
    ("tools/build_page.py", os.path.join(REPO, "tools", "build_page.py")),
    ("tools/page_template.tpl", os.path.join(REPO, "tools", "page_template.tpl")),
    ("assets/app.js", os.path.join(REPO, "assets", "app.js")),
    ("assets/style.css", os.path.join(REPO, "assets", "style.css")),
]

missing = [src for _, src in FILES if not os.path.exists(src)]
if missing:
    raise SystemExit("缺少文件：\n" + "\n".join(missing))

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for arc, src in FILES:
        zf.write(src, arc)

print("打包完成：%s（%d 个文件，%.0f KB）" % (OUT, len(FILES), os.path.getsize(OUT) / 1024))
for arc, src in FILES:
    print("  %-26s %6.1f KB" % (arc, os.path.getsize(src) / 1024))
