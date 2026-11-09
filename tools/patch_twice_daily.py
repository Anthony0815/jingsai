# -*- coding: utf-8 -*-
"""改成每天两次（08:00 / 20:00）：工作流 cron、页面说明、README。"""
import re
from pathlib import Path

ROOT = Path(r"D:\大肥鱼\jingsai")

# 1) 工作流
wf = ROOT / ".github" / "workflows" / "daily-sync.yml"
t = wf.read_text(encoding="utf-8")
t = t.replace('cron: "0 0 * * *"', 'cron: "0 0,12 * * *"')
t = t.replace("name: 每日同步官方通知", "name: 每日两次同步官方通知")
wf.write_text(t, encoding="utf-8")
print("cron:", "ok" if '0 0,12 * * *' in t else "MISS")

# 2) 页面说明
bp = ROOT / "tools" / "build_page.py"
b = bp.read_text(encoding="utf-8")
old = ('<p>云端每天北京时间 <b>08:00</b> 自动检查一次，抓取官方公开页面；'
       '<b>只有出现新通知或页面本身有更新时才会重新发布</b>，'
       '所以「最近同步」显示的是最近一次真正发生变化的时间。</p>')
new = ('<p>云端每天北京时间 <b>08:00</b> 与 <b>20:00</b> 各自动检查一次，抓取官方公开页面；'
       '<b>只有出现新通知或页面本身有更新时才会重新发布</b>，'
       '所以「最近同步」显示的是最近一次真正发生变化的时间。</p>')
if old in b:
    b = b.replace(old, new)
    bp.write_text(b, encoding="utf-8")
    print("SYNC_NOTE: ok")
else:
    print("SYNC_NOTE: MISS")

# 3) README
rd = ROOT / "README.md"
r = rd.read_text(encoding="utf-8")
pairs = [
    ("每天北京时间 08:00 检查一次官方公开页面", "每天北京时间 08:00 与 20:00 各检查一次官方公开页面"),
    ("每天 UTC 00:00（北京时间 08:00）触发（cron: 0 0 * * *)",
     "每天 UTC 00:00 与 12:00（北京时间 08:00 / 20:00）触发（cron: 0 0,12 * * *）"),
    ("| 每日自动更新 |", "| 每日两次自动更新 |"),
    ("云端照常每天 08:00 跑（不依赖你的电脑）", "云端照常每天 08:00、20:00 跑（不依赖你的电脑）"),
    ("- **云端**（GitHub Actions 与阿里云 FC，每天 08:00）",
     "- **云端**（GitHub Actions 每天 08:00 / 20:00；阿里云 FC 每天 08:00）"),
]
miss = []
for o, n in pairs:
    if o in r:
        r = r.replace(o, n)
    else:
        miss.append(o[:26])
rd.write_text(r, encoding="utf-8")
print("README 未匹配:", miss or "无")
