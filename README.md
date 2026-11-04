# 辽宁省创新创业大赛 · 官方通知聚合

一个自动同步 **辽宁省创新创业大赛** 相关官方通知的静态网页：每天北京时间 08:00 抓取官方公开页面，重新生成页面并发布，标题、日期、链接全部保持官方原文，点击可直接跳转官方网页查看全文。

- 在线访问：https://anthony0815.github.io/jingsai/
- 省级平台入口：https://cxcy.upln.cn/

## 页面能做什么

| 功能 | 说明 |
| --- | --- |
| 通知聚合 | 汇总省教育厅「最新通知 / 公示公告 / 教育要闻」与高校竞赛通知，共 4 个官方来源 |
| 频道筛选 | 全部 / 创新创业 / 大赛活动 / 省厅通知 / 公示公告 / 高校竞赛通知 |
| 标题搜索 | 按大赛、选拔赛、训练计划等关键词即时过滤 |
| 原文跳转 | 每条通知都可直达官方原文页面 |
| 每日自动更新 | GitHub Actions 定时任务，每天 08:00（北京时间）抓取并提交变更 |
| 状态透明 | 显示最近同步时间、下次同步时间、各来源抓取状态与条数 |

## 自动化是怎么跑的

```
.github/workflows/daily-sync.yml   每天 UTC 00:00（北京时间 08:00）触发
        ↓
scraper/scrape.py                  抓取 4 个官方来源 → data/notices.json
        ↓
tools/build_page.py                模板 + 数据 + 样式脚本 → 单文件 index.html
        ↓
commit & push                      GitHub Pages 自动重新发布
```

抓取失败时不会编造内容：该来源沿用上一次的缓存条目，并在页面「数据来源」中标记状态。

也可以手动触发：仓库 **Actions → 每日同步官方通知 → Run workflow**。

## 目录结构

```
index.html                  构建产物，GitHub Pages 直接托管的单文件页面
assets/app.js               前端逻辑（渲染、筛选、搜索、原文抽屉）
assets/style.css            页面样式
tools/page_template.html    页面模板
tools/build_page.py         构建脚本
scraper/scrape.py           抓取脚本（仅用标准库）
data/notices.json           抓取结果快照
.github/workflows/          GitHub Actions 定时任务
```

## 本地运行

```bash
python scraper/scrape.py     # 抓取最新通知
python tools/build_page.py   # 生成 index.html
python -m http.server 8000   # 打开 http://127.0.0.1:8000/
```

## 数据来源

- 辽宁省教育厅 · 最新通知 https://jyt.ln.gov.cn/jyt/gk/zxtz/index.shtml
- 辽宁省教育厅 · 公示公告 https://jyt.ln.gov.cn/jyt/gk/gsgg/index.shtml
- 辽宁省教育厅 · 教育要闻 https://jyt.ln.gov.cn/jyt/jyzx/jyyw/index.shtml
- 辽宁工业大学 · 竞赛通知 https://cxcy.lnut.edu.cn/scjs/jstz.htm

「辽宁省大学生创新创业管理共享平台」（https://cxcy.upln.cn/）为登录后前端渲染的单页应用，接口未公开，因此本站只提供入口链接与连通性检测，不抓取其数据。

## 免责声明

本站仅聚合官方公开页面信息，不做任何改写；报名、评审、获奖等最终以官方发布为准。内容版权归原作者与发布单位所有。
