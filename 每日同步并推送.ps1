param([switch]$RunNow, [switch]$Force, [switch]$LogonGuard)

# 本机同步：抓取官方页面 -> 重新构建 index.html -> 推 GitHub + 部署 PocketBay
# 触发方式：
#   1) 每小时守护进程 tools/每小时同步.py（登录后常驻，整点跑一次；内容没变就只检查不发布）
#   2) 计划任务 LN-CXCY-GitHubSync 每天 08:00（错过时由 Windows 补跑）作为兜底
#   3) 登录启动项 开机补跑.vbs（带 -LogonGuard），当天没同步过就补跑一次
#   4) 双击 立即同步.bat（等于带 -RunNow -Force）

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir "sync.log"

function Write-Log($msg) {
  $line = "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $msg
  Add-Content -Path $log -Value $line -Encoding UTF8 -ErrorAction SilentlyContinue
  Write-Output $line
}

if ($RunNow) { Write-Log "手动触发同步" }

$markFile = Join-Path $root "data/.last-sync"
$today = Get-Date -Format "yyyy-MM-dd"
if ($LogonGuard) {
  $lastSync = ""
  if (Test-Path $markFile) { $lastSync = (Get-Content $markFile -Raw -Encoding UTF8).Trim() }
  if ($lastSync -like ($today + "*")) {
    Write-Log ("开机补跑：今天已同步过（" + $lastSync + "），跳过")
    return
  }
  Write-Log "开机补跑：今天还没同步，开始抓取"
}

try {
  $dataFile = Join-Path $root "data/notices.json"
  $indexFile = Join-Path $root "index.html"

  $out = & python "scraper/scrape.py" 2>&1
  Write-Log ("抓取完成: " + ($out -join " "))

  $buildOut = & python "tools/build_page.py" 2>&1
  Write-Log ("页面构建完成: " + (($buildOut | Select-Object -Last 1) -join " "))

  $new = Get-Content $dataFile -Raw -Encoding UTF8 | ConvertFrom-Json

  # 线上指纹（build + data-digest）与本地一致就跳过发布，避免每小时刷提交
  $needPublish = $true
  if (-not $Force) {
    $gate = & python "tools/should_publish.py" 2>&1
    $gateText = ($gate -join " ")
    $gateLines = $gate | Where-Object { $_ -match "^(build|data|结论|读取)" }
    foreach ($l in $gateLines) { Write-Log ("发布判定: " + $l) }
    if ($gateText -match "NEED_PUBLISH=0") { $needPublish = $false }
  } else {
    Write-Log "发布判定: -Force 指定，强制发布"
  }

  if (-not $needPublish) {
    Set-Content -Path $markFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Encoding UTF8 -NoNewline
    Write-Log ("内容与线上一致，跳过发布（" + $new.counts.total + " 条）")
    return
  }

  # GitHub Pages
  $push = & (Join-Path $root "tools/push_via_api.ps1") 2>&1
  Write-Log ("推送结果: " + (($push -join " ").Trim()))

  # PocketBay
  try {
    $pb = & (Join-Path $root "tools/deploy_pocketbay.ps1") -ProjectId 3681 2>&1
    Write-Log ("PocketBay 部署: " + (($pb -join " ").Trim()))
  } catch {
    Write-Log ("PocketBay 部署异常（不影响 GitHub）: " + $_.Exception.Message)
  }

  # 记录最近一次成功同步的时间，供开机补跑判断
  Set-Content -Path $markFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Encoding UTF8 -NoNewline
  Write-Log "本次同步结束"
} catch {
  Write-Log ("同步失败: " + $_.Exception.Message)
  exit 1
}
