#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取辽宁省创新创业大赛相关的官方公开页面，生成 data/notices.json。

只使用 Python 标准库，供 GitHub Actions 每日定时运行：
    python scraper/scrape.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "notices.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

TZ = dt.timezone(dt.timedelta(hours=8))  # 北京时间
SYNC_HOUR = 8

SOURCES = [
    {"key": "zxtz", "name": "辽宁省教育厅 · 最新通知", "category": "通知公告",
     "url": "https://jyt.ln.gov.cn/jyt/gk/zxtz/index.shtml", "filter": "all"},
    {"key": "gsgg", "name": "辽宁省教育厅 · 公示公告", "category": "公示公告",
     "url": "https://jyt.ln.gov.cn/jyt/gk/gsgg/index.shtml", "filter": "all"},
    {"key": "jyyw", "name": "辽宁省教育厅 · 教育要闻", "category": "赛事动态",
     "url": "https://jyt.ln.gov.cn/jyt/jyzx/jyyw/index.shtml", "filter": "race"},
    {"key": "lnut", "name": "辽宁工业大学 · 竞赛通知", "category": "高校竞赛通知",
     "url": "https://cxcy.lnut.edu.cn/scjs/jstz.htm", "filter": "all",
     "parser": "li", "forceCxcy": True,
     "pages": ["https://cxcy.lnut.edu.cn/scjs/jstz/27.htm"]},
]

KEYWORDS_CXCY = [
    "创新创业", "双创", "互联网+", "挑战杯", "大学生创业", "创新项目",
    "创业项目", "创新大赛", "创业大赛", "训练计划", "创客", "创业孵化",
    "创新方法", "科技成果转化",
]
KEYWORDS_RACE = [
    "大赛", "竞赛", "赛事", "选拔赛", "赛区", "决赛", "初赛", "复赛",
    "路演", "获奖名单", "评审", "参赛", "赛", "评奖", "颁奖",
]
SKIP_TITLE_HINTS = ("无障碍", "网站地图", "返回", "更多", "登录", "注册", "首页")

OFFICIAL_LINKS = [
    {"name": "辽宁省大学生创新创业管理共享平台", "url": "https://cxcy.upln.cn/",
     "desc": "省赛报名、项目申报与评审公示主入口"},
    {"name": "辽宁省教育厅 · 最新通知", "url": "https://jyt.ln.gov.cn/jyt/gk/zxtz/index.shtml",
     "desc": "省级大赛通知、实施方案的权威发布页"},
    {"name": "辽宁省教育厅 · 公示公告", "url": "https://jyt.ln.gov.cn/jyt/gk/gsgg/index.shtml",
     "desc": "获奖名单、评审结果公示"},
    {"name": "全国大学生创业服务网", "url": "https://cy.ncss.cn/",
     "desc": "中国国际大学生创新大赛等国家级赛事官方站点"},
    {"name": "辽宁省教育厅 · 门户首页", "url": "https://jyt.ln.gov.cn/",
     "desc": "省教育厅官方门户"},
]


def ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
        try:
            ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        except Exception:
            pass
    return ctx


CTX = ssl_context()


def fetch(url: str, timeout: int = 30, retries: int = 2) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
                raw = resp.read()
            break
        except Exception as exc:
            last = exc
            if attempt + 1 >= retries:
                raise
    else:  # pragma: no cover
        raise last
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("gb18030", "replace")


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


def tags_for(title: str):
    cxcy = [k for k in KEYWORDS_CXCY if k in title]
    race = [k for k in KEYWORDS_RACE if k in title]
    tags = list(dict.fromkeys(cxcy[:2] + race[:2]))
    return cxcy, tags


def parse_date(*chunks: str) -> str:
    for chunk in chunks:
        m = re.search(r"(20\d{2})[-/年]?(\d{2})[-/月]?(\d{2})", chunk or "")
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                return "%s-%s-%s" % (y, mo, d)
    return ""


def parse_list(text: str, source: dict):
    items = []
    for attrs, inner in re.findall(r"<a\b([^>]*)>(.*?)</a>", text, re.S | re.I):
        hm = re.search(r'href\s*=\s*["\']?([^"\'\s>]+)', attrs, re.I)
        if not hm:
            continue
        href = hm.group(1)
        if not re.search(r"/\d{6,}/?(?:index\.s?html?)?$", href):
            continue
        tm = re.search(r'title\s*=\s*["\']([^"\']+)', attrs, re.I)
        title = clean(tm.group(1) if tm else inner)
        if len(title) < 6 or any(h in title for h in SKIP_TITLE_HINTS):
            continue
        url = urllib.parse.urljoin(source["url"], href)
        date = parse_date(href, inner)
        if not date:
            continue
        cxcy_hits, tags = tags_for(title)
        if source.get("filter") == "race" and not (cxcy_hits or tags):
            continue
        items.append({
            "id": url, "title": title, "url": url, "date": date,
            "sourceKey": source["key"], "source": source["name"],
            "category": source["category"],
            "cxcy": bool(cxcy_hits or source.get("forceCxcy")),
            "tournament": bool(cxcy_hits or tags),
            "tags": tags,
        })
    return items


