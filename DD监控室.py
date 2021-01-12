import os, sys, json
from PyQt5.Qt import *
from LayoutPanel import LayoutSettingPanel
from VideoWidget import PushButton, Slider, VideoWidget
from LiverSelect import LiverPanel


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
        self.resize(400, 150)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('DD监控室 v0.0.7测试版'), 0, 0)
        layout.addWidget(QLabel('by 神君Channel：https://space.bilibili.com/637783'))


class DumpConfig(QThread):
    def __init__(self, config):
        super(DumpConfig, self).__init__()
        self.config = config

    def run(self):
        # while 0 in self.config['roomid']:
        #     self.config['roomid'].remove(0)
        with open(r'utils/config.json', 'w') as f:
            f.write(json.dumps(self.config, ensure_ascii=False))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('DD监控室')
        self.resize(1600, 900)
        self.maximumToken = True
        if os.path.exists(r'utils/config.json'):
            self.config = json.loads(open(r'utils/config.json').read())
            while len(self.config['player']) < 9:
                self.config['player'].append(0)
            if type(self.config['roomid']) == list:
                roomIDList = self.config['roomid']
                self.config['roomid'] = {}
                for roomID in roomIDList:
                    self.config['roomid'][roomID] = False
            if 'quality' not in self.config:
                self.config['quality'] = [80] * 9
            if 'translator' not in self.config:
                self.config['translator'] = [True] * 9
        else:
            self.config = {
                'roomid': {'21463219': False, '21501730': False, '21096962': False, '21449068': False},  # 置顶显示
                'layout': [(0, 0, 1, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)],
                'player': [21463219, 21501730, 21096962, 21449068, 0, 0, 0, 0, 0],
                'quality': [80] * 9,
                'muted': [1] * 9,
                'volume': [25] * 9,
                'danmu': [True] * 9,
                'translator': [True] * 9,
                'globalVolume': 25,
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

        self.videoWidgetList = []
        for i in range(9):
            self.videoWidgetList.append(VideoWidget(i))
            self.videoWidgetList[i].mutedChanged.connect(self.mutedChanged)
            self.videoWidgetList[i].volumeChanged.connect(self.volumeChanged)
            self.videoWidgetList[i].addMedia.connect(self.addMedia)
            self.videoWidgetList[i].deleteMedia.connect(self.deleteMedia)
            self.videoWidgetList[i].exchangeMedia.connect(self.exchangeMedia)
            self.videoWidgetList[i].setDanmu.connect(self.setDanmu)
            self.videoWidgetList[i].setTranslator.connect(self.setTranslator)
            self.videoWidgetList[i].changeQuality.connect(self.setQuality)
            self.videoWidgetList[i].popWindow.connect(self.popWindow)
            self.videoWidgetList[i].mediaMute(self.config['muted'][i], emit=False)
            self.videoWidgetList[i].player.setVolume(self.config['volume'][i])
            self.videoWidgetList[i].slider.setValue(self.config['volume'][i])
            self.videoWidgetList[i].quality = self.config['quality'][i]
            if self.config['danmu'][i]:
                self.videoWidgetList[i].textBrowser.show()
            else:
                self.videoWidgetList[i].textBrowser.hide()
            if self.config['translator'][i]:
                self.videoWidgetList[i].translator.show()
            else:
                self.videoWidgetList[i].translator.hide()
        # self.popVideoWidgetList = []  # 置顶的悬浮窗
        self.popVideoWidget = VideoWidget(10, True, '悬浮窗', [1280, 720])
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
        self.volume = PushButton(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volume.clicked.connect(self.globalMediaMute)
        self.controlBar.addWidget(self.volume)
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
        controlPanelAction = QAction('显示/隐藏控制条', self, triggered=self.openControlPanel)
        self.optionMenu.addAction(controlPanelAction)
        self.fullScreenAction = QAction('全屏显示 (Esc退出)', self, triggered=self.fullScreen)
        self.optionMenu.addAction(self.fullScreenAction)

        self.versionMenu = self.menuBar().addMenu('版本')
        versionAction = QAction('当前版本', self, triggered=self.openVersion)
        self.versionMenu.addAction(versionAction)

    def setPlayer(self):
        for index, layoutConfig in enumerate(self.config['layout']):
            id = self.config['player'][index]
            self.videoWidgetList[index].roomID = id
            y, x, h, w = layoutConfig
            self.mainLayout.addWidget(self.videoWidgetList[index], y, x, h, w)
        self.videoIndex = 0
        self.setMediaTimer = QTimer()
        self.setMediaTimer.timeout.connect(self.setMedia)
        self.setMediaTimer.start(500)

    def setMedia(self):
        if self.videoIndex == 9:
            self.setMediaTimer.stop()
        elif self.videoIndex < len(self.config['layout']):
            # pass
            self.videoWidgetList[self.videoIndex].mediaReload()
        else:
            self.videoWidgetList[self.videoIndex].player.setMedia(QMediaContent(QUrl('')))
        self.videoIndex += 1

    def addMedia(self, info):  # 窗口 房号
        id, roomID = info
        self.config['player'][id] = roomID
        self.dumpConfig.start()

    def deleteMedia(self, id):
        self.config['player'][id] = 0
        self.dumpConfig.start()

    def exchangeMedia(self, info):  # 窗口 房号
        toID, fromRoomID, fromID, toRoomID = info
        self.config['player'][toID] = fromRoomID
        self.config['player'][fromID] = toRoomID
        self.videoWidgetList[fromID].roomID = toRoomID
        self.videoWidgetList[fromID].textBrowser.textBrowser.clear()
        self.videoWidgetList[fromID].translator.textBrowser.clear()
        self.videoWidgetList[fromID].mediaReload()
        self.dumpConfig.start()

    def setDanmu(self, info):
        id, token = info  # 窗口 弹幕显示布尔值
        self.config['danmu'][id] = token
        self.dumpConfig.start()

    def setTranslator(self, info):
        id, token = info  # 窗口 同传显示布尔值
        self.config['translator'][id] = token
        self.dumpConfig.start()

    def setQuality(self, info):
        id, quality = info  # 窗口 画质
        self.config['quality'][id] = quality
        self.dumpConfig.start()

    def popWindow(self, info):  # 悬浮窗播放
        id, roomID, quality, showMax = info
        self.popVideoWidget.roomID = roomID
        self.popVideoWidget.quality = quality
        if showMax:
            self.popVideoWidget.showMaximized()
        else:
            self.popVideoWidget.show()
        self.popVideoWidget.mediaReload()

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
            self.volume.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        else:
            force = 2
            self.volume.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
        self.globalMuteToken = not self.globalMuteToken
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaMute(force)
        self.config['muted'] = [force] * 9
        self.dumpConfig.start()

    def globalSetVolume(self, value):
        for videoWidget in self.videoWidgetList:
            videoWidget.player.setVolume(value)
            videoWidget.slider.setValue(value)
        self.config['volume'] = [value] * 9
        self.config['globalVolume'] = value
        self.dumpConfig.start()

    def globalMediaStop(self):
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaStop()

    def openControlPanel(self):
        self.controlBar.hide() if self.controlBarToken else self.controlBar.show()
        self.controlBarToken = not self.controlBarToken
        self.config['control'] = self.controlBarToken
        self.dumpConfig.start()

    def openVersion(self):
        self.version.hide()
        self.version.show()

    def closeEvent(self, QCloseEvent):
        self.hide()
        self.layoutSettingPanel.close()
        self.liverPanel.addLiverRoomWidget.close()
        for videoWidget in self.videoWidgetList:
            videoWidget.player.stop()
        for videoWidget in self.videoWidgetList:
            videoWidget.danmu.terminate()
            videoWidget.danmu.quit()
        self.dumpConfig.start()

    def openLayoutSetting(self):
        self.layoutSettingPanel.hide()
        self.layoutSettingPanel.show()

    def changeLayout(self, layoutConfig):
        for videoWidget in self.videoWidgetList:
            videoWidget.mediaPlay(1)  # 全部暂停
        for _ in self.config['layout']:
            self.mainLayout.itemAt(0).widget().hide()
            self.mainLayout.removeWidget(self.mainLayout.itemAt(0).widget())
        for index, layout in enumerate(layoutConfig):
            y, x, h, w = layout
            self.videoWidgetList[index].show()
            self.mainLayout.addWidget(self.videoWidgetList[index], y, x, h, w)
            self.videoWidgetList[index].mediaPlay(2)  # 显示的窗口播放
        self.config['layout'] = layoutConfig
        self.dumpConfig.start()

    def fullScreen(self):
        self.maximumToken = self.isMaximized()
        self.optionMenu.menuAction().setVisible(False)
        self.versionMenu.menuAction().setVisible(False)
        if self.controlBarToken:
            self.controlBar.hide()
        for videoWidget in self.videoWidgetList:
            videoWidget.fullScreen = True
        self.showFullScreen()

    def keyPressEvent(self, QEvent):
        if QEvent.key() == Qt.Key_Escape:
            for videoWidget in self.videoWidgetList:
                videoWidget.fullScreen = False
            if self.maximumToken:
                self.showMaximized()
            else:
                self.showNormal()
            self.optionMenu.menuAction().setVisible(True)
            self.versionMenu.menuAction().setVisible(True)
            if self.controlBarToken:
                self.controlBar.show()

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
    app = QApplication(sys.argv)
    with open('utils/qdark.qss', 'r') as f:
        qss = f.read()
    app.setStyleSheet(qss)
    mainWindow = MainWindow()
    mainWindow.showMaximized()
    mainWindow.show()
    sys.exit(app.exec_())
