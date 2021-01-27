'''
DD监控室主界面进程 包含对所有子页面的初始化、排版管理
同时卡片和播放窗口的交互需要通过主界面线程通信
以及软件启动和退出后的一些操作
新增全局鼠标坐标跟踪 用于刷新鼠标交互效果
'''
import log
# 找不到 dll
# https://stackoverflow.com/questions/54110504/dynlib-dll-was-no-found-when-the-application-was-frozen-when-i-make-a-exe-fil
import ctypes

import os, sys, json, time, shutil, logging,platform, threading
from PyQt5.QtWidgets import * 	# QAction,QFileDialog
from PyQt5.QtGui import *		# QIcon,QPixmap
from PyQt5.QtCore import * 		# QSize
from LayoutPanel import LayoutSettingPanel
# from VideoWidget import PushButton, Slider, VideoWidget  # 已弃用
from VideoWidget_vlc import PushButton, Slider, VideoWidget
from LiverSelect import LiverPanel
from pay import pay
import codecs
import dns.resolver
from ReportException import thraedingExceptionHandler, uncaughtExceptionHandler,\
    unraisableExceptionHandler, getSystemInfo


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
        layout.addWidget(QLabel('DD监控室 v1.1'), 0, 0, 1, 2)
        layout.addWidget(QLabel('by 神君Channel'), 1, 0, 1, 2)
        layout.addWidget(QLabel('特别鸣谢：大锅饭 美东矿业'), 2, 0, 1, 2)
        releases_url = QLabel('')
        releases_url.setOpenExternalLinks(True)
        releases_url.setText(_translate("MainWindow", "<html><head/><body><p><a href=\"https://space.bilibili.com/637783\">\
<span style=\" text-decoration: underline; color:#cccccc;\">https://space.bilibili.com/637783</span></a></p></body></html>", None))
        layout.addWidget(releases_url, 1, 1, 1, 2, Qt.AlignRight)

        checkButton = QPushButton('检查更新')
        checkButton.setFixedHeight(40)
        checkButton.clicked.connect(self.checkUpdate)
        layout.addWidget(checkButton, 0, 2, 1, 1)

    def checkUpdate(self):
        QDesktopServices.openUrl(QUrl(r'https://github.com/zhimingshenjun/DD_Monitor/releases/tag/DD_Monitor'))


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
        self.backupNumber = 1

    def run(self):
        try:
            configJSONPath = os.path.join(application_path, r'utils/config.json')
            with codecs.open(configJSONPath, 'w', 'utf8') as f:
                f.write(json.dumps(self.config, ensure_ascii=False))
        except Exception as e:
            logging.error(str(e))
        try:  # 备份 防止存储config时崩溃
            configJSONPath = os.path.join(application_path, r'utils/config_备份%d.json' % self.backupNumber)
            self.backupNumber += 1
            if self.backupNumber == 4:
                self.backupNumber = 1
            # with open(configJSONPath, 'w') as f:
            #     f.write(json.dumps(self.config, ensure_ascii=False))
            with codecs.open(configJSONPath, 'w', 'utf8') as f:
                f.write(json.dumps(self.config, ensure_ascii=False))
        except Exception as e:
            logging.error(str(e))

class CheckDanmmuProvider(QThread):
    def __init__(self):
        super(CheckDanmmuProvider,self).__init__()
    
    def run(self):
        anwsers = dns.resolver.resolve('broadcastlv.chat.bilibili.com', 'A')
        danmu_ip = anwsers[0].to_text()
        logging.info("弹幕IP: %s" % danmu_ip)