def parse_list_li(text: str, source: dict):
    items = []
    for block in re.findall(r"<li\b[^>]*>(.*?)</li>", text, re.S | re.I):
        am = re.search(r'<a\b([^>]*)>(.*?)</a>', block, re.S | re.I)
        if not am:
            continue
        attrs, inner = am.group(1), am.group(2)
        hm = re.search(r'href\s*=\s*["\']?([^"\'\s>]+)', attrs, re.I)
        if not hm:
            continue
        href = hm.group(1)
        if not re.search(r"info/\d+/\d+\.s?html?$", href):
            continue
        tm = re.search(r'title\s*=\s*["\']([^"\']+)', attrs, re.I)
        title = clean(tm.group(1) if tm else inner)
        if len(title) < 6 or any(h in title for h in SKIP_TITLE_HINTS):
            continue
        dm = re.search(r"timea?\"?[^>]*>\s*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})", block)
        date = parse_date(dm.group(1) if dm else "", block)
        if not date:
            continue
        url = urllib.parse.urljoin(source["url"], href)
        cxcy_hits, tags = tags_for(title)
        items.append({
            "id": url, "title": title, "url": url, "date": date,
            "sourceKey": source["key"], "source": source["name"],
            "category": source["category"],
            "cxcy": bool(cxcy_hits or source.get("forceCxcy")),
            "tournament": bool(cxcy_hits or tags),
            "tags": tags,
        })
    return items


def next_sync_time(now: dt.datetime) -> str:
    local = now.astimezone(TZ)
    target = local.replace(hour=SYNC_HOUR, minute=0, second=0, microsecond=0)
    if local >= target:
        target += dt.timedelta(days=1)
    return target.strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    previous = {}
    if DATA_FILE.exists():
        try:
            old = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            previous = {x["url"]: x for x in old.get("items", [])}
        except Exception:
            previous = {}

    merged, sources_status = [], []
    for source in SOURCES:
        parser = parse_list_li if source.get("parser") == "li" else parse_list
        pages = [source["url"]] + list(source.get("pages", []))
        got, errors = [], []
        for page_url in pages:
            try:
                got.extend(parser(fetch(page_url), source))
            except Exception as exc:  # 单页失败不影响其它页
                errors.append("%s: %s" % (page_url, exc.__class__.__name__))
        if got:
            merged.extend(got)
            sources_status.append({"key": source["key"], "name": source["name"],
                                   "status": "ok", "count": len(got)})
        else:
            cached = [dict(item, stale=True) for item in previous.values()
                      if item.get("sourceKey") == source["key"]]
            merged.extend(cached)
            sources_status.append({
                "key": source["key"], "name": source["name"],
                "status": "stale" if cached else "fail",
                "count": len(cached),
                "error": "; ".join(errors)[:200] or "no items",
            })

    seen, deduped = set(), []
    for item in merged:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    deduped.sort(key=lambda x: (x.get("date") or "", x.get("title") or ""), reverse=True)
    for item in deduped:
        item["isNew"] = item["url"] not in previous

    platform = {"ok": False, "status": "unknown", "name": "辽宁省大学生创新创业管理共享平台",
                "url": "https://cxcy.upln.cn/"}
    try:
        req = urllib.request.Request("https://cxcy.upln.cn/", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
            platform["ok"] = resp.status == 200
            platform["status"] = "ok" if platform["ok"] else "fail"
    except Exception as exc:
        # 运行环境（如境外 CI）无法完成 TLS 握手时，标记为「未检测」而不是「不可达」
        platform["status"] = "unknown"
        platform["error"] = str(exc)[:160]

    now = dt.datetime.now(dt.timezone.utc)
    snapshot = {
        "generatedAt": now.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "nextSync": next_sync_time(now),
        "items": deduped,
        "counts": {
            "total": len(deduped),
            "cxcy": sum(1 for x in deduped if x.get("cxcy")),
            "tournament": sum(1 for x in deduped if x.get("tournament")),
            "new": sum(1 for x in deduped if x.get("isNew")),
        },
        "sources": sources_status,
        "platform": platform,
        "officialLinks": OFFICIAL_LINKS,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"generatedAt": snapshot["generatedAt"], "counts": snapshot["counts"],
                      "sources": sources_status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
