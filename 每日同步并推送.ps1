param([switch]$RunNow)

# 本机每日同步：抓取官方页面 -> 重新构建 index.html -> 通过 GitHub API 推送
# 由 Windows 计划任务 LN-CXCY-GitHubSync 每天 08:00 调用

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

if ($RunNow) {
  Write-Log "手动触发同步"
}

try {
  $dataFile = Join-Path $root "data/notices.json"
  $indexFile = Join-Path $root "index.html"
  $shaFile = Join-Path $root "data/.pushed-sha"
  $lastSha = ""
  if (Test-Path $shaFile) { $lastSha = (Get-Content $shaFile -Raw -Encoding UTF8).Trim() }

  $out = & python "scraper/scrape.py" 2>&1
  Write-Log ("抓取完成: " + ($out -join " "))

  $null = & python "tools/build_page.py" 2>&1
  Write-Log "页面构建完成"

  $new = Get-Content $dataFile -Raw -Encoding UTF8 | ConvertFrom-Json
  $gen = [string]$new.generatedAt
  # 用构建产物的哈希判断是否需要推送（避免因数据文件已被更新而漏推）
  $sha = (Get-FileHash -Path $indexFile -Algorithm SHA256).Hash

  if ($sha -eq $lastSha) {
    Write-Log ("页面无变化，跳过推送（" + $new.counts.total + " 条）")
  } else {
    $push = & (Join-Path $root "tools/push_via_api.ps1") 2>&1
    $pushText = ($push -join " ")
    Write-Log ("推送结果: " + $pushText)
    if ($pushText -match "pushed|no change") {
      Set-Content -Path $shaFile -Value $sha -Encoding UTF8 -NoNewline
    }
  }

  # PocketBay 同步：按 generatedAt 判断，与 GitHub 推送互不影响
  $stampFile = Join-Path $root "data/.pocketbay-stamp"
  $lastPb = ""
  if (Test-Path $stampFile) { $lastPb = (Get-Content $stampFile -Raw -Encoding UTF8).Trim() }
  if ($gen -ne $lastPb) {
    try {
      $pb = & (Join-Path $root "tools/deploy_pocketbay.ps1") -ProjectId 3681 2>&1
      $pbText = ($pb -join " ")
      Write-Log ("PocketBay 部署: " + $pbText)
      if ($pbText -match "POCKETBAY_DEPLOY_OK") {
        Set-Content -Path $stampFile -Value $gen -Encoding UTF8 -NoNewline
      }
    } catch {
      Write-Log ("PocketBay 部署异常（不影响 GitHub）: " + $_.Exception.Message)
    }
  } else {
    Write-Log ("PocketBay 已是同一版本（" + $gen + "），跳过部署")
  }
} catch {
  Write-Log ("同步失败: " + $_.Exception.Message)
  exit 1
}
