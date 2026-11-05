param([switch]$RunNow, [switch]$Force, [switch]$LogonGuard)

# 本机每日同步：抓取官方页面 -> 重新构建 index.html -> 推送到 GitHub + 部署 PocketBay
# 触发方式：
#   1) 计划任务 LN-CXCY-GitHubSync 每天 08:00；错过时由 Windows 的「错过则尽快启动」补跑
#   2) 登录启动项 开机补跑.vbs（带 -LogonGuard），当天没同步过就补跑一次
#   3) 双击 立即同步.bat（等于带 -RunNow -Force）

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir "sync.log"

function Write-Log($msg) {
  $line = "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $msg
  Add-Content -Path $log -Value $line -Encoding UTF8
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
  $ghFile = Join-Path $root "data/.pushed-sha"
  $pbFile = Join-Path $root "data/.pocketbay-sha"

  $ghSha = ""
  if (Test-Path $ghFile) { $ghSha = (Get-Content $ghFile -Raw -Encoding UTF8).Trim() }
  $pbSha = ""
  if (Test-Path $pbFile) { $pbSha = (Get-Content $pbFile -Raw -Encoding UTF8).Trim() }

  $out = & python "scraper/scrape.py" 2>&1
  Write-Log ("抓取完成: " + ($out -join " "))

  $null = & python "tools/build_page.py" 2>&1
  Write-Log "页面构建完成"

  $new = Get-Content $dataFile -Raw -Encoding UTF8 | ConvertFrom-Json
  $gen = [string]$new.generatedAt
  # 用构建产物哈希判断内容是否真有变化，避免重复提交/重复部署
  $sha = (Get-FileHash -Path $indexFile -Algorithm SHA256).Hash

  # GitHub
  if ($sha -eq $ghSha) {
    Write-Log ("GitHub 无变化，跳过推送（" + $new.counts.total + " 条）")
  } else {
    $push = & (Join-Path $root "tools/push_via_api.ps1") 2>&1
    $pushText = ($push -join " ")
    Write-Log ("推送结果: " + $pushText)
    if ($pushText -match "pushed|no change") {
      Set-Content -Path $ghFile -Value $sha -Encoding UTF8 -NoNewline
    }
  }

  # PocketBay
  if ($sha -eq $pbSha) {
    Write-Log ("PocketBay 已是同一版本，跳过部署（" + $gen + "）")
  } else {
    try {
      $pb = & (Join-Path $root "tools/deploy_pocketbay.ps1") -ProjectId 3681 2>&1
      $pbText = ($pb -join " ")
      Write-Log ("PocketBay 部署: " + $pbText)
      if ($pbText -match "POCKETBAY_DEPLOY_OK") {
        Set-Content -Path $pbFile -Value $sha -Encoding UTF8 -NoNewline
      }
    } catch {
      Write-Log ("PocketBay 部署异常（不影响 GitHub）: " + $_.Exception.Message)
    }
  }

  # 记录最近一次成功同步的时间，供开机补跑判断
  Set-Content -Path $markFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -Encoding UTF8 -NoNewline
  Write-Log "本次同步结束"
} catch {
  Write-Log ("同步失败: " + $_.Exception.Message)
  exit 1
}