class MainWindow(QMainWindow):
    def __init__(self, cacheFolder, progressBar, progressText):
        super(MainWindow, self).__init__()
        self.setWindowTitle('DD监控室')
        self.resize(1600, 900)
        self.maximumToken = True
        self.cacheFolder = cacheFolder
        self.configJSONPath = os.path.join(application_path, r'utils/config.json')
        self.config = {}
        if os.path.exists(self.configJSONPath):  # 读取config
            if os.path.getsize(self.configJSONPath):
                try:
                    with codecs.open(self.configJSONPath, 'r', 'utf8') as f:
                        self.config = json.loads(f.read())
                    # self.config = json.loads(open(self.configJSONPath).read())
                except Exception as e:
                    print(str(e))
                    self.config = {}
        if not self.config:  # 读取config失败 尝试读取备份
            for backupNumber in [1, 2, 3]:  # 备份预设123
                self.configJSONPath = os.path.join(application_path, r'utils/config_备份%d.json' % backupNumber)
                if os.path.exists(self.configJSONPath):  # 如果备份文件存在
                    if os.path.getsize(self.configJSONPath):  # 如过备份文件有效
                        try:
                            self.config = json.loads(open(self.configJSONPath).read())
                            break
                        except:
                            self.config = {}
        if self.config:  # 如果能成功读取到config文件
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
                    self.config['danmu'][index] = [textSetting, 20, 1, 7, 0, '【 [ {']
            if 'hardwareDecode' not in self.config:
                self.config['hardwareDecode'] = True
            if 'maxCacheSize' not in self.config:
                self.config['maxCacheSize'] = 2048000
                logging.warn('最大缓存没有被设置，使用默认1G')
            if 'startWithDanmu' not in self.config:
                self.config['startWithDanmu'] = True
                logging.warn('启动时加载弹幕没有被设置，默认加载')
            for danmuConfig in self.config['danmu']:
                if len(danmuConfig) == 6:
                    danmuConfig.append(10)
        else:
            self.config = {
                'roomid': {'21396545': False, '21402309': False, '22384516': False, '8792912': False,
                           '21696950': False, '14327465': False, '704808': True, '1321846': False,
                           '56237': False, '8725120': False, '22347054': False, '14052636': False,
                           '21320551': False, '876396': False, '21448649': False, '24393': False,
                           '12845193': False, '41682': False, '21652717': False, '22571958': False,
                           '21919321': True, '21013446': False},  # 置顶显示
                'layout': [(0, 0, 1, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)],
                # 'player': ['21396545', '21402309', '22384516', '8792912',
                #            '21696950', '14327465', '704808', '1321846', '318'],
                'player': ['0'] * 9,
                'quality': [80] * 9,
                'audioChannel': [0] * 9,
                'muted': [1] * 9,
                'volume': [50] * 9,
                'danmu': [[True, 50, 1, 7, 0, '【 [ {', 10]] * 9,  # 显示,透明,横向,纵向,类型,同传字符,字体大小
                'globalVolume': 30,
                'control': True,
                'hardwareDecode': True,
                'maxCacheSize': 2048000,
                'startWithDanmu': True
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
        self.pay = pay()

        self.videoWidgetList = []
        self.popVideoWidgetList = []
        vlcProgressCounter = 1
        for i in range(9):
            volume = self.config['volume'][i]
            progressText.setText('设置第%s个主层播放器...' % str(i + 1))
            self.videoWidgetList.append(VideoWidget(i, volume, cacheFolder, textSetting=self.config['danmu'][i],
                                                    maxCacheSize = self.config['maxCacheSize'],
                                                    startWithDanmu=self.config['startWithDanmu']))
            vlcProgressCounter += 1
            progressBar.setValue(vlcProgressCounter)
            # self.videoWidgetList[i].mutedChanged.connect(self.mutedChanged)  # 硬盘io过高 屏蔽掉 退出的时候统一保存
            # self.videoWidgetList[i].volumeChanged.connect(self.volumeChanged)  # 硬盘io过高 屏蔽掉 退出的时候统一保存
            self.videoWidgetList[i].addMedia.connect(self.addMedia)
            self.videoWidgetList[i].deleteMedia.connect(self.deleteMedia)
            self.videoWidgetList[i].exchangeMedia.connect(self.exchangeMedia)
            # self.videoWidgetList[i].setDanmu.connect(self.setDanmu)  # 硬盘io过高 屏蔽掉 退出的时候统一保存
            # self.videoWidgetList[i].setTranslator.connect(self.setTranslator)  # 已废弃
            self.videoWidgetList[i].changeQuality.connect(self.setQuality)
            # self.videoWidgetList[i].changeAudioChannel.connect(self.setAudioChannel)  # 硬盘io过高 屏蔽掉 退出的时候统一保存
            self.videoWidgetList[i].popWindow.connect(self.popWindow)
            self.videoWidgetList[i].hideBarKey.connect(self.openControlPanel)
            self.videoWidgetList[i].fullScreenKey.connect(self.fullScreen)
            self.videoWidgetList[i].muteExceptKey.connect(self.muteExcept)
            self.videoWidgetList[i].mediaMute(self.config['muted'][i], emit=False)
            self.videoWidgetList[i].slider.setValue(self.config['volume'][i])
            self.videoWidgetList[i].quality = self.config['quality'][i]
            self.videoWidgetList[i].audioChannel = self.config['audioChannel'][i]
            self.popVideoWidgetList.append(VideoWidget(i + 9, volume, cacheFolder, True, '悬浮窗', [1280, 720],
                                                       maxCacheSize=self.config['maxCacheSize'],
                                                       startWithDanmu=self.config['startWithDanmu']))
            vlcProgressCounter += 1
            progressBar.setValue(vlcProgressCounter)
            progressText.setText('设置第%s个悬浮窗播放器...' % str(i + 1))
            app.processEvents()
            logging.info("VLC设置完毕 %s / 9" % str(i + 1))
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
        progressText.setText('设置播放器控制...')

        self.addButton = QPushButton('+')
        self.addButton.setFixedSize(160, 104)
        self.addButton.setStyleSheet('border:3px dotted #EEEEEE')
        self.addButton.setFont(QFont('Arial', 24, QFont.Bold))
        progressText.setText('设置添加控制...')

        self.controlBar.addWidget(self.addButton)
        self.controlBar.addWidget(QLabel())
        progressText.setText('设置全局控制...')

        self.scrollArea = ScrollArea()
        self.scrollArea.setStyleSheet('border-width:0px')
        self.scrollArea.setMinimumHeight(111)
        self.controlBar.addWidget(self.scrollArea)
        self.liverPanel = LiverPanel(self.config['roomid'], application_path)
        self.liverPanel.addLiverRoomWidget.getHotLiver.start()
        self.liverPanel.addToWindow.connect(self.addCoverToPlayer)
        self.liverPanel.dumpConfig.connect(self.dumpConfig.start)  # 保存config
        self.liverPanel.refreshIDList.connect(self.refreshPlayerStatus)  # 刷新播放器
        self.scrollArea.setWidget(self.liverPanel)
        self.addButton.clicked.connect(self.liverPanel.openLiverRoomPanel)
        progressText.setText('设置主播选择控制...')

        self.optionMenu = self.menuBar().addMenu('设置')
        self.controlBarToken = self.config['control']
        layoutConfigAction = QAction('布局方式', self, triggered=self.openLayoutSetting)
        self.optionMenu.addAction(layoutConfigAction)
        globalQualityMenu = self.optionMenu.addMenu('全局画质 ►')
        originQualityAction = QAction('原画', self, triggered=lambda: self.globalQuality(10000))
        globalQualityMenu.addAction(originQualityAction)
        bluerayQualityAction = QAction('蓝光', self, triggered=lambda: self.globalQuality(400))
        globalQualityMenu.addAction(bluerayQualityAction)
        highQualityAction = QAction('超清', self, triggered=lambda: self.globalQuality(250))
        globalQualityMenu.addAction(highQualityAction)
        lowQualityAction = QAction('流畅', self, triggered=lambda: self.globalQuality(80))
        globalQualityMenu.addAction(lowQualityAction)
        globalAudioMenu = self.optionMenu.addMenu('全局音效 ►')
        audioOriginAction = QAction('原始音效', self, triggered=lambda: self.globalAudioChannel(0))
        globalAudioMenu.addAction(audioOriginAction)
        audioDolbysAction = QAction('杜比音效', self, triggered=lambda: self.globalAudioChannel(5))
        globalAudioMenu.addAction(audioDolbysAction)
        hardDecodeMenu = self.optionMenu.addMenu('解码方案 ►')
        hardDecodeAction = QAction('硬解', self, triggered=lambda: self.setDecode(True))
        hardDecodeMenu.addAction(hardDecodeAction)
        softDecodeAction = QAction('软解', self, triggered=lambda: self.setDecode(False))
        hardDecodeMenu.addAction(softDecodeAction)
        cacheSizeSetting = QAction('最大缓存设置', self, triggered=self.openCacheSizeSetting)
        self.optionMenu.addAction(cacheSizeSetting)
        startWithDanmuSetting = QAction('自动加载弹幕设置', self, triggered=self.openStartWithDanmuSetting)
        self.optionMenu.addAction(startWithDanmuSetting)
        controlPanelAction = QAction('显示 / 隐藏控制条(H)', self, triggered=self.openControlPanel)
        self.optionMenu.addAction(controlPanelAction)
        self.fullScreenAction = QAction('全屏(F) / 退出(Esc)', self, triggered=self.fullScreen)
        self.optionMenu.addAction(self.fullScreenAction)
        exportConfig = QAction('导出预设', self, triggered=self.exportConfig)
        self.optionMenu.addAction(exportConfig)
        importConfig = QAction('导入预设', self, triggered=self.importConfig)
        self.optionMenu.addAction(importConfig)
        progressText.setText('设置选项菜单...')

        self.versionMenu = self.menuBar().addMenu('帮助')
        bilibiliAction = QAction('B站视频', self, triggered=self.openBilibili)
        self.versionMenu.addAction(bilibiliAction)
        hotKeyAction = QAction('快捷键', self, triggered=self.openHotKey)
        self.versionMenu.addAction(hotKeyAction)
        versionAction = QAction('检查版本', self, triggered=self.openVersion)
        self.versionMenu.addAction(versionAction)
        otherDDMenu = self.versionMenu.addMenu('其他DD系列工具 ►')
        DDSubtitleAction = QAction('DD烤肉机', self, triggered=self.openDDSubtitle)
        otherDDMenu.addAction(DDSubtitleAction)
        DDThanksAction = QAction('DD答谢机', self, triggered=self.openDDThanks)
        otherDDMenu.addAction(DDThanksAction)
        progressText.setText('设置帮助菜单...')

        self.payMenu = self.menuBar().addMenu('开源和投喂')
        githubAction = QAction('GitHub', self, triggered=self.openGithub)
        self.payMenu.addAction(githubAction)
        feedAction = QAction('投喂作者', self, triggered=self.openFeed)
        self.payMenu.addAction(feedAction)
        # killAction = QAction('自尽(测试)', self, triggered=lambda a: 0 / 0)
        # self.payMenu.addAction(killAction)
        progressText.setText('设置关于菜单...')

        self.oldMousePos = QPoint(0, 0)  # 初始化鼠标坐标
        self.hideMouseCnt = 90
        self.mouseTrackTimer = QTimer()
        self.mouseTrackTimer.timeout.connect(self.checkMousePos)
        self.mouseTrackTimer.start(100)  # 0.1s检测一次
        progressText.setText('设置UI...')
        self.checkDanmmuProvider = CheckDanmmuProvider()
        self.checkDanmmuProvider.start()
        logging.info('UI构造完毕')

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
        # fromMuted, toMuted = self.config['muted'][fromID], self.config['muted'][toID]  # 获取原来的静音设置
        # fromVolume, toVolume = self.config['volume'][fromID], self.config['volume'][toID]  # 获取原来的音量
        fromVideoPos = fromVideo.mapToGlobal(fromVideo.videoFrame.pos())  # 保持弹幕框相对位置
        toVideoPos = toVideo.mapToGlobal(toVideo.videoFrame.pos())
        fromTextDelta, toTextDelta = fromVideo.textPosDelta, toVideo.textPosDelta
        fromVideo.textBrowser.move(toVideoPos + fromTextDelta)
        toVideo.textBrowser.move(fromVideoPos + toTextDelta)
        # fromVideo.mediaMute(toMuted)  # 交换静音设置
        # fromVideo.setVolume(toVolume)  # 交换音量
        # toVideo.mediaMute(fromMuted)
        # toVideo.setVolume(fromVolume)
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
        id, roomID, quality, showMax, startWithDanmu = info
        logging.info("%s 进入悬浮窗模式, 弹幕?: %s"  % (roomID, startWithDanmu))
        self.popVideoWidgetList[id].roomID = roomID
        self.popVideoWidgetList[id].quality = quality
        self.popVideoWidgetList[id].resize(1280, 720)
        self.popVideoWidgetList[id].show()
        if startWithDanmu:
            self.popVideoWidgetList[id].showDanmu()
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
            if not videoWidget.isHidden():
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
        # self.dumpConfig.start()

    def globalSetVolume(self, value):
        for videoWidget in self.videoWidgetList:
            videoWidget.player.audio_set_volume(int(value * videoWidget.volumeAmplify))
            videoWidget.volume = value
            videoWidget.slider.setValue(value)
        self.config['volume'] = [value] * 9
        self.config['globalVolume'] = value
        # self.dumpConfig.start()

    def globalMediaStop(self):
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaStop()

    def globalQuality(self, quality):
        for videoWidget in self.videoWidgetList:
            if not videoWidget.isHidden():  # 窗口没有被隐藏
                videoWidget.quality = quality
                videoWidget.mediaReload()
        self.config['quality'] = [quality] * 9
        self.dumpConfig.start()

    def globalAudioChannel(self, audioChannel):
        for videoWidget in self.videoWidgetList:
            videoWidget.audioChannel = audioChannel
            videoWidget.player.audio_set_channel(audioChannel)
        self.config['audioChannel'] = [audioChannel] * 9
        # self.dumpConfig.start()

    def setDecode(self, hardwareDecodeToken):
        for videoWidget in self.videoWidgetList:
            videoWidget.hardwareDecode = hardwareDecodeToken
        self.globalMediaReload()
        self.config['hardwareDecode'] = hardwareDecodeToken

    def openControlPanel(self):
        self.controlBar.hide() if self.controlBarToken else self.controlBar.show()
        self.controlBarToken = not self.controlBarToken
        self.config['control'] = self.controlBarToken
        # self.dumpConfig.start()

    def openVersion(self):
        self.version.hide()
        self.version.show()

    def openGithub(self):
        QDesktopServices.openUrl(QUrl(r'https://github.com/zhimingshenjun/DD_Monitor'))

    def openBilibili(self):
        QDesktopServices.openUrl(QUrl(r'https://www.bilibili.com/video/BV1yo4y1d7iP'))

    def openDDSubtitle(self):
        QDesktopServices.openUrl(QUrl(r'https://www.bilibili.com/video/BV1p5411b7o7'))

    def openDDThanks(self):
        QDesktopServices.openUrl(QUrl(r'https://www.bilibili.com/video/BV1Di4y1L7T2'))

    def openCacheSizeSetting(self):
        userInputCache, okPressed = QInputDialog.getInt(self,"设置最大缓存大小","最大缓存(GB)",
            int(float(self.config['maxCacheSize']) / (10 ** 6)), 1, 4, 1)
        if okPressed:
            self.config['maxCacheSize'] = int(userInputCache * 10 ** 6)
            self.dumpConfig.start()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("缓存大小设置成功，重启监控室后生效。")
            msg.exec()

    def openStartWithDanmuSetting(self):
        items = ('加载(推荐，默认。但可能增加网络压力，可能会被限流。)', '不加载')
        defulatSelection = 0
        if not self.config['startWithDanmu']:
            defulatSelection = 1
        selection, okPressed = QInputDialog.getItem(self,"设置启动时是否加载弹幕", "加载选项", items, defulatSelection, False)
        if okPressed:
            trueDanmu = (selection == items[0])
            self.config['startWithDanmu'] = trueDanmu
            self.dumpConfig.start()

    def openHotKey(self):
        self.hotKey.hide()
        self.hotKey.show()

    def openFeed(self):
        self.pay.hide()
        self.pay.show()
        self.pay.thankToBoss.start()

    def checkMousePos(self):
        for videoWidget in self.videoWidgetList:  # vlc的播放会直接音量最大化 实在没地方放了 写在这里实时强制修改它的音量
            videoWidget.player.audio_set_volume(int(videoWidget.volume * videoWidget.volumeAmplify))
        newMousePos = QCursor.pos()
        if newMousePos != self.oldMousePos:
            self.setCursor(Qt.ArrowCursor)  # 鼠标动起来就显示
            self.oldMousePos = newMousePos
            self.hideMouseCnt = 20  # 刷新隐藏鼠标的间隔
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
            videoPos = videoWidget.mapToGlobal(videoWidget.videoFrame.pos())  # videoFrame的坐标要转成globalPos
            videoWidget.textBrowser.move(videoPos + videoWidget.textPosDelta)
            videoWidget.textPosDelta = videoWidget.textBrowser.pos() - videoPos

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
            videoWidget = self.videoWidgetList[index]
            videoWidget.show()
            if videoWidget.textSetting[0]:  # 显示弹幕
                videoWidget.textBrowser.show()
            self.mainLayout.addWidget(videoWidget, y, x, h, w)
            if videoWidget.roomID != '0':
                videoWidget.mediaPlay(2)  # 显示的窗口播放
        for videoWidget in self.videoWidgetList[index + 1:]:  # 被隐藏起来的窗口
            videoWidget.getMediaURL.recordToken = False  # 关闭缓存并清除
            videoWidget.getMediaURL.checkTimer.stop()
            videoWidget.checkPlaying.stop()
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
            self.payMenu.menuAction().setVisible(True)
            if self.controlBarToken:
                self.controlBar.show()
        else:  # 全屏
            for videoWidget in self.videoWidgetList:
                videoWidget.fullScreen = True
            self.maximumToken = self.isMaximized()
            self.optionMenu.menuAction().setVisible(False)
            self.versionMenu.menuAction().setVisible(False)
            self.payMenu.menuAction().setVisible(False)
            if self.controlBarToken:
                self.controlBar.hide()
            for videoWidget in self.videoWidgetList:
                videoWidget.fullScreen = True
            self.showFullScreen()

    def exportConfig(self):
        self.savePath = QFileDialog.getSaveFileName(self, "选择保存路径", 'DD监控室预设', "*.json")[0]
        if self.savePath:  # 保存路径有效
            try:
                with open(self.savePath, 'w') as f:
                    f.write(json.dumps(self.config, ensure_ascii=False))
                QMessageBox.information(self, '导出预设', '导出完成', QMessageBox.Ok)
            except Exception as e:
                logging.error(str(e))

    def importConfig(self):
        jsonPath = QFileDialog.getOpenFileName(self, "选择预设", None, "*.json")[0]
        if jsonPath:
            if os.path.getsize(jsonPath):
                config = {}
                try:
                    config = json.loads(open(jsonPath).read())
                except:
                    config = {}
                if config:  # 如果能成功读取到config文件
                    self.config = config
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
                            self.config['danmu'][index] = [textSetting, 20, 1, 7, 0, '【 [ {']
                    if 'hardwareDecode' not in self.config:
                        self.config['hardwareDecode'] = True
                    self.liverPanel.addLiverRoomList(self.config['roomid'].keys())
                    QMessageBox.information(self, '导入预设', '导入完成', QMessageBox.Ok)

    def muteExcept(self):
        for videoWidget in self.videoWidgetList:
            if videoWidget.hoverToken:
                videoWidget.mediaMute(1)  # 取消静音
            else:
                videoWidget.mediaMute(2)  # 静音

    def keyPressEvent(self, QEvent):
        if QEvent.key() == Qt.Key_Escape:
            self.fullScreen()  # 自动判断全屏状态并退出
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
    if platform.system() == 'Windows':
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    cachePath = os.path.join(application_path, 'cache')
    logsPath = os.path.join(application_path, 'logs')
    if not os.path.exists(cachePath):  # 启动前初始化cache文件夹
        os.mkdir(cachePath)
    if not os.path.exists(logsPath):  # 启动前初始化logs文件夹
        os.mkdir(logsPath)
    try:  # 尝试清除上次缓存 如果失败则跳过
        for cacheFolder in os.listdir(cachePath):
            shutil.rmtree(os.path.join(application_path, 'cache/%s' % cacheFolder))
    except:
        pass
    cacheFolder = os.path.join(application_path, 'cache/%d' % time.time())  # 初始化缓存文件夹
    os.mkdir(cacheFolder)
    # 主程序注释 + 应用qss
    app = QApplication(sys.argv)
    with open(os.path.join(application_path, 'utils/qdark.qss'), 'r') as f:
        qss = f.read()
    app.setStyleSheet(qss)
    app.setFont(QFont('微软雅黑', 9))
    # 日志采集
    log.init_log(application_path)
    sys.excepthook = uncaughtExceptionHandler
    sys.unraisablehook = unraisableExceptionHandler
    threading.excepthook = thraedingExceptionHandler
    sysInfo, gpuInfo = getSystemInfo()
    logging.info("系统信息: %s" % str(sysInfo))
    logging.info("GPU信息: %s" % str(gpuInfo))
    # 欢迎页面
    splash = QSplashScreen(QPixmap(os.path.join(application_path, 'utils/splash.jpg')), Qt.WindowStaysOnTopHint)
    progressBar = QProgressBar(splash)
    progressBar.setMaximum(18) # 9 * 2个播放器, 0 - 17 index
    progressBar.setGeometry(0, splash.height() - 20, splash.width(), 20)
    progressText = QLabel(splash)
    progressText.setText("加载中...")
    progressText.setGeometry(0, 0, 170, 20)
    splash.show()
    # 主页面入口
    mainWindow = MainWindow(cacheFolder, progressBar, progressText)
    mainWindow.showMaximized()
    mainWindow.show()
    splash.hide()
    sys.exit(app.exec_())
