# -*- coding: utf-8 -*-
"""README 补充「正文抓取/缓存」说明。"""
from pathlib import Path

p = Path(r"D:\大肥鱼\jingsai\README.md")
text = p.read_text(encoding="utf-8")

old_row = "| 详情抽屉 | 省厅、辽工大条目可在站内预览正文；省双创平台与大连大学条目因跨域限制显示提示，并给出「前往官网查看原文」按钮 |"
new_row = ("| 详情抽屉 | 抓取时把官方正文一并存进数据（当前 102/106 条），点开即可在站内读正文；"
           "抓不到就沿用上次缓存；省双创平台（页面是前端渲染，拿不到正文）仍显示提示 + 「前往官网查看原文」按钮 |")

old_flow = """页面里会写两个指纹："""
new_flow = """正文也在这条链路里一起抓：`scraper/scrape.py` 的 `enrich_bodies()` 对缺正文的条目并发读官方详情页
（每轮最多 45 篇、8 线程、单页 15 秒超时），抽到的正文（单条上限 2400 字）直接写进 `data/notices.json`；
抓取失败就继承上一次快照里的正文并标记 `bodyFrom: "cache"`，所以页面永远不会因为某次抓取失败而变空。
正文不参与发布指纹（避免页面文字上的微小抖动导致每小时都发版），新通知出现时自然会把正文一起带上。

页面里会写两个指纹："""

changed = []
for old, new in ((old_row, new_row), (old_flow, new_flow)):
    if old in text:
        text = text.replace(old, new)
        changed.append("ok")
    else:
        changed.append("miss:" + old[:24])

p.write_text(text, encoding="utf-8")
print("README:", changed)
