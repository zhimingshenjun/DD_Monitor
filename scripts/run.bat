@echo off
chcp 65001 rem utf8
cls
mode con: cols=130 lines=40
SET script_path=%~dp0
color 3E
type %script_path%\ascii.txt
rem Banner
set "START_STR=欢迎使用DD监控室^! 本窗口为监控室的调试窗口，请保持打开。监控室约在5秒后运行。"

echo ****************************************************************************************************
echo %START_STR%
echo ****************************************************************************************************

rem 5秒间隔
timeout 5
cls
%script_path%\DDMonitor.exe