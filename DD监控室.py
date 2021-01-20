'''
DD监控室主界面进程 包含对所有子页面的初始化、排版管理
同时卡片和播放窗口的交互需要通过主界面线程通信
以及软件启动和退出后的一些操作
新增全局鼠标坐标跟踪 用于刷新鼠标交互效果
'''
import os, sys, json, time, shutil
from PyQt5.Qt import *
from LayoutPanel import LayoutSettingPanel
# from VideoWidget import PushButton, Slider, VideoWidget
from VideoWidget_vlc import PushButton, Slider, VideoWidget
from LiverSelect import LiverPanel

application_path = ""

def _translate(context, text, disambig):
    return QApplication.translate(context, text, disambig)


class ScrollArea(QScrollArea):
    def __init__(self):
        super(ScrollArea, self).__init__()

    def wheelEvent(self, QEvent):
        if QEvent.angleDelta().y() < 0:
            value = self.horizontalScrollBar().value()
            self.horizontalScrollBar().setValue(value + 80)
        elif QEvent.angleDelta().y() > 0:
            value = self.horizontalScrollBar().value()
            self.horizontalScrollBar().setValue(value - 80)


class Version(QWidget):
    def __init__(self):
        super(Version, self).__init__()
        self.resize(350, 150)
        self.setWindowTitle('当前版本')
        layout = QGridLayout(self)
        layout.addWidget(QLabel('DD监控室 v0.11测试版'), 0, 0, 1, 2)
        layout.addWidget(QLabel('by 神君Channel'), 1, 0, 1, 1)
        releases_url = QLabel('')
        releases_url.setOpenExternalLinks(True)
        releases_url.setText(_translate("MainWindow", "<html><head/><body><p><a href=\"https://space.bilibili.com/637783\">\
<span style=\" text-decoration: underline; color:#cccccc;\">https://space.bilibili.com/637783</span></a></p></body></html>", None))
        layout.addWidget(releases_url, 1, 1, 1, 1)


class HotKey(QWidget):
    def __init__(self):
        super(HotKey, self).__init__()
        self.resize(350, 150)
        self.setWindowTitle('快捷键')
        layout = QGridLayout(self)
        layout.addWidget(QLabel('F、f —— 全屏'), 0, 0)
        layout.addWidget(QLabel('H、h —— 隐藏控制条'), 1, 0)
        layout.addWidget(QLabel('M、m —— 除当前鼠标悬停窗口外全部静音'), 2, 0)


class DumpConfig(QThread):
    def __init__(self, config):
        super(DumpConfig, self).__init__()
        self.config = config

    def run(self):
        configJSONPath = os.path.join(application_path, r'utils/config.json')
        with open(configJSONPath, 'w') as f:
            f.write(json.dumps(self.config, ensure_ascii=False))


