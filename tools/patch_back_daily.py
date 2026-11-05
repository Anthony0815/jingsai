# -*- coding: utf-8 -*-
"""工作流与文档：从「每小时」改回「每天 08:00」。"""
from pathlib import Path

wf = Path(r"D:\大肥鱼\jingsai\.github\workflows\daily-sync.yml")
t = wf.read_text(encoding="utf-8")
t = t.replace("name: 每小时同步官方通知", "name: 每日同步官方通知")
t = t.replace('cron: "0 * * * *"', 'cron: "0 0 * * *"')
wf.write_text(t, encoding="utf-8")
print("workflow:", "ok" if '0 0 * * *' in t and "每日同步官方通知" in t else "MISS")

readme = Path(r"D:\大肥鱼\jingsai\README.md")
r = readme.read_text(encoding="utf-8")
pairs = [
    ("每小时（北京时间整点）检查一次官方公开页面，**内容有变化才重新生成并发布**",
     "每天北京时间 08:00 检查一次官方公开页面，**内容有变化才重新生成并发布**"),
    ("| 每小时自动更新 | 云端每小时（整点）检查一次：有变化才提交并部署到 GitHub Pages + PocketBay，没变化只留一行日志；本机每小时守护进程兜底 |",
     "| 每日自动更新 | 云端每天 08:00（北京时间）检查一次：有变化才提交并部署到 GitHub Pages + PocketBay，没变化只留一行日志；本机计划任务同一时间兜底 |"),
    (".github/workflows/daily-sync.yml   每小时整点触发（cron: 0 * * * *）",
     ".github/workflows/daily-sync.yml   每天 UTC 00:00（北京时间 08:00）触发（cron: 0 0 * * *）"),
    ("仓库 **Actions → 每小时同步官方通知 → Run workflow**",
     "仓库 **Actions → 每日同步官方通知 → Run workflow**"),
    ("| 电脑关机 / 休眠 | 云端照常每小时跑（不依赖你的电脑）",
     "| 电脑关机 / 休眠 | 云端照常每天 08:00 跑（不依赖你的电脑）"),
    ("- **云端**（GitHub Actions 与阿里云 FC，每小时）",
     "- **云端**（GitHub Actions 与阿里云 FC，每天 08:00）"),
    ("它每小时（整点）在阿里云上跑一次",
     "它每天北京时间 08:00 在阿里云上跑一次"),
]
miss = []
for old, new in pairs:
    if old in r:
        r = r.replace(old, new)
    else:
        miss.append(old[:28])
readme.write_text(r, encoding="utf-8")
print("README 未匹配:", miss or "无")
