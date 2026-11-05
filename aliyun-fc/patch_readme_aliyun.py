# -*- coding: utf-8 -*-
"""在仓库 README 末尾追加「阿里云函数计算」章节（幂等）。"""
import io
import os

README = r"D:\大肥鱼\jingsai\README.md"

SECTION = """
## 九、可选：阿里云函数计算（让更新不依赖本机）

`D:\\大肥鱼\\aliyun-fc\\` 是一套可以直接传到阿里云函数计算 FC 的代码包：
`aliyun-fc-site-sync.zip`（26 KB，纯标准库，handler = `index.handler`）。

它每天北京时间 08:00 在阿里云上跑一次「抓取 6 个官方来源 → 构建 → 发布到 PocketBay」。
阿里云出口 IP 在国内，能直连省教育厅、辽工大、**大连大学**和**省双创平台**，
因此这条链路拿到的是全部 6 个来源，不像 GitHub Actions 那样有 2 个来源要标「沿用缓存」。

部署步骤见 `D:\\大肥鱼\\aliyun-fc\\部署说明.md`（控制台约 3 分钟：上传 zip、填 `index.handler`、
配 `POCKETBAY_TOKEN` 环境变量、加定时触发器 `0 0 8 * * *` / Asia/Shanghai）。
改完页面代码后运行 `python D:\\大肥鱼\\aliyun-fc\\build_pkg.py` 重新打包再上传即可。
"""

if os.path.exists(README):
    text = io.open(README, encoding="utf-8").read()
    if "阿里云函数计算" in text:
        print("README 已包含该章节，跳过")
    else:
        io.open(README, "w", encoding="utf-8").write(text.rstrip() + "\n" + SECTION)
        print("已追加，当前长度", len(text) + len(SECTION))
else:
    print("README 不存在：", README)
