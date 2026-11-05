#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 PocketBay 项目访问统计（双击 查看访问统计.bat 运行）。

只读脚本：调用 PocketBay 开放接口的 observability 端点，把数字整理成人看得懂的报告。
令牌从 %USERPROFILE%\\.pocketbay\\token.txt 读取，不写进代码。
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

PROJECT_ID = "3681"
BASE = "https://pocketbay.com"
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".pocketbay", "token.txt")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def read_token():
    if not os.path.exists(TOKEN_FILE):
        print("找不到令牌文件: %s" % TOKEN_FILE)
        sys.exit(1)
    with open(TOKEN_FILE, "r", encoding="utf-8-sig") as fh:
        return fh.read().strip()


def fetch(path, token, tries=4):
    """接口偶尔会返回 403（限流），退避重试几次。"""
    last = None
    for attempt in range(tries):
        if attempt:
            time.sleep(2 * attempt)
        req = urllib.request.Request(
            BASE + path,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/json",
                "User-Agent": UA,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in (403, 429, 500, 502, 503, 504):
                raise
        except urllib.error.URLError as exc:
            last = exc
    raise last


def fmt_bytes(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


def line(title):
    print("\n" + title)
    print("-" * 46)


def main():
    token = read_token()
    overview = fetch("/api/observability/projects/%s" % PROJECT_ID, token)
    totals = fetch("/api/observability/overview", token)

    print("PocketBay 访问统计 · 项目 %s（辽宁省创新创业大赛）" % PROJECT_ID)
    print("统计区间: 最近 %s" % overview.get("range", "24h"))

    line("整体")
    print("请求数      : %s" % overview.get("request_count", "-"))
    print("平均速率    : %s 次/分钟" % overview.get("requests_per_min", "-"))
    print("错误数      : %s（错误率 %s）" % (overview.get("error_count", 0), overview.get("error_rate", 0)))
    print("流量        : %s" % overview.get("bytes_human", fmt_bytes(overview.get("bytes_total"))))

    lat = overview.get("latency") or {}
    if lat:
        print("响应耗时    : 平均 %sms / p95 %sms / 最大 %sms"
              % (lat.get("avg_ms"), lat.get("p95_ms"), lat.get("max_ms")))

    line("访客（账号级汇总，含所有项目）")
    t = totals.get("totals") or {}
    print("访客数      : %s" % t.get("visitor_count", "-"))
    print("页面浏览    : %s" % t.get("visit_count", "-"))
    print("请求总数    : %s" % t.get("request_count", "-"))

    for proj in totals.get("projects") or []:
        if str(proj.get("id")) == PROJECT_ID:
            line("本项目访客")
            print("访客数      : %s" % proj.get("visitor_count", "-"))
            print("页面浏览    : %s" % proj.get("visit_count", "-"))
            print("数据来源    : %s（%s）" % (proj.get("visit_source", "-"), proj.get("visit_status", "-")))
            series = proj.get("visit_series") or []
            if series:
                print("最近分布    : %s" % " ".join(str(x) for x in series[-12:]))

    paths = overview.get("top_paths") or []
    if paths:
        line("访问最多的页面")
        for item in paths[:8]:
            print("%-42s %4s 次" % (item.get("path", "-"), item.get("count", 0)))

    series = overview.get("series") or []
    if series:
        line("逐时段请求量（UTC）")
        for point in series[-10:]:
            print("%s  %5s 次  平均 %sms" % (point.get("t", "")[5:16].replace("T", " "),
                                            point.get("count", 0), point.get("avg_ms", "-")))

    errors = overview.get("recent_errors") or []
    line("最近错误")
    print("无" if not errors else "\n".join(str(e) for e in errors[:5]))

    print("\n提示：地区 / 设备类型 / 来源网站 这类维度需要页面接入统计 SDK，")
    print("      PocketBay 目前只提供网关级聚合数据（visit_status 见上）。")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print("查询失败: %s" % exc)
        sys.exit(1)
