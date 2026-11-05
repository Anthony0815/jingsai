# -*- coding: utf-8 -*-
"""判断 token 是否具备写权限：读 scopes、尝试创建小文件。"""
import base64
import json
import os
import subprocess
import urllib.error
import urllib.request

GIT = r"C:\Program Files\Git\cmd\git.exe"
UA = "Mozilla/5.0 fc-diag"


def token():
    p = subprocess.run([GIT, "credential", "fill"],
                       input=b"protocol=https\nhost=github.com\n\n",
                       capture_output=True, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("password="):
            return line[9:].strip()
    return ""


TOK = token()


def call(method, url, data=None):
    hdrs = {"Authorization": "Bearer " + TOK, "Accept": "application/vnd.github+json",
            "User-Agent": UA, "X-GitHub-Api-Version": "2022-11-28"}
    body = json.dumps(data).encode() if data else None
    if body:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


st, hd, body = call("GET", "https://api.github.com/user")
print("GET /user:", st, "scopes=", hd.get("x-oauth-scopes"), "accepted-perms=",
      hd.get("x-accepted-github-permissions"))

st, hd, body = call("PUT", "https://api.github.com/repos/Anthony0815/jingsai/contents/fc-write-test.txt",
                    {"message": "chore: 写权限自检", "content": base64.b64encode(b"ok\n").decode(),
                     "branch": "main"})
print("PUT new file:", st, body[:200].replace("\n", " "))
