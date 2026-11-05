# -*- coding: utf-8 -*-
"""把「8 点没开机怎么办」章节插入 README（位于「目录结构」之前）。"""
from pathlib import Path

p = Path(r"D:\大肥鱼\辽宁省创新创业大赛-网站\README.md")
text = p.read_text(encoding="utf-8")
if "8 点没开机怎么办" in text:
    print("already present")
else:
    section = """## 8 点没开机怎么办

三层兜底，正常情况下不需要点任何东西：

| 场景 | 会发生什么 |
| --- | --- |
| 电脑关机 / 休眠，8 点没开 | 云端 GitHub Actions 照常 08:00 跑一次（不依赖你的电脑）：省教育厅 + 辽工大实时更新，省双创平台与大连大学沿用缓存 |
| 11 点、13 点才开机 | ① 计划任务 `LN-CXCY-GitHubSync` 带「错过则尽快启动」，开机后自动补跑；② 登录启动项 `开机补跑.vbs` 后台静默检查，当天若还没同步就立刻补一次（已同步则跳过，不重复跑） |
| 想立刻刷一次 | 双击 `立即同步.bat`；或网页右上角「立即更新」（只抓 4 个公开来源，省双创平台与大连大学受限） |

补跑全程无窗口，过程写入 `logs/sync.log`；补跑完成后网页上「最近同步」会更新。

"""
    text = text.replace("## 目录结构", section + "## 目录结构", 1)
    p.write_text(text, encoding="utf-8")
    print("inserted, chars", len(text))
