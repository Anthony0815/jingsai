#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取辽宁省创新创业大赛相关的官方公开页面，生成 data/notices.json。

只使用 Python 标准库，供 GitHub Actions 每日定时运行：
    python scraper/scrape.py
"""
from __future__ import annotations

import datetime as dt
import html as html_lib
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# 默认在仓库根目录运行；云端函数（阿里云 FC）等只写 /tmp 的环境用环境变量覆盖
ROOT = Path(os.environ.get("SITE_ROOT") or Path(__file__).resolve().parent.parent)
DATA_FILE = Path(os.environ.get("DATA_FILE") or ROOT / "data" / "notices.json")

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
    {"key": "upln", "name": "辽宁省双创平台 · 竞赛大厅", "category": "省双创竞赛",
     "filter": "all", "api": True,
     "url": "https://cxcy.upln.cn/provincial/match/competition/queryShow?pageNo=1&pageSize=100"},
    {"key": "dlu", "name": "大连大学 · 创新创业竞赛", "category": "大连大学竞赛通知",
     "url": "https://cxcy.dlu.edu.cn/kcsj/cxcyjs.htm", "filter": "all",
     "parser": "tr", "forceCxcy": True,
     "pages": ["https://cxcy.dlu.edu.cn/zxzx/zytz.htm"]},
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
    {"name": "大连大学 · 创新创业学院", "url": "https://cxcy.dlu.edu.cn/kcsj/cxcyjs.htm",
     "desc": "大连大学竞赛通知与校内选拔赛公告"},

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


DEADLINE_RES = [
    re.compile(r"截止(?:时间|日期)?\s*[:：]?\s*(20\d{2})\s*[年\-/\.]\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})"),
    re.compile(r"(?:请于|于)\s*(20\d{2})\s*[年\-/\.]\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})\s*(?:前|之前)"),
    re.compile(r"(?:报名|申报|提交|报送|作品提交|材料提交)[^。；]{0,12}?截至\s*(20\d{2})\s*[年\-/\.]\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})"),
]
DEADLINE_MD = re.compile(r"截止(?:时间|日期)?\s*[:：]?\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})")


def extract_deadline(html_text: str, ref_year: int) -> str:
    """从通知正文里抽取「报名截止」日期，抽不到返回空串。"""
    text = clean(html_text)
    for rx in DEADLINE_RES:
        m = rx.search(text)
        if m:
            y, mo, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= mo <= 12 and 1 <= day <= 31:
                return "%04d-%02d-%02d" % (y, mo, day)
    m = DEADLINE_MD.search(text)
    if m:
        mo, day = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12 and 1 <= day <= 31:
            return "%04d-%02d-%02d" % (ref_year, mo, day)
    return ""


def enrich_deadlines(items, source_key="dlu", max_items=40, workers=6):
    """对没有截止日期的条目补抓详情页（并发，失败就跳过）。"""
    from concurrent.futures import ThreadPoolExecutor

    targets = [it for it in items
               if it.get("sourceKey") == source_key and not it.get("deadline")][:max_items]
    if not targets:
        return

    def work(item):
        try:
            page = fetch(item["url"], timeout=12, retries=1)
        except Exception:
            return ""
        year = int((item.get("date") or "2026")[:4])
        return extract_deadline(page, year)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for item, deadline in zip(targets, pool.map(work, targets)):
            if deadline:
                item["deadline"] = deadline


BODY_LIMIT = 2400
BODY_DAYS = 60   # 只给最近 60 天内的通知存正文
BODY_NOISE = re.compile(
    r"^(字号|打印|关闭|分享|扫一扫|【?字体|上一篇|下一篇|相关附件|附件下载|返回顶部|"
    r"浏览次数|点击次数|首页|当前位置|您所在的位置)")
BODY_MARKERS = ('id="vsb_content"', "id='vsb_content'", 'class="v_news_content',
                'class="TRS_Editor', "class='TRS_Editor", 'class="article',
                "class='article", 'class="content', "class='content", 'class="zoom"')


def extract_body(html_text: str) -> str:
    """从官方详情页 HTML 里抽出正文纯文本（不是正文页 / 抓不到就返回空串）。"""
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html_text or "")
    start = -1
    for marker in BODY_MARKERS:
        pos = text.find(marker)
        if pos >= 0 and (start < 0 or pos < start):
            start = pos
    chunk = text[start:start + 90000] if start >= 0 else text[:90000]
    if start >= 0:  # 切点在标签中间，丢掉半个开标签
        cut = chunk.find(">")
        if 0 <= cut < 200:
            chunk = chunk[cut + 1:]
    chunk = re.sub(r"(?is)<br\s*/?>", "\n", chunk)
    chunk = re.sub(r"(?is)</(p|div|li|h[1-6]|tr|section)>", "\n", chunk)
    chunk = re.sub(r"(?s)<[^>]+>", " ", chunk)
    chunk = html_lib.unescape(chunk)
    lines = []
    total = 0
    started = False
    for raw in chunk.split("\n"):
        line = re.sub(r"[ \t\u3000]+", " ", raw).strip()
        if not line or BODY_NOISE.match(line):
            continue
        if len(line) < 4 and not re.search(r"\d", line):
            continue
        if lines and lines[-1] == line:
            continue
        if not started:
            # 正文开头前的导航/面包屑（短、无标点）先跳过
            if len(line) < 14 and not re.search(r"[，。；：、！？]", line):
                continue
            started = True
        lines.append(line)
        total += len(line) + 1
        if total >= BODY_LIMIT:
            break
    if total < 60:  # 太短，多半抓到的是导航而不是正文
        return ""
    return "\n".join(lines)[:BODY_LIMIT]


def enrich_bodies(items, previous_map, max_items=45, workers=8, days=BODY_DAYS):
    """补正文（只保留最近 days 天内的通知）：先继承上次快照，再并发抓详情页。"""
    from concurrent.futures import ThreadPoolExecutor

    cutoff = (dt.datetime.now(TZ).date() - dt.timedelta(days=days)).isoformat()
    fresh = []
    for it in items:
        if (it.get("date") or "") < cutoff:   # 太旧的通知不存正文，避免页面越滚越大
            it.pop("body", None)
            it.pop("bodyFrom", None)
            continue
        prev = previous_map.get(it.get("url")) or {}
        if prev.get("body"):
            it["body"] = prev["body"]
            it["bodyFrom"] = "cache"
        fresh.append(it)

    pending = [it for it in fresh if not it.get("body")]
    pending.sort(key=lambda x: (bool(x.get("isNew")), x.get("date") or ""), reverse=True)
    targets = pending[:max_items]
    if not targets:
        return

    def work(item):
        try:
            return extract_body(fetch(item["url"], timeout=15, retries=1))
        except Exception:
            return ""

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for item, body in zip(targets, pool.map(work, targets)):
            if body:
                item["body"] = body
                item["bodyFrom"] = "live"


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


def parse_list_tr(text: str, source: dict):
    """解析「表格行」结构的高校列表页（如大连大学创新创业学院）。

    每行形如：
      <tr height="26">
        <td><a href="../info/1101/3826.htm" title="标题">…</a></td>
        <td><span class="timestyle…">2026-10-27&nbsp;</span></td>
      </tr>
    """
    items = []
    for block in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, re.S | re.I):
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
        dm = re.search(r"([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})", block)
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


def fetch_json(url: str, timeout: int = 30, retries: int = 2):
    """请求平台的 JSON 接口（需带 Referer/Origin，否则会被网关拦下）。"""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://cxcy.upln.cn/match",
        "Origin": "https://cxcy.upln.cn",
    })
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as exc:
            last = exc
            if attempt + 1 >= retries:
                raise
    raise last  # pragma: no cover


def parse_upln(data, source: dict):
    """解析省双创平台「竞赛大厅」接口返回的竞赛列表。"""
    if isinstance(data, str):
        data = json.loads(data)
    rows = data.get("result") or []
    if isinstance(rows, dict):
        rows = rows.get("records") or []
    now = dt.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    items = []
    for row in rows:
        title = clean(str(row.get("name") or ""))
        cid = str(row.get("id") or "")
        if len(title) < 4 or not cid:
            continue
        start = str(row.get("startTime") or "")[:19]
        end = str(row.get("endTime") or "")[:19]
        date = parse_date(start)
        if not date:
            continue
        if now < start:
            state = "即将开始"
        elif now <= end:
            state = "报名中"
        else:
            state = "已结束"
        items.append({
            "id": "upln_" + cid,
            "title": title,
            "url": "https://cxcy.upln.cn/match/details?comId=" + cid,
            "date": date,
            "sourceKey": source["key"],
            "source": source["name"],
            "category": source["category"],
            "cxcy": True,
            "tournament": True,
            "tags": [state, "省平台"],
            "signupStart": start,
            "signupEnd": end,
            "deadline": end[:10],
            "state": state,
            "synopsis": clean(str(row.get("synopsis") or ""))[:120],
        })
    return items


def next_sync_time(now: dt.datetime) -> str:
    """下一次整点（云端每小时跑一次）。"""
    local = now.astimezone(TZ)
    target = (local.replace(minute=0, second=0, microsecond=0)
              + dt.timedelta(hours=1))
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
    parser_map = {"li": parse_list_li, "tr": parse_list_tr}
    for source in SOURCES:
        parser = parser_map.get(source.get("parser"), parse_list)
        pages = [source["url"]] + list(source.get("pages", []))
        got, errors = [], []
        for page_url in pages:
            try:
                if source.get("api"):
                    got.extend(parse_upln(fetch_json(page_url), source))
                else:
                    got.extend(parser(fetch(page_url), source))
            except Exception as exc:  # 单页失败不影响其它页
                reason = str(exc).strip()
                errors.append(exc.__class__.__name__ + (": " + reason[:60] if reason else ""))
        if got:
            merged.extend(got)
            sources_status.append({"key": source["key"], "name": source["name"],
                                   "status": "ok", "count": len(got)})
        else:
            cached = [dict(item, stale=True) for item in previous.values()
                      if item.get("sourceKey") == source["key"]]
            status = {
                "key": source["key"], "name": source["name"],
                "status": "stale" if cached else "fail",
                "count": len(cached),
            }
            if cached:
                # 有缓存就沿用，不把技术错误写进数据源面板（页面只显示「沿用缓存」）
                status["note"] = "沿用上次缓存（%s）" % ("; ".join(errors)[:80] or "本次未取到")
            else:
                status["error"] = "; ".join(errors)[:160] or "no items"
            merged.extend(cached)
            sources_status.append(status)

    seen, deduped = set(), []
    for item in merged:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)

    deduped.sort(key=lambda x: (x.get("date") or "", x.get("title") or ""), reverse=True)
    for item in deduped:
        item["isNew"] = item["url"] not in previous

    # 补充「报名截止」：省双创平台自带；大连大学逐条读详情页（失败则留空）
    enrich_deadlines(deduped)

    # 补充正文：直接抓官方详情页；抓不到就沿用上一次缓存里的正文
    enrich_bodies(deduped, previous)

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
            "upln": sum(1 for x in deduped if x.get("sourceKey") == "upln"),
            "dlu": sum(1 for x in deduped if x.get("sourceKey") == "dlu"),
            "new": sum(1 for x in deduped if x.get("isNew")),
        },
        "sources": sources_status,
        "platform": platform,
        "officialLinks": OFFICIAL_LINKS,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    c = snapshot["counts"]
    parts = ["%s %s/%s" % (s["key"], s.get("status"), s.get("count"))
             for s in sources_status]
    print("抓取完成 %s | 共 %d 条（创新创业 %d / 大赛 %d）| %s" % (
        snapshot["generatedAt"], c.get("total", 0), c.get("cxcy", 0),
        c.get("tournament", 0), " · ".join(parts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
