python-vlc 二进制依赖说明
==========================


## Plugin 必备插件

播放一个音视频分为4个步骤

### access 访问
目前的逻辑是先缓存到文件，然后直接播放文件。
故仅保留文件系统的读取模块。

如果要增加其他视频流来源，则需补充对应的插件。（建议直接安装完整版 VLC）

+ access/libfilesystem_plugin

### demux 解复用
文件为 flv 格式，貌似无需解复用。

### decode 解码
+ codec/libdxva2_plugin.dll
+ codec/libavcodec_plugin.dll

### output 输出
**音频**
+ audio_output/libdirectsound_plugin.dll  
    ds 音频输出
+ audio_mixer/libfloat_mixer_plugin.dll  
    浮点数音量。或许可以去掉，取决于音量混合使用的方法

**视频**
+ video_chroma/libswscale_plugin.dll  
    使用 YUV420 == i420
+ video_output/libdirect3d_plugin.dll
+ video_output/libdrawable_plugin.dll
+ video_output/libdirectdraw_plugin.dll  
    硬件加速非必须？


## 参考资料

+ plugin 文件夹的源码： [modules · master · VideoLAN / VLC · GitLab]( https://code.videolan.org/videolan/vlc/-/tree/master/modules )  
  不知道某个动态链接库的功能时，去看源码开头的说明。

+ [VLC源码分析]( https://www.dazhuanlan.com/2020/02/24/5e53abbc6d6fe/ )
+ [VLC框架总结（一）VLC源码及各modules功能介绍]( https://blog.csdn.net/hejjunlin/article/details/77888143 )

