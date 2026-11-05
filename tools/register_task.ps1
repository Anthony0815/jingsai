$ErrorActionPreference = "Stop"

$root = "D:\大肥鱼\jingsai"
$syncScript = Join-Path $root "每日同步并推送.ps1"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $syncScript + '"')

# 触发器 1：每天 08:00
$t1 = New-ScheduledTaskTrigger -Daily -At "08:00"

# 触发器 2：登录后 2 分钟（开机晚了也能补一次）
$t2 = New-ScheduledTaskTrigger -AtLogOn
$t2.Delay = "PT2M"

$set = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
  -MultipleInstances IgnoreNew
$set.Hidden = $true

$prin = New-ScheduledTaskPrincipal -UserId ($env:USERDOMAIN + "\" + $env:USERNAME) `
  -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName "LN-CXCY-GitHubSync" -Action $action `
  -Trigger @($t1, $t2) -Settings $set -Principal $prin -Force | Out-Null

$t = Get-ScheduledTask -TaskName "LN-CXCY-GitHubSync"
"triggers=" + (($t.Triggers | ForEach-Object { $_.CimClass.CimClassName }) -join ",")
"state=" + $t.State
"next=" + (Get-ScheduledTaskInfo -TaskName "LN-CXCY-GitHubSync").NextRunTime
"action=" + $t.Actions[0].Arguments
