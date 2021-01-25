@echo off
pyinstaller --clean --noconfirm DDMonitor.spec
mkdir dist\DDMonitor\logs
mkdir dist\DDMonitor\utils
copy utils\config_default.json dist\DDMonitor\utils\config.json
