# DD监控室

## 运行指南

确保安装VLC, `HELP.html`内有更多解释。

## 开发指南

推荐在venv/anaconda环境下开发

### 所需包
 - PyQt5
 - requests
 - aiowebsocket
 - python-vlc
 - pyinstaller

### 打包

在 `scripts` 文件夹下有各平台的打包脚本，需要在仓库根目录运行。

## TODO

### 全平台
 - [] 加载热播主播时显示加载状态（在Macos上有明显卡顿）

### Windows平台
 - [] ?

### MacOS平台
 - [] 保证程序打包后附带文件可以被访问
 - [] 添加热播主播后Thread卡死
 - [] 添加主播到播放器后不会继承窗口大小，需要重整layout来激活

### Linux平台