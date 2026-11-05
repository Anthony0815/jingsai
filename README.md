# 辽宁省创新创业大赛 · 官方通知聚合

一个自动同步 **辽宁省创新创业大赛** 相关官方通知的静态网页：每天北京时间 08:00 抓取官方公开页面，重新生成页面并发布，标题、日期、链接全部保持官方原文，点击可直接跳转官方网页查看全文。

- 在线访问（GitHub Pages）：https://anthony0815.github.io/jingsai/
- 在线访问（PocketBay）：https://app-ixvf.pocketbay.app/
- 省级平台入口：https://cxcy.upln.cn/

## 页面能做什么

| 功能 | 说明 |
| --- | --- |
| 通知聚合 | 汇总省教育厅「最新通知 / 公示公告 / 教育要闻」、辽宁工业大学、大连大学与省双创平台竞赛，共 6 个官方来源（当前 106 条） |
| 频道筛选 | 全部 / 创新创业 / 大赛活动 / 省厅通知 / 公示公告 / 高校竞赛通知 / 省双创竞赛 / 大连大学竞赛 |
| 报名截止提醒 | 页面顶部「即将截止」列出 7 天内到期的赛事；列表每条带「剩 N 天 / 已截止 / MM-DD 截止」徽章 |
| 标题搜索 | 按大赛、选拔赛、训练计划等关键词即时过滤 |
| 详情抽屉 | 省厅、辽工大条目可在站内预览正文；省双创平台与大连大学条目因跨域限制显示提示，并给出「前往官网查看原文」按钮 |
| 原文跳转 | 每条通知都可直达官方原文页面 |
| 每日自动更新 | 云端 GitHub Actions 每天 08:00（北京时间）抓取并提交，同时部署到 PocketBay；本机计划任务同一时间兜底 |
| 立即更新 | 页面右上角按钮，在访客浏览器里实时抓取 4 个公开来源（省双创平台、大连大学除外） |
| 状态透明 | 显示最近同步时间、下次同步时间、各来源抓取状态与条数 |

## 自动化是怎么跑的

```
.github/workflows/daily-sync.yml   每天 UTC 00:00（北京时间 08:00）触发
        ↓
scraper/scrape.py                  抓取 6 个官方来源 → data/notices.json（含报名截止抽取）
        ↓
tools/build_page.py                模板 + 数据 + 样式脚本 → 单文件 index.html
        ↓
commit & push → GitHub Pages       同时部署到 PocketBay 项目 3681
```

抓取失败时不会编造内容：该来源沿用上一次的缓存条目，并在页面「数据来源」中标记状态。

也可以手动触发：仓库 **Actions → 每日同步官方通知 → Run workflow**。

想在本地立刻同步一次（会顺带更新省双创平台与大连大学数据并发布），**双击 `立即同步.bat`**：
它会跑完「抓取 → 构建 → 推送 → PocketBay 部署」，窗口里能看到每一步结果，跑完按任意键关闭。

> `.ps1` 文件双击默认是用记事本打开的，所以不要双击 `每日同步并推送.ps1`；
> 要么用 `立即同步.bat`，要么右键该 `.ps1` → 使用 PowerShell 运行。

## 报名截止是怎么算出来的

- **省双创平台竞赛**：直接用官方接口返回的 `endTime`，不需要猜测。
- **大连大学条目**：抓取详情页正文，用正则找「截止时间 / 请于…前 / 报名…截至」等表述，取其中的日期；只有月日时按发布年份补全。**抽不到就不显示徽章**，绝不编造日期。
- 每次同步最多为 40 条大连大学条目并发拉取详情页（约 +2 秒），已算过的会随缓存保留。

## 8 点没开机怎么办

三层兜底，正常情况下不需要点任何东西：

| 场景 | 会发生什么 |
| --- | --- |
| 电脑关机 / 休眠，8 点没开 | 云端 GitHub Actions 照常 08:00 跑一次（不依赖你的电脑）：省教育厅 + 辽工大实时更新，省双创平台与大连大学沿用缓存 |
| 11 点、13 点才开机 | ① 计划任务 `LN-CXCY-GitHubSync` 带「错过则尽快启动」，开机后自动补跑；② 登录启动项 `开机补跑.vbs` 后台静默检查，当天若还没同步就立刻补一次（已同步则跳过，不重复跑） |
| 想立刻刷一次 | 双击 `立即同步.bat`；或网页右上角「立即更新」（只抓 4 个公开来源，省双创平台与大连大学受限） |

补跑全程无窗口，过程写入 `logs/sync.log`；补跑完成后网页上「最近同步」会更新。
想再手动补一次也不会有副作用：GitHub 与 PocketBay 各自按页面内容哈希判断，内容没变就跳过推送 / 部署。

## 目录结构

```
index.html                  构建产物，GitHub Pages / PocketBay 直接托管的单文件页面
assets/app.js               前端逻辑（渲染、筛选、搜索、截止提醒、原文抽屉）
assets/style.css            页面样式
tools/page_template.tpl     页面模板（构建用，勿直接部署）
tools/build_page.py         构建脚本
scraper/scrape.py           抓取脚本（仅用标准库）
立即同步.bat                一键同步：抓取 + 构建 + 推送 + 部署
每日同步并推送.ps1          被计划任务 / 登录启动项调用的同步脚本
开机补跑.vbs                登录启动项副本（已装进「启动」文件夹）
查看访问统计.bat            查看 PocketBay 近 24 小时访问量
data/notices.json           抓取结果快照
.github/workflows/          GitHub Actions 定时任务
tools/push_via_api.ps1      通过 GitHub REST API 推送（本机直连 github.com:443 被阻断时用）
tools/deploy_pocketbay.ps1  部署到 PocketBay 项目 3681
tools/make_task_xml.py      生成计划任务 XML（每日 08:00 + 登录后补跑）
tools/register_task.ps1     注册计划任务（需管理员权限）
tools/make_startup_vbs.py   生成登录启动项 开机补跑.vbs
tools/show_stats.py         PocketBay 访问量报表
tools/dump_dom.py           无头 Edge dump DOM（没有 node/playwright 时用它看页面）
tools/verify_ui.py          校验「即将截止」区块与抽屉改造
tools/verify_online.py      校验线上两端内容
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
- 辽宁省双创平台 · 竞赛大厅 https://cxcy.upln.cn/match（接口 /provincial/match/competition/queryShow）
- 辽宁工业大学 · 竞赛通知 https://cxcy.lnut.edu.cn/scjs/jstz.htm
- 大连大学 · 创新创业竞赛 https://cxcy.dlu.edu.cn/kcsj/cxcyjs.htm ＋ 重要通知 https://cxcy.dlu.edu.cn/zxzx/zytz.htm（表格行解析，单独一个「大连大学竞赛」频道）

「辽宁省大学生创新创业管理共享平台」的竞赛大厅接口对浏览器跨域请求返回 403（无 CORS 头），且 GitHub 的境外运行环境无法解析该域名；大连大学网站同样只对中国大陆网络开放（境外 runner 与公开代理都超时）。因此：

- **云端**（GitHub Actions 每天 08:00）：能实时抓取省教育厅 3 个来源 + 辽宁工业大学；省双创平台与大连大学沿用上一次缓存（页面上标「沿用缓存」）。
- **本机**（计划任务 `LN-CXCY-GitHubSync`、登录补跑或双击 `立即同步.bat`）：6 个来源全部实时抓取，抓到的最新内容会一并推送到 GitHub 与 PocketBay。

## PocketBay 部署（项目 3681）

- 访问地址：https://app-ixvf.pocketbay.app/
- 部署令牌：`%USERPROFILE%\.pocketbay\token.txt`（不要外泄，撤销后需重新生成并覆盖该文件）
- 手动部署：`powershell -NoProfile -ExecutionPolicy Bypass -File tools\deploy_pocketbay.ps1 -ProjectId 3681`
- 云端自动部署：GitHub Actions 用仓库密钥 `POCKETBAY_TOKEN`，随每日同步一起发布
- 注意：PocketBay 是快照式托管，页面本身不会自己刷新，内容更新靠上面的部署动作

## 免责声明

本站仅聚合官方公开页面信息，不做任何改写；报名、评审、获奖等最终以官方发布为准。内容版权归原作者与发布单位所有。
