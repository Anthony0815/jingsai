# -*- coding: utf-8 -*-
"""诊断 GitHub Contents API：token 是否有效、仓库是否可见、index.html 是否读得到。"""
import json
import os
import subprocess
import urllib.error
import urllib.request

GIT = r"C:\Program Files\Git\cmd\git.exe"


def gh_token():
    p = subprocess.run([GIT, "credential", "fill"],
                       input=b"protocol=https\nhost=github.com\n\n",
                       capture_output=True,
                       env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("password="):
            return line[9:].strip()
    return ""


tok = gh_token()
print("token:", (tok[:4] + "…" + tok[-4:]) if tok else "NONE")

TARGETS = [
    ("GET /user", "https://api.github.com/user"),
    ("GET repo", "https://api.github.com/repos/Anthony0815/jingsai"),
    ("GET contents", "https://api.github.com/repos/Anthony0815/jingsai/contents/index.html?ref=main"),
    ("GET branches", "https://api.github.com/repos/Anthony0815/jingsai/branches"),
]

for name, url in TARGETS:
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + tok,
        "Accept": "application/vnd.github+json",
        "User-Agent": "fc-diag",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read().decode("utf-8", "replace")
        print("%-14s %s %s" % (name, r.status, body[:120].replace("\n", " ")))
    except urllib.error.HTTPError as e:
        print("%-14s HTTP %s %s" % (name, e.code, e.read().decode("utf-8", "replace")[:160]))
    except Exception as e:
        print("%-14s FAIL %s %s" % (name, type(e).__name__, str(e)[:80]))
