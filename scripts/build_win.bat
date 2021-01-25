@echo off
pyinstaller DDMonitor.spec
mkdir dist\DDMonitor\utils
copy utils\config_default.json dist\DDMonitor\utils\config.json
copy utils\qdark.qss dist\DDMonitor\utils
copy utils\vtb.csv dist\DDMonitor\utils
copy utils\splash.jpg dist\DDMonitor\utils
copy scripts\run.bat dist\DDMonitor
copy utils\ascii.txt dist\DDMonitor
copy utils\help.html dist\DDMonitor\HELP.html