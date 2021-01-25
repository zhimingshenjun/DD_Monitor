@echo off
pyinstaller DD¼à¿ØÊÒ.spec
mkdir dist\DD¼à¿ØÊÒ\utils
copy utils\config_default.json dist\DD¼à¿ØÊÒ\utils\config.json
copy utils\qdark.qss dist\DD¼à¿ØÊÒ\utils
copy utils\vtb.csv dist\DD¼à¿ØÊÒ\utils
copy utils\splash.jpg dist\DD¼à¿ØÊÒ\utils