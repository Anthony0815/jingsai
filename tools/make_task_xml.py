# -*- coding: utf-8 -*-
"""生成 LN-CXCY-GitHubSync 的任务 XML（双触发器：每天 08:00 + 登录后 2 分钟）。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "每日同步并推送.ps1"

XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>每天 08:00 抓取辽宁双创大赛官方通知，推送到 GitHub Pages 与 PocketBay；错过后开机自动补跑</Description>
    <URI>\\LN-CXCY-GitHubSync</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-21-3791682147-1341666057-3747718495-1001</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Hidden>true</Hidden>
    <IdleSettings>
      <Duration>PT10M</Duration>
      <WaitTimeout>PT1H</WaitTimeout>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-11-05T08:00:00+08:00</StartBoundary>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT2M</Delay>
    </LogonTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%s"</Arguments>
    </Exec>
  </Actions>
</Task>
""" % SYNC

out = ROOT / "tools" / "task.xml"
out.write_text(XML, encoding="utf-16")
print("written", out, out.stat().st_size)
