# -*- coding: utf-8 -*-
"""从 GitHub 全量恢复 D:\\大肥鱼\\jingsai（按 main 最新提交的 tree 逐文件下载）。"""
import base64
import json
import os
import subprocess
import urllib.request

REPO = "Anthony0815/jingsai"
DEST = r"D:\大肥鱼\jingsai"


def token():
    p = subprocess.run(["git", "credential", "fill"], input=b"protocol=https\nhost=github.com\n\n",
                       capture_output=True)
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("拿不到 GitHub 令牌")


T = token()
H = {"Authorization": "Bearer " + T, "Accept": "application/vnd.github+json", "User-Agent": "restore"}


def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


head = api("/repos/%s/commits/main" % REPO)
sha = head["sha"]
tree = api("/repos/%s/git/trees/%s?recursive=1" % (REPO, sha))
blobs = [n for n in tree["tree"] if n["type"] == "blob"]
print("HEAD %s，文件 %d 个" % (sha[:8], len(blobs)))

os.makedirs(DEST, exist_ok=True)
written = 0
for n in blobs:
    path = os.path.join(DEST, n["path"].replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request("https://api.github.com/repos/%s/git/blobs/%s" % (REPO, n["sha"]),
                                 headers={**H, "Accept": "application/vnd.github.raw"})
    data = urllib.request.urlopen(req, timeout=90).read()
    with open(path, "wb") as f:
        f.write(data)
    written += 1

print("已写入 %d 个文件到 %s" % (written, DEST))
print("HEAD sha =", sha)
