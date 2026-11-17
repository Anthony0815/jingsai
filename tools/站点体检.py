# -*- coding: utf-8 -*-
"""网站体检：两站可访问性、内嵌数据新鲜度、来源状态、Actions 运行、Pages 构建、本机任务。"""
import json
import re
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
UA = {"User-Agent": "Mozilla/5.0 Chrome/124.0"}


def get(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def pat():
    p = subprocess.run(["git", "credential", "fill"], input=b"protocol=https\nhost=github.com\n\n",
                       capture_output=True)
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    return ""


TOKEN = pat()
print("== 1. 两个线上地址 ==")
pages = {}
for name, url in (("GitHub Pages", "https://anthony0815.github.io/jingsai/?v=hc1"),
                  ("PocketBay", "https://app-ixvf.pocketbay.app/?v=hc1")):
    try:
        code, body = get(url)
        h = body.decode("utf-8", "replace")
        m = re.search(r"window\.__EMBEDDED_DATA__\s*=\s*(.*?);\s*</script>", h, re.S)
        d = json.loads(m.group(1)) if m else {}
        pages[name] = d
        print("%-13s HTTP %s  %6.1f KB  gen=%s  total=%s  next=%s" % (
            name, code, len(body) / 1024, d.get("generatedAt"), d.get("counts", {}).get("total"),
            d.get("nextSync")))
    except Exception as e:
        print("%-13s 访问失败：%s: %s" % (name, type(e).__name__, str(e)[:90]))

if pages:
    d = next(iter(pages.values()))
    print("\n== 2. 六个来源状态（以第一个成功站点为准） ==")
    for s in d.get("sources", []):
        print("   %-24s %-8s %3s 条   最近条目 %s" % (
            s.get("name", "?"), s.get("status"), s.get("count"), s.get("latest", "") or "-"))
    gen = d.get("generatedAt", "")
    if gen:
        t = datetime.strptime(gen, "%Y-%m-%d %H:%M:%S").replace(tzinfo=CST)
        age = datetime.now(CST) - t
        print("\n   数据距现在 %.1f 小时（%.1f 天）" % (age.total_seconds() / 3600, age.total_seconds() / 86400))

    items = d.get("items", [])
    dates = sorted(i.get("date", "") for i in items if i.get("date"))
    print("   条目日期范围：%s ~ %s" % (dates[0] if dates else "-", dates[-1] if dates else "-"))

print("\n== 3. GitHub Actions 最近运行 ==")
try:
    code, body = get("https://api.github.com/repos/Anthony0815/jingsai/actions/runs?per_page=8",
                     {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json"})
    runs = json.loads(body)["workflow_runs"]
    for r in runs:
        print("   %-22s %-10s %s" % (r["created_at"].replace("T", " ")[:19],
                                     r["conclusion"] or r["status"], r["display_title"][:34]))
except Exception as e:
    print("   查询失败：", type(e).__name__, str(e)[:80])

print("\n== 4. GitHub Pages 构建状态 ==")
try:
    code, body = get("https://api.github.com/repos/Anthony0815/jingsai/pages",
                     {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json"})
    p = json.loads(body)
    print("   status=%s  cname=%s  url=%s  build_type=%s" % (
        p.get("status"), p.get("cname"), p.get("html_url"), p.get("build_type")))
except Exception as e:
    print("   查询失败：", type(e).__name__, str(e)[:80])

print("\n== 5. 本机计划任务 ==")
try:
    out = subprocess.run(["schtasks", "/query", "/fo", "csv", "/v"], capture_output=True).stdout.decode("gbk", "replace")
    import csv, io
    for row in csv.DictReader(io.StringIO(out)):
        if "LN-CXCY" in (row.get("TaskName") or ""):
            print("   %-28s %-8s 上次=%s 结果=%s 下次=%s" % (
                row.get("TaskName"), row.get("Status"), row.get("Last Run Time"),
                row.get("Last Result"), row.get("Next Run Time")))
except Exception as e:
    print("   查询失败：", type(e).__name__, str(e)[:80])
