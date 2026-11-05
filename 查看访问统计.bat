@echo off
chcp 65001 >nul
set PYTHONUTF8=1
title PocketBay 访问统计 - 辽宁省创新创业大赛
cd /d "%~dp0"
echo.
python "%~dp0tools\show_stats.py"
echo.
echo  --------------------------------------------------
echo    按任意键关闭窗口
echo  --------------------------------------------------
pause >nul
