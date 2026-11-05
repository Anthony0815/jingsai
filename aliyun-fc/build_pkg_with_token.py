# -*- coding: utf-8 -*-
"""生成「已内置 token」的 FC 代码包，省去在控制台配环境变量的步骤。

    python D:\\大肥鱼\\aliyun-fc\\build_pkg_with_token.py

内置两把钥匙：
    POCKETBAY_TOKEN  读 ~\\.pocketbay\\token.txt
    GH_TOKEN         读 git credential（GITHUB 的 PAT）

产物：aliyun-fc-site-sync-baked.zip —— 环境变量仍然优先，控制台里配了也不会冲突。
注意：这个 zip 含密钥，只用于上传到你自己的阿里云函数，不要提交到公开仓库。
"""
import io
import os
import subprocess
import zipfile

FC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(os.path.dirname(FC_DIR), "jingsai")
OUT = os.path.join(FC_DIR, "aliyun-fc-site-sync-baked.zip")
GIT = r"C:\Program Files\Git\cmd\git.exe"


def pocketbay_token() -> str:
    path = os.path.expanduser(r"~\.pocketbay\token.txt")
    with io.open(path, encoding="utf-8") as fh:
        return fh.read().strip()


def github_token() -> str:
    proc = subprocess.run(
        [GIT, "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, timeout=60,
        env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    return ""


pb = pocketbay_token()
gh = github_token()
if not pb:
    raise SystemExit("PocketBay token 为空")
if not gh:
    print("警告：没取到 GitHub PAT，GitHub Pages 那一步会被跳过")

with io.open(os.path.join(FC_DIR, "index.py"), encoding="utf-8") as fh:
    index_src = fh.read()

OLD_PB = 'TOKEN = os.environ.get("POCKETBAY_TOKEN", "").strip()'
OLD_GH = 'GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()'
if OLD_PB not in index_src or OLD_GH not in index_src:
    raise SystemExit("index.py 里 token 那两行结构变了，请检查")

index_src = index_src.replace(
    OLD_PB, 'TOKEN = os.environ.get("POCKETBAY_TOKEN", "%s").strip()' % pb)
if gh:
    index_src = index_src.replace(
        OLD_GH, 'GH_TOKEN = os.environ.get("GH_TOKEN", "%s").strip()' % gh)

FILES = [
    ("scraper/scrape.py", os.path.join(REPO, "scraper", "scrape.py")),
    ("tools/build_page.py", os.path.join(REPO, "tools", "build_page.py")),
    ("tools/page_template.tpl", os.path.join(REPO, "tools", "page_template.tpl")),
    ("assets/app.js", os.path.join(REPO, "assets", "app.js")),
    ("assets/style.css", os.path.join(REPO, "assets", "style.css")),
]

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("index.py", index_src)
    for arc, src in FILES:
        zf.write(src, arc)

print("已生成：%s（%.0f KB）" % (OUT, os.path.getsize(OUT) / 1024))
print("  PocketBay token: %s…%s" % (pb[:4], pb[-4:]))
print("  GitHub   token: %s…%s" % (gh[:4], gh[-4:]) if gh else "  GitHub token: 未内置")
