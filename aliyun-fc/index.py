#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阿里云函数计算 FC 入口：抓取 6 个官方来源 → 构建单文件页面 → 发布到 PocketBay。

为什么放在阿里云：函数计算的出口 IP 在国内，能直连省教育厅、辽工大、大连大学
和省双创平台（GitHub Actions 的境外机器连不上后两个，公共 CORS 代理又经常超时）。

部署形态
    Runtime   python3.10（仅用标准库，无第三方依赖）
    Handler   index.handler
    触发器    定时 0 0 8 * * *（Asia/Shanghai），想更勤可改 0 0 * * * *（每小时）
    超时      300 秒
    环境变量  POCKETBAY_TOKEN（必需）、POCKETBAY_PROJECT（默认 3681）

本地自测
    set POCKETBAY_TOKEN=... && python index.py
    set DRY_RUN=1 && python index.py   # 只抓取+构建，不发布
"""
from __future__ import annotations

import json
import os
import re
import ssl
import time
import base64
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("FC_WORKDIR") or "/tmp/site")
LIVE = os.environ.get("SEED_FROM_LIVE", "https://app-ixvf.pocketbay.app/")
PROJECT = os.environ.get("POCKETBAY_PROJECT", "3681")
TOKEN = os.environ.get("POCKETBAY_TOKEN", "").strip()
# GitHub Pages 同步（可选）：有 token 就顺手把 index.html 提交上去，GitHub 会自动重新构建 Pages
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip()
GH_REPO = os.environ.get("GH_REPO", "Anthony0815/jingsai")
GH_BRANCH = os.environ.get("GH_BRANCH", "main")
GH_PATH = os.environ.get("GH_PATH", "index.html")
DRY_RUN = os.environ.get("DRY_RUN", "") not in ("", "0", "false", "False")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
API_BASE = "https://pocketbay.com/api/projects/" + PROJECT

CTX = ssl.create_default_context()
CTX.options |= 0x4  # 容忍部分老旧政务站点的重协商


def _log(msg: str) -> None:
    print("[fc] " + msg, flush=True)


def _request(url: str, data: bytes = None, headers: dict = None, timeout: int = 60,
             method: str = None):
    hdrs = {"User-Agent": UA}
    hdrs.update(headers or {})
    if method is None:
        method = "POST" if data is not None else "GET"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    return urllib.request.urlopen(req, timeout=timeout, context=CTX)


def seed_cache() -> int:
    """把线上页面里内嵌的上一份快照写到 /tmp，作为抓取失败时的兜底缓存。

    函数计算每次冷启动 /tmp 都是空的，没有这一步，某个来源临时失败就会直接少几条。
    顺手把线上 HTML 存一份（WORK/live.html），供「内容没变就不重复发布」比较用。
    """
    target = WORK / "data" / "notices.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _request(LIVE, timeout=45) as resp:
            html = resp.read().decode("utf-8", "replace")
        (WORK / "live.html").write_text(html, encoding="utf-8")
        m = re.search(r"window\.__EMBEDDED_DATA__\s*=\s*(.*?);\s*</script>", html, re.S)
        if not m:
            _log("seed: 线上页面里没找到内嵌数据，跳过缓存")
            return 0
        snapshot = json.loads(m.group(1))
        items = snapshot.get("items", [])
        if not items:
            return 0
        target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
        _log("seed: 已载入上次快照 %d 条（%s）" % (len(items), snapshot.get("generatedAt", "")))
        return len(items)
    except Exception as exc:  # 兜底失败不影响主流程
        _log("seed: 跳过（%s: %s）" % (exc.__class__.__name__, str(exc)[:80]))
        return 0


def page_fingerprint(html: str) -> dict:
    """取页面里的 build / data-digest 两个 meta，用于判断「线上是否已经是这份内容」。"""
    out = {}
    for name in ("build", "data-digest"):
        m = re.search(r'<meta name="%s" content="([^"]*)"' % name, html)
        out[name] = m.group(1) if m else ""
    return out


def run_scrape() -> dict:
    os.environ["SITE_ROOT"] = str(WORK)
    os.environ["DATA_FILE"] = str(WORK / "data" / "notices.json")
    import sys

    for p in (str(BASE), str(BASE / "scraper"), str(BASE / "tools")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import scrape  # noqa: E402  (仓库里的 scraper/scrape.py)

    scrape.main()
    return json.loads((WORK / "data" / "notices.json").read_text(encoding="utf-8"))


def run_build() -> Path:
    os.environ["SITE_ROOT"] = str(BASE)
    os.environ["DATA_FILE"] = str(WORK / "data" / "notices.json")
    os.environ["OUT_HTML"] = str(WORK / "index.html")
    import sys

    sys.path.insert(0, str(BASE / "tools"))
    import build_page  # noqa: E402

    build_page.main()
    return WORK / "index.html"


def make_zip(html: Path) -> Path:
    zpath = WORK / "site.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(html, "index.html")
    return zpath


def push_github(html_path: Path, stamp: str) -> str:
    """把 index.html 提交到 GitHub 仓库（Contents API），提交后 Pages 会自动重新构建。"""
    if not GH_TOKEN:
        return "skipped(no GH_TOKEN)"
    api = "https://api.github.com/repos/%s/contents/%s" % (GH_REPO, GH_PATH)
    headers = {
        "Authorization": "Bearer " + GH_TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = html_path.read_bytes()
    payload = {
        "message": "chore: 云端同步 %s" % (stamp or ""),
        "content": base64.b64encode(data).decode("ascii"),
        "branch": GH_BRANCH,
    }
    try:
        with _request(api + "?ref=" + GH_BRANCH, headers=headers, timeout=60) as resp:
            cur = json.loads(resp.read().decode("utf-8", "replace"))
        if cur.get("content"):
            try:
                if base64.b64decode(cur["content"]) == data:
                    return "unchanged"
            except Exception:
                pass
        if cur.get("sha"):
            payload["sha"] = cur["sha"]
    except urllib.error.HTTPError as exc:
        if exc.code != 404:  # 404 = 文件还不存在，直接新建
            return "fail(HTTP %s)" % exc.code
    body = json.dumps(payload).encode("utf-8")
    headers2 = dict(headers)
    headers2["Content-Type"] = "application/json; charset=utf-8"
    try:
        with _request(api, data=body, headers=headers2, timeout=120, method="PUT") as resp:
            res = json.loads(resp.read().decode("utf-8", "replace"))
        sha = (res.get("commit") or {}).get("sha", "")
        _log("GitHub 已提交: %s" % sha[:8])
        return "pushed " + sha[:8]
    except Exception as exc:
        return "fail(%s)" % str(exc)[:80]


def deploy(zpath: Path, wait_seconds: int = 240) -> str:
    boundary = "----fc" + uuid.uuid4().hex
    blob = zpath.read_bytes()
    head = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"site.zip\"\r\n"
            "Content-Type: application/zip\r\n\r\n" % boundary).encode("utf-8")
    tail = ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    body = head + blob + tail
    with _request(API_BASE + "/deploy", data=body, timeout=180, headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "multipart/form-data; boundary=" + boundary,
    }) as resp:
        info = json.loads(resp.read().decode("utf-8", "replace"))
    _log("deploy 已提交: id=%s status=%s" % (info.get("id"), info.get("status")))

    deadline, state = time.time() + wait_seconds, "unknown"
    while time.time() < deadline:
        time.sleep(6)
        try:
            with _request(API_BASE + "/deploy/status", timeout=45,
                          headers={"Authorization": "Bearer " + TOKEN}) as resp:
                st = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception:
            continue
        state = "%s/%s" % (st.get("status"), st.get("phase"))
        _log("status=%s phase=%s stage=%s" % (st.get("status"), st.get("phase"),
                                             ">".join(st.get("stage_events") or [])))
        if st.get("phase") == "success" and st.get("status") in ("running", "success"):
            return state
        if st.get("phase") == "failed" or st.get("status") in ("failed", "error"):
            return state
    return state


def handler(event=None, context=None):
    """FC 调用入口。"""
    started = time.time()
    WORK.mkdir(parents=True, exist_ok=True)
    _log("开始: work=%s project=%s dry_run=%s" % (WORK, PROJECT, DRY_RUN))

    seeded = seed_cache()
    snapshot = run_scrape()
    html = run_build()
    counts = snapshot.get("counts", {})
    sources = {s["key"]: "%s/%s" % (s.get("status"), s.get("count")) for s in snapshot.get("sources", [])}
    _log("抓取完成: total=%s cxcy=%s upln=%s dlu=%s sources=%s" % (
        counts.get("total"), counts.get("cxcy"), counts.get("upln"), counts.get("dlu"),
        json.dumps(sources, ensure_ascii=False)))

    result = {
        "generatedAt": snapshot.get("generatedAt"),
        "counts": counts,
        "sources": snapshot.get("sources"),
        "seeded": seeded,
        "htmlBytes": html.stat().st_size,
        "elapsed": round(time.time() - started, 1),
    }

    if DRY_RUN:
        result["deploy"] = "skipped(DRY_RUN)"
        _log("DRY_RUN=1：只抓取和构建，不发布")
        return result

    # 线上已经是同一份内容（同样的构建 + 同样的数据摘要）就不重复提交/部署，
    # 这样改成每小时跑一次也不会刷屏：一天最多只在真有新通知时才发一次。
    local_fp = page_fingerprint(html.read_text(encoding="utf-8"))
    live_file = WORK / "live.html"
    live_fp = page_fingerprint(live_file.read_text(encoding="utf-8")) if live_file.exists() else {}
    result["fingerprint"] = local_fp
    if local_fp["build"] and local_fp == live_fp:
        result["github"] = "skipped(unchanged)"
        result["deploy"] = "skipped(unchanged)"
        _log("内容与线上一致（build=%s data=%s），跳过发布" % (
            local_fp["build"], local_fp["data-digest"]))
        return result

    if os.environ.get("SKIP_DEPLOY", "") in ("1", "true", "True"):
        result["github"] = push_github(html, snapshot.get("generatedAt", ""))
        result["deploy"] = "skipped(SKIP_DEPLOY)"
        _log("SKIP_DEPLOY=1：只做 GitHub 同步，不发布 PocketBay（github=%s）" % result["github"])
        return result

    if not TOKEN:
        # 明确报错，避免「测试函数」看起来成功但其实什么都没发布
        raise RuntimeError(
            "缺少环境变量 POCKETBAY_TOKEN：请在函数配置 → 环境变量里填上 PocketBay 的 API token"
            "（本机路径 C:\\Users\\ASUS\\.pocketbay\\token.txt），然后重新测试函数。"
            " 只想验证抓取可设置 DRY_RUN=1。")

    # GitHub Pages：内容有变化才提交（提交后 GitHub 会自动重建 Pages）
    result["github"] = push_github(html, snapshot.get("generatedAt", ""))
    _log("GitHub 同步结果: %s" % result["github"])

    state = deploy(make_zip(html))
    result["deploy"] = state
    result["elapsed"] = round(time.time() - started, 1)
    ok = state.endswith("/success")
    _log("POCKETBAY_DEPLOY_%s %s" % ("OK" if ok else "FAILED", state))
    if not ok:
        raise RuntimeError("PocketBay 部署未成功: " + state)
    return result


if __name__ == "__main__":
    print(json.dumps(handler({}, None), ensure_ascii=False, indent=1))