class MainWindow(QMainWindow):
    def __init__(self, cacheFolder):
        super(MainWindow, self).__init__()
        self.setWindowTitle('DD监控室')
        self.resize(1600, 900)
        self.maximumToken = True
        self.cacheFolder = cacheFolder
        self.configJSONPath = os.path.join(application_path, r'utils/config.json')
        if os.path.exists(self.configJSONPath):
            self.config = json.loads(open(self.configJSONPath).read())
            while len(self.config['player']) < 9:
                self.config['player'].append(0)
            if type(self.config['roomid']) == list:
                roomIDList = self.config['roomid']
                self.config['roomid'] = {}
                for roomID in roomIDList:
                    self.config['roomid'][roomID] = False
            if 'quality' not in self.config:
                self.config['quality'] = [80] * 9
            if 'audioChannel' not in self.config:
                self.config['audioChannel'] = [0] * 9
            if 'translator' not in self.config:
                self.config['translator'] = [True] * 9
            for index, textSetting in enumerate(self.config['danmu']):
                if type(textSetting) == bool:
                    self.config['danmu'][index] = [textSetting, 20, 2, 6, 0, '【 [ {']
        else:
            self.config = {
                'roomid': {'21396545': False, '21402309': False, '22384516': False, '8792912': False,
                           '21696950': False, '14327465': False, '704808': True, '1321846': False,
                           '56237': False, '8725120': False, '22347054': False, '14052636': False,
                           '21320551': False, '876396': False, '21448649': False, '24393': False,
                           '12845193': False, '41682': False, '21652717': False, '22571958': False,
                           '21919321': True, '21013446': False},  # 置顶显示
                'layout': [(0, 0, 1, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)],
                'player': ['21396545', '21402309', '22384516', '8792912',
                           '21696950', '14327465', '704808', '1321846', '318'],
                'quality': [80] * 9,
                'audioChannel': [0] * 9,
                'muted': [1] * 9,
                'volume': [50] * 9,
                'danmu': [[True, 20, 2, 6, 0, '【 [ {']] * 9,  # 显示弹幕, 透明度, 横向占比, 纵向占比, 显示同传, 同传过滤字符
                'globalVolume': 30,
                'control': True,
            }
        self.dumpConfig = DumpConfig(self.config)
        mainWidget = QWidget()
        self.setCentralWidget(mainWidget)
        self.mainLayout = QGridLayout(mainWidget)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.layoutSettingPanel = LayoutSettingPanel()
        self.layoutSettingPanel.layoutConfig.connect(self.changeLayout)
        self.version = Version()
        self.hotKey = HotKey()

        self.videoWidgetList = []
        self.popVideoWidgetList = []
        for i in range(9):
            volume = self.config['volume'][i]
            self.videoWidgetList.append(VideoWidget(i, volume, cacheFolder, textSetting=self.config['danmu'][i]))
            self.videoWidgetList[i].mutedChanged.connect(self.mutedChanged)
            self.videoWidgetList[i].volumeChanged.connect(self.volumeChanged)
            self.videoWidgetList[i].addMedia.connect(self.addMedia)
            self.videoWidgetList[i].deleteMedia.connect(self.deleteMedia)
            self.videoWidgetList[i].exchangeMedia.connect(self.exchangeMedia)
            self.videoWidgetList[i].setDanmu.connect(self.setDanmu)
            self.videoWidgetList[i].setTranslator.connect(self.setTranslator)
            self.videoWidgetList[i].changeQuality.connect(self.setQuality)
            self.videoWidgetList[i].changeAudioChannel.connect(self.setAudioChannel)
            self.videoWidgetList[i].popWindow.connect(self.popWindow)
            self.videoWidgetList[i].hideBarKey.connect(self.openControlPanel)
            self.videoWidgetList[i].fullScreenKey.connect(self.fullScreen)
            self.videoWidgetList[i].muteExceptKey.connect(self.muteExcept)
            self.videoWidgetList[i].mediaMute(self.config['muted'][i], emit=False)
            self.videoWidgetList[i].slider.setValue(self.config['volume'][i])
            self.videoWidgetList[i].quality = self.config['quality'][i]
            self.videoWidgetList[i].audioChannel = self.config['audioChannel'][i]
            self.popVideoWidgetList.append(VideoWidget(i + 9, volume, cacheFolder, True, '悬浮窗', [1280, 720]))
        self.setPlayer()

        self.controlBar = QToolBar()
        self.addToolBar(self.controlBar)
        self.controlBar.show() if self.config['control'] else self.controlBar.hide()

        self.globalPlayToken = True
        self.play = PushButton(self.style().standardIcon(QStyle.SP_MediaPause))
        self.play.clicked.connect(self.globalMediaPlay)
        self.controlBar.addWidget(self.play)
        self.reload = PushButton(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.reload.clicked.connect(self.globalMediaReload)
        self.controlBar.addWidget(self.reload)
        self.globalMuteToken = False
        self.volumeButton = PushButton(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volumeButton.clicked.connect(self.globalMediaMute)
        self.controlBar.addWidget(self.volumeButton)
        self.slider = Slider()
        self.slider.setValue(self.config['globalVolume'])
        self.slider.value.connect(self.globalSetVolume)
        self.controlBar.addWidget(self.slider)
        self.stop = PushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.stop.clicked.connect(self.globalMediaStop)
        self.controlBar.addWidget(self.stop)

        self.addButton = QPushButton('+')
        self.addButton.setFixedSize(160, 104)
        self.addButton.setStyleSheet('border:3px dotted #EEEEEE')
        self.addButton.setFont(QFont('Arial', 24, QFont.Bold))

        self.controlBar.addWidget(self.addButton)
        self.controlBar.addWidget(QLabel())

        self.scrollArea = ScrollArea()
        self.scrollArea.setStyleSheet('border-width:0px')
        self.scrollArea.setMinimumHeight(111)
        self.controlBar.addWidget(self.scrollArea)
        self.liverPanel = LiverPanel(self.config['roomid'])
        self.liverPanel.addLiverRoomWidget.getHotLiver.start()
        self.liverPanel.addToWindow.connect(self.addCoverToPlayer)
        self.liverPanel.dumpConfig.connect(self.dumpConfig.start)  # 保存config
        self.liverPanel.refreshIDList.connect(self.refreshPlayerStatus)  # 刷新播放器
        self.scrollArea.setWidget(self.liverPanel)
        self.addButton.clicked.connect(self.liverPanel.openLiverRoomPanel)

        self.optionMenu = self.menuBar().addMenu('设置')
        self.controlBarToken = self.config['control']
        layoutConfigAction = QAction('布局方式', self, triggered=self.openLayoutSetting)
        self.optionMenu.addAction(layoutConfigAction)
        globalQualityMenu = self.optionMenu.addMenu('全局画质')
        originQualityAction = QAction('原画', self, triggered=lambda: self.globalQuality(10000))
        globalQualityMenu.addAction(originQualityAction)
        bluerayQualityAction = QAction('蓝光', self, triggered=lambda: self.globalQuality(400))
        globalQualityMenu.addAction(bluerayQualityAction)
        highQualityAction = QAction('超清', self, triggered=lambda: self.globalQuality(250))
        globalQualityMenu.addAction(highQualityAction)
        lowQualityAction = QAction('流畅', self, triggered=lambda: self.globalQuality(80))
        globalQualityMenu.addAction(lowQualityAction)
        globalAudioMenu = self.optionMenu.addMenu('全局音效')
        audioOriginAction = QAction('原始音效', self, triggered=lambda: self.globalAudioChannel(0))
        globalAudioMenu.addAction(audioOriginAction)
        audioDolbysAction = QAction('杜比音效', self, triggered=lambda: self.globalAudioChannel(5))
        globalAudioMenu.addAction(audioDolbysAction)
        controlPanelAction = QAction('显示 / 隐藏控制条(H)', self, triggered=self.openControlPanel)
        self.optionMenu.addAction(controlPanelAction)
        self.fullScreenAction = QAction('全屏(F) / 退出(Esc)', self, triggered=self.fullScreen)
        self.optionMenu.addAction(self.fullScreenAction)

        self.versionMenu = self.menuBar().addMenu('关于DD监控室')
        githubAction = QAction('GitHub', self, triggered=self.openGithub)
        self.versionMenu.addAction(githubAction)
        bilibiliAction = QAction('B站', self, triggered=self.openBilibili)
        self.versionMenu.addAction(bilibiliAction)
        hotKeyAction = QAction('快捷键', self, triggered=self.openHotKey)
        self.versionMenu.addAction(hotKeyAction)
        versionAction = QAction('当前版本', self, triggered=self.openVersion)
        self.versionMenu.addAction(versionAction)

        self.oldMousePos = QPoint(0, 0)  # 初始化鼠标坐标
        self.hideMouseCnt = 90
        self.mouseTrackTimer = QTimer()
        self.mouseTrackTimer.timeout.connect(self.checkMousePos)
        self.mouseTrackTimer.start(500)  # 0.5s检测一次

    def setPlayer(self):
        for index, layoutConfig in enumerate(self.config['layout']):
            roomID = self.config['player'][index]
            videoWidget = self.videoWidgetList[index]
            videoWidget.roomID = str(roomID)  # 转一下防止格式出错
            y, x, h, w = layoutConfig
            self.mainLayout.addWidget(videoWidget, y, x, h, w)
            self.videoWidgetList[index].show()
        self.videoIndex = 0
        self.setMediaTimer = QTimer()
        self.setMediaTimer.timeout.connect(self.setMedia)
        # self.setMediaTimer.start(500)  # QMediaPlayer加载慢一点 否则容易崩
        self.setMediaTimer.start(10)  # vlc

    def setMedia(self):
        if self.videoIndex == 9:
            self.setMediaTimer.stop()
        elif self.videoIndex < len(self.config['layout']):
            # pass
            self.videoWidgetList[self.videoIndex].mediaReload()
        else:
            self.videoWidgetList[self.videoIndex].player.stop()
        self.videoIndex += 1

    def addMedia(self, info):  # 窗口 房号
        id, roomID = info
        self.config['player'][id] = roomID
        self.dumpConfig.start()

    def deleteMedia(self, id):
        self.config['player'][id] = 0
        self.dumpConfig.start()

    def exchangeMedia(self, info):  # 交换播放窗口的函数
        fromID, fromRoomID, toID, toRoomID = info  # 交换数据
        fromVideo, toVideo = self.videoWidgetList[fromID], self.videoWidgetList[toID]  # 待交换的两个控件
        fromVideo.id, toVideo.id = toID, fromID  # 交换id
        fromVideo.topLabel.setText(fromVideo.topLabel.text().replace('窗口%s' % (fromID + 1), '窗口%s' % (toID + 1)))
        toVideo.topLabel.setText(toVideo.topLabel.text().replace('窗口%s' % (toID + 1), '窗口%s' % (fromID + 1)))
        fromMuted, toMuted = self.config['muted'][fromID], self.config['muted'][toID]  # 获取原来的静音设置
        fromVolume, toVolume = self.config['volume'][fromID], self.config['volume'][toID]  # 获取原来的音量
        fromVideo.mediaMute(toMuted)  # 交换静音设置
        fromVideo.setVolume(toVolume)  # 交换音量
        toVideo.mediaMute(fromMuted)
        toVideo.setVolume(fromVolume)
        self.videoWidgetList[fromID], self.videoWidgetList[toID] = toVideo, fromVideo  # 交换控件列表
        self.config['player'][toID] = fromRoomID  # 记录config
        self.config['player'][fromID] = toRoomID
        self.dumpConfig.start()
        self.changeLayout(self.config['layout'])  # 刷新layout

    def setDanmu(self):
        self.dumpConfig.start()

    def setTranslator(self, info):
        id, token = info  # 窗口 同传显示布尔值
        self.config['translator'][id] = token
        self.dumpConfig.start()

    def setQuality(self, info):
        id, quality = info  # 窗口 画质
        self.config['quality'][id] = quality
        self.dumpConfig.start()

    def setAudioChannel(self, info):
        id, audioChannel = info  # 窗口 音效
        self.config['audioChannel'][id] = audioChannel
        self.dumpConfig.start()

    def popWindow(self, info):  # 悬浮窗播放
        id, roomID, quality, showMax = info
        self.popVideoWidgetList[id].roomID = roomID
        self.popVideoWidgetList[id].quality = quality
        self.popVideoWidgetList[id].resize(1280, 720)
        self.popVideoWidgetList[id].show()
        self.popVideoWidgetList[id].textBrowser.show()
        if showMax:
            self.popVideoWidgetList[id].showMaximized()
        self.popVideoWidgetList[id].mediaReload()

    def mutedChanged(self, mutedInfo):
        id, muted = mutedInfo
        token = 2 if muted else 1
        self.config['muted'][id] = token
        self.dumpConfig.start()

    def volumeChanged(self, volumeInfo):
        id, value = volumeInfo
        self.config['volume'][id] = value
        self.dumpConfig.start()

    def globalMediaPlay(self):
        if self.globalPlayToken:
            force = 1
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            force = 2
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.globalPlayToken = not self.globalPlayToken
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaPlay(force)

    def globalMediaReload(self):
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaReload()

    def globalMediaMute(self):
        if self.globalMuteToken:
            force = 1
            self.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        else:
            force = 2
            self.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
        self.globalMuteToken = not self.globalMuteToken
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaMute(force)
        self.config['muted'] = [force] * 9
        self.dumpConfig.start()

    def globalSetVolume(self, value):
        for videoWidget in self.videoWidgetList:
            videoWidget.player.audio_set_volume(value)
            videoWidget.volume = value
            videoWidget.slider.setValue(value)
        self.config['volume'] = [value] * 9
        self.config['globalVolume'] = value
        self.dumpConfig.start()

    def globalMediaStop(self):
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaStop()

    def globalQuality(self, quality):
        for videoWidget in self.videoWidgetList:
            videoWidget.quality = quality
            videoWidget.mediaReload()
        self.config['quality'] = [quality] * 9
        self.dumpConfig.start()

    def globalAudioChannel(self, audioChannel):
        for videoWidget in self.videoWidgetList:
            videoWidget.audioChannel = audioChannel
            videoWidget.player.audio_set_channel(audioChannel)
        self.config['audioChannel'] = [audioChannel] * 9
        self.dumpConfig.start()

    def openControlPanel(self):
        self.controlBar.hide() if self.controlBarToken else self.controlBar.show()
        self.controlBarToken = not self.controlBarToken
        self.config['control'] = self.controlBarToken
        self.dumpConfig.start()

    def openVersion(self):
        self.version.hide()
        self.version.show()

    def openGithub(self):
        QDesktopServices.openUrl(QUrl(r'https://github.com/zhimingshenjun/DD_Monitor'))

    def openBilibili(self):
        QDesktopServices.openUrl(QUrl(r'https://www.bilibili.com/video/BV1yo4y1d7iP'))

    def openHotKey(self):
        self.hotKey.hide()
        self.hotKey.show()

    def checkMousePos(self):
        for videoWidget in self.videoWidgetList:  # vlc的播放会直接音量最大化 实在没地方放了 写在这里实时强制修改它的音量
            videoWidget.player.audio_set_volume(videoWidget.volume)
        newMousePos = QCursor.pos()
        if newMousePos != self.oldMousePos:
            self.setCursor(Qt.ArrowCursor)  # 鼠标动起来就显示
            self.oldMousePos = newMousePos
            self.hideMouseCnt = 6  # 刷新隐藏鼠标的间隔
        if self.hideMouseCnt > 0:
            self.hideMouseCnt -= 1
        else:
            self.setCursor(Qt.BlankCursor)  # 计数归零隐藏鼠标
            for videoWidget in self.videoWidgetList:
                videoWidget.topLabel.hide()  # 隐藏播放窗口的控制条
                videoWidget.frame.hide()
            for videoWidget in self.popVideoWidgetList:
                videoWidget.topLabel.hide()  # 隐藏悬浮窗口的控制条
                videoWidget.frame.hide()

    def moveEvent(self, QMoveEvent):  # 捕获主窗口moveEvent来实时同步弹幕机位置
        for videoWidget in self.videoWidgetList:
            videoWidget.moveTextBrowser()

    def changeEvent(self, QEvent):  # 当用户最小化界面的时候把弹幕机也隐藏了
        try:
            if self.isMinimized():
                for videoWidget in self.videoWidgetList:
                    videoWidget.textBrowser.hide()
            else:
                for index, videoWidget in enumerate(self.videoWidgetList):
                    if self.config['danmu'][index][0] and not videoWidget.isHidden():  # 显示弹幕机
                        videoWidget.textBrowser.show()
        except:
            pass

    def closeEvent(self, QCloseEvent):
        self.hide()
        self.layoutSettingPanel.close()
        self.liverPanel.addLiverRoomWidget.close()
        for videoWidget in self.videoWidgetList:
            videoWidget.player.stop()
            videoWidget.getMediaURL.recordToken = False  # 关闭缓存并清除
            videoWidget.getMediaURL.checkTimer.stop()
            videoWidget.checkPlaying.stop()
        for videoWidget in self.popVideoWidgetList:  # 关闭悬浮窗
            videoWidget.player.stop()
            videoWidget.getMediaURL.recordToken = False
            videoWidget.getMediaURL.checkTimer.stop()
            videoWidget.checkPlaying.stop()
            videoWidget.close()
        self.dumpConfig.start()

    def openLayoutSetting(self):
        self.layoutSettingPanel.hide()
        self.layoutSettingPanel.show()

    def changeLayout(self, layoutConfig):
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaPlay(1)  # 全部暂停
        for index, _ in enumerate(self.config['layout']):
            self.videoWidgetList[index].textBrowser.hide()
            self.mainLayout.itemAt(0).widget().hide()
            self.mainLayout.removeWidget(self.mainLayout.itemAt(0).widget())
        for index, layout in enumerate(layoutConfig):
            y, x, h, w = layout
            self.videoWidgetList[index].show()
            self.videoWidgetList[index].textBrowser.show()
            self.mainLayout.addWidget(self.videoWidgetList[index], y, x, h, w)
            if self.videoWidgetList[index].roomID != '0':
                self.videoWidgetList[index].mediaPlay(2)  # 显示的窗口播放
        self.config['layout'] = layoutConfig
        self.dumpConfig.start()

    def fullScreen(self):
        if self.isFullScreen():  # 退出全屏
            if self.maximumToken:
                self.showMaximized()
            else:
                self.showNormal()
            self.optionMenu.menuAction().setVisible(True)
            self.versionMenu.menuAction().setVisible(True)
            if self.controlBarToken:
                self.controlBar.show()
        else:  # 全屏
            for videoWidget in self.videoWidgetList:
                videoWidget.fullScreen = True
            self.maximumToken = self.isMaximized()
            self.optionMenu.menuAction().setVisible(False)
            self.versionMenu.menuAction().setVisible(False)
            if self.controlBarToken:
                self.controlBar.hide()
            for videoWidget in self.videoWidgetList:
                videoWidget.fullScreen = True
            self.showFullScreen()

    def muteExcept(self):
        for videoWidget in self.videoWidgetList:
            if videoWidget.hoverToken:
                videoWidget.mediaMute(1)  # 取消静音
            else:
                videoWidget.mediaMute(2)  # 静音

    def keyPressEvent(self, QEvent):
        if QEvent.key() == Qt.Key_Escape:
            if self.maximumToken:
                self.showMaximized()
            else:
                self.showNormal()
            self.optionMenu.menuAction().setVisible(True)
            self.versionMenu.menuAction().setVisible(True)
            if self.controlBarToken:
                self.controlBar.show()
        elif QEvent.key() == Qt.Key_F:
            self.fullScreen()
        elif QEvent.key() == Qt.Key_H:
            self.openControlPanel()
        elif QEvent.key() == Qt.Key_M:
            self.muteExcept()

    def addCoverToPlayer(self, info):  # 窗口 房号
        self.addMedia(info)
        self.videoWidgetList[info[0]].roomID = info[1]  # 修改房号
        self.videoWidgetList[info[0]].mediaReload()  # 重载视频

    def refreshPlayerStatus(self, refreshIDList):  # 刷新直播状态发生变化的播放器
        for videoWidget in self.videoWidgetList:
            for roomID in refreshIDList:
                if roomID == videoWidget.roomID:
                    videoWidget.mediaReload()
                    break


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    cachePath = os.path.join(application_path, 'cache')
    if not os.path.exists(cachePath):  # 启动前初始化cache文件夹
        os.mkdir(cachePath)
    try:  # 尝试清除上次缓存 如果失败则跳过
        for cacheFolder in os.listdir(cachePath):
            shutil.rmtree(os.path.join(application_path, 'cache/%s' % cacheFolder))
    except:
        pass
    cacheFolder = os.path.join(application_path, 'cache/%d' % time.time())  # 初始化缓存文件夹
    os.mkdir(cacheFolder)
    app = QApplication(sys.argv)
    with open(os.path.join(application_path, 'utils/qdark.qss'), 'r') as f:
        qss = f.read()
    app.setStyleSheet(qss)
    mainWindow = MainWindow(cacheFolder)
    mainWindow.showMaximized()
    mainWindow.show()
    sys.exit(app.exec_())
