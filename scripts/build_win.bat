@echo off
pyinstaller --clean --noconfirm DDMonitor.spec
mkdir dist\DDMonitor\logs
mkdir dist\DDMonitor\utils
copy utils\config_default.json dist\DDMonitor\utils\config.json

rem remove useless dll
del /F /Q dist\DDMonitor\Qt5DBus.dll
del /F /Q dist\DDMonitor\Qt5Network.dll
del /F /Q dist\DDMonitor\Qt5Qml.dll
del /F /Q dist\DDMonitor\Qt5QmlModels.dll
del /F /Q dist\DDMonitor\Qt5Quick.dll
del /F /Q dist\DDMonitor\Qt5Svg.dll
del /F /Q dist\DDMonitor\Qt5WebSockets.dll

del /F /Q dist\DDMonitor\libEGL.dll
del /F /Q dist\DDMonitor\libGLESv2.dll

del /F /Q dist\DDMonitor\opengl32sw.dll
del /F /Q dist\DDMonitor\ucrtbase.dll

del /F /Q dist\DDMonitor\pyexpat.pyd
del /F /Q dist\DDMonitor\_decimal.pyd
del /F /Q dist\DDMonitor\_multiprocessing.pyd
