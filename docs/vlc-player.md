VLC 播放器调用
==============

仅描述在某个 QFrame 中调用 VLC 播放器的方法。


## VLC 实例化 

```python3
self.instance = vlc.Instance()
```

## Player 实例化
```python3
self.player = self.instance.media_player_new()

# 更多 self.player 的设置 ...

# 绑定到 QFrame
if platform.system() == "Linux": # for Linux using the X Server
    self.mediaplayer.set_xwindow(int(self.videoframe.winId()))
elif platform.system() == "Windows": # for Windows
    self.mediaplayer.set_hwnd(int(self.videoframe.winId()))
elif platform.system() == "Darwin": # for MacOS
    self.mediaplayer.set_nsobject(int(self.videoframe.winId()))

# 设置视频流来源
self.mediaplayer.set_media(self.media)
```

## `self.player.stop()` 的问题
`stop()` 之后 `self.player` 被设置为停止状态[^1][src-libvlc_media_player_stop]。
再次启用时会出现无法单独控制音频的bug。
因此需要重新实例化。

官方的qt例子也是采用先 stop 然后重新实例化的方式[^2][src-qtplayer]。

现在采用将 `stop()` 和重新实例化封装为一个函数的办法解决以上bug。
参见：`VideoWidget.playerRestart()`


[src-libvlc_media_player_stop]: https://code.videolan.org/videolan/vlc/-/blob/3.0.0-git/lib/media_player.c#L1045
[src-qtplayer]: https://code.videolan.org/videolan/vlc/-/blob/3.0.0-git/doc/libvlc/QtPlayer/player.cpp#L119


## 参考资料
+ [doc/libvlc/QtPlayer/player.cpp · 3.0.0-git · VideoLAN / VLC · GitLab]( https://code.videolan.org/videolan/vlc/-/blob/3.0.0-git/doc/libvlc/QtPlayer/player.cpp )
    VLC 官方的 Qt 例子
+ [python-vlc/pyqt5vlc.py at master · oaubert/python-vlc]( https://github.com/oaubert/python-vlc/blob/master/examples/pyqt5vlc.py )
    python-vlc 的 PyQt 例子
