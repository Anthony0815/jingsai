# -*- coding: utf-8 -*-
"""排查最近的失败：GitHub Actions 运行结论 + PocketBay 部署状态。"""
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

def get(url, token, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": accept,
        "User-Agent": "dsh-agent",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

tok = git_cred()
runs = get("https://api.github.com/repos/Anthony0815/jingsai/actions/runs?per_page=5", tok)
print("== GitHub Actions 最近 5 次 ==")
for r in runs.get("workflow_runs", []):
    print(" #%s %s conclusion=%s event=%s created=%s" % (
        r["run_number"], r["name"], r["conclusion"], r["event"], r["created_at"]))
    if r["conclusion"] != "success":
        jobs = get(r["jobs_url"], tok)
        for j in jobs.get("jobs", []):
            print("    job:", j["name"], j["conclusion"])
            for s in j.get("steps", []):
                if s["conclusion"] not in (None, "success", "skipped"):
                    print("      step FAILED:", s["name"], s["conclusion"])

# PocketBay 最近部署
pb_tok = open(r"C:\Users\ASUS\.pocketbay\token.txt", encoding="utf-8").read().strip()
req = urllib.request.Request(
    "https://pocketbay.com/api/projects/3681/deploy/status",
    headers={"Authorization": "Bearer " + pb_tok, "User-Agent": "dsh-agent"})
with urllib.request.urlopen(req, timeout=60) as r:
    st = json.loads(r.read().decode("utf-8"))
print("\n== PocketBay 最新部署 ==")
print("id=%s status=%s phase=%s finished=%s" % (
    st.get("id"), st.get("status"), st.get("phase"), st.get("finished_at")))
print("failure:", st.get("failure_stage"), st.get("failure_code"), st.get("error"))
