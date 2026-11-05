# -*- coding: utf-8 -*-
"""把 README 与阿里云部署说明里的「每天 08:00」改成「每小时」，并补充去重说明。"""
from pathlib import Path

ROOT = Path(r"D:\大肥鱼\jingsai")
README = ROOT / "README.md"
FC_DOC = Path(r"D:\大肥鱼\aliyun-fc\部署说明.md")

pairs = [
    ("一个自动同步 **辽宁省创新创业大赛** 相关官方通知的静态网页：每天北京时间 08:00 抓取官方公开页面，重新生成页面并发布，",
     "一个自动同步 **辽宁省创新创业大赛** 相关官方通知的静态网页：每小时（北京时间整点）检查一次官方公开页面，**内容有变化才重新生成并发布**，"),
    ("| 每日自动更新 | 云端 GitHub Actions 每天 08:00（北京时间）抓取并提交，同时部署到 PocketBay；本机计划任务同一时间兜底 |",
     "| 每小时自动更新 | 云端每小时（整点）检查一次：有变化才提交并部署到 GitHub Pages + PocketBay，没变化只留一行日志；本机每小时守护进程兜底 |"),
    (".github/workflows/daily-sync.yml   每天 UTC 00:00（北京时间 08:00）触发",
     ".github/workflows/daily-sync.yml   每小时整点触发（cron: 0 * * * *）"),
    ("也可以手动触发：仓库 **Actions → 每日同步官方通知 → Run workflow**。",
     "也可以手动触发：仓库 **Actions → 每小时同步官方通知 → Run workflow**。"),
    ("| 电脑关机 / 休眠，8 点没开 | 云端 GitHub Actions 照常 08:00 跑一次（不依赖你的电脑）：省教育厅 + 辽工大实时更新，省双创平台与大连大学沿用缓存 |",
     "| 电脑关机 / 休眠 | 云端照常每小时跑（不依赖你的电脑）：省教育厅 + 辽工大实时更新，省双创平台与大连大学沿用缓存 |"),
    ("- **云端**（GitHub Actions 每天 08:00）：能实时抓取省教育厅 3 个来源 + 辽宁工业大学；省双创平台与大连大学沿用上一次缓存（页面上标「沿用缓存」）。",
     "- **云端**（GitHub Actions 与阿里云 FC，每小时）：Actions 能实时抓取省教育厅 3 个来源 + 辽宁工业大学；阿里云 FC 还能抓到辽宁工业大学与大连大学；省双创平台会沿用上一次缓存（页面上标「沿用缓存」）。"),
    ("它每天北京时间 08:00 在阿里云上跑一次「抓取 6 个官方来源 → 构建 → 发布到 PocketBay」。",
     "它每小时（整点）在阿里云上跑一次「抓取 6 个官方来源 → 构建 → 同步 GitHub Pages + 发布 PocketBay」，内容没变化会自动跳过发布。"),
    ("""抓取失败时不会编造内容：该来源沿用上一次的缓存条目，并在页面「数据来源」中标记状态。""",
     """抓取失败时不会编造内容：该来源沿用上一次的缓存条目，并在页面「数据来源」中标记状态。

页面里会写两个指纹：`<meta name="build">`（模板 + app.js + style.css）和 `<meta name="data-digest">`（通知数据）。
每次跑完先和线上页面的指纹比一比，**两个都一样就跳过提交与部署**——所以改成每小时跑，也只在真有新通知（或页面代码改动）时才会多出一条提交。"""),
]

text = README.read_text(encoding="utf-8")
missing = []
for old, new in pairs:
    if old not in text:
        missing.append(old[:40])
        continue
    text = text.replace(old, new)
README.write_text(text, encoding="utf-8")
print("README 更新完成，未匹配：", missing or "无")

doc = FC_DOC.read_text(encoding="utf-8")
doc_pairs = [
    ("这一整条链路搬到阿里云上，每天定时跑一次。",
     "这一整条链路搬到阿里云上，每小时（整点）跑一次；线上内容没变化会自动跳过发布。"),
    ("   - 触发周期：`0 0 8 * * *`（秒 分 时 日 月 周 → 每天 08:00:00）\n   - 时区：**Asia/Shanghai**\n   - 想更勤就改成 `0 0 * * * *`（每小时整点），成本依然极低。",
     "   - 触发周期：`0 0 * * * *`（秒 分 时 日 月 周 → 每小时整点）\n   - 时区：**Asia/Shanghai**\n   - 想改回每天一次就用 `0 0 8 * * *`。"),
    ("| **阿里云 FC（本方案）** | 每天 08:00（可改每小时） |",
     "| **阿里云 FC（本方案）** | 每小时整点 |"),
]
for old, new in doc_pairs:
    if old not in doc:
        missing.append("FC:" + old[:30])
        continue
    doc = doc.replace(old, new)
FC_DOC.write_text(doc, encoding="utf-8")
print("部署说明更新完成，未匹配：", missing or "无")
