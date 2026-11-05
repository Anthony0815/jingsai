Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""D:\大肥鱼\jingsai\每日同步并推送.ps1"" -LogonGuard", 0, False
