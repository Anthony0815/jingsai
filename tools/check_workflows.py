# -*- coding: utf-8 -*-
"""列出 daily-sync 工作流全部运行，定位失败项；并检查仓库内是否有构建异常文件。"""
import json
import re
import subprocess
import urllib.request

def git_cred():
    out = subprocess.run(
        [r"C:\Program Files\Git\cmd\git.exe", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout
    m = re.search(r"password=(.+)", out)
    return m.group(1).strip() if m else ""

def api(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "dsh-agent",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

tok = git_cred()
wfs = api("https://api.github.com/repos/Anthony0815/jingsai/actions/workflows", tok)
print("== workflows ==")
target = None
for w in wfs.get("workflows", []):
    print(" id=%s name=%s state=%s path=%s" % (w["id"], w["name"], w["state"], w["path"]))
    if "daily" in w["path"]:
        target = w

if target:
    runs = api("https://api.github.com/repos/Anthony0815/jingsai/actions/workflows/%s/runs?per_page=10" % target["id"], tok)
    print("\n== %s 最近运行 ==" % target["name"])
    for r in runs.get("workflow_runs", []):
        print(" #%s conclusion=%s event=%s created=%s url=%s" % (
            r["run_number"], r["conclusion"], r["event"], r["created_at"], r["html_url"]))
        if r["conclusion"] not in ("success",):
            jobs = api(r["jobs_url"], tok)
            for j in jobs.get("jobs", []):
                print("    job:", j["name"], j["conclusion"])
                for s in j.get("steps", []):
                    if s["conclusion"] not in (None, "success", "skipped"):
                        print("      FAILED STEP:", s["name"], s["conclusion"])

pages = api("https://api.github.com/repos/Anthony0815/jingsai/pages", tok)
print("\n== Pages ==", pages.get("status"), pages.get("html_url"), "build_type=", pages.get("build_type"))
