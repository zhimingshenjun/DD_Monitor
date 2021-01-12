import requests, json
from PyQt5.Qt import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from remote import remoteThread


class Bar(QLabel):
    moveSignal = pyqtSignal(QPoint)

    def __init__(self, text):
        super(Bar, self).__init__()
        self.setText(text)
        self.setFixedHeight(25)

    def mousePressEvent(self, event):
        self.startPos = event.pos()

    def mouseMoveEvent(self, event):
        self.moveSignal.emit(event.pos() - self.startPos)


class TextBrowser(QWidget):
    closeSignal = pyqtSignal()

    def __init__(self, parent, id, title='弹幕'):
        super(TextBrowser, self).__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.bar = Bar(' 窗口%s %s' % (id + 1, title))
        self.bar.setStyleSheet('background:#AAAAAAAA')
        self.bar.moveSignal.connect(self.moveWindow)
        layout.addWidget(self.bar, 0, 0, 1, 10)

        self.closeButton = QToolButton()
        self.closeButton.setStyleSheet('border-color:#CCCCCC')
        self.closeButton.setFixedSize(25, 25)
        self.closeButton.setIcon(self.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
        self.closeButton.clicked.connect(self.userClose)
        layout.addWidget(self.closeButton, 0, 9, 1, 1)

        self.textBrowser = QTextBrowser()
        self.textBrowser.setFont(QFont('Microsoft JhengHei', 16, QFont.Bold))
        self.textBrowser.setStyleSheet('background:#66000000;border-width:1')
        layout.addWidget(self.textBrowser, 1, 0, 1, 10)

    def userClose(self):
        self.hide()
        self.closeSignal.emit()

    def moveWindow(self, moveDelta):
        newPos = self.pos() + moveDelta
        x, y = newPos.x(), newPos.y()
        rightBorder = self.parent().width() - self.width()
        bottomBoder = self.parent().height() - self.height()
        if x < 0:
            x = 0
        elif x > rightBorder:
            x = rightBorder
        if y < 0:
            y = 0
        elif y > bottomBoder:
            y = bottomBoder
        self.move(x, y)


class PushButton(QPushButton):
    def __init__(self, icon='', text=''):
        super(PushButton, self).__init__()
        self.setFixedSize(30, 30)
        self.setStyleSheet('background-color:#00000000')
        if icon:
            self.setIcon(icon)
        elif text:
            self.setText(text)


class Slider(QSlider):
    value = pyqtSignal(int)

    def __init__(self, value=100):
        super(Slider, self).__init__()
        self.setOrientation(Qt.Horizontal)
        self.setFixedWidth(100)
        self.setValue(value)

    def mousePressEvent(self, event):
        self.updateValue(event.pos())

    def mouseMoveEvent(self, event):
        self.updateValue(event.pos())

    def wheelEvent(self, event):  # 把进度条的滚轮事件去了 用啥子滚轮
        pass

    def updateValue(self, QPoint):
        value = QPoint.x()
        if value > 100: value = 100
        elif value < 0: value = 0
        self.setValue(value)
        self.value.emit(value)


class GraphicsView(QGraphicsView):
    rightClicked = pyqtSignal(QEvent)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rightClicked.emit(event)


class GraphicsVideoItem(QGraphicsVideoItem):
    dropFile = pyqtSignal(str)  # 重写接收drop信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dropEvent(self, QEvent):
        if QEvent.mimeData().hasText:
            self.dropFile.emit(QEvent.mimeData().text())


class GetMediaURL(QThread):
    url = pyqtSignal(QMediaContent)

    def __init__(self):
        super(GetMediaURL, self).__init__()
        self.roomID = 0
        self.quality = 250

    def setConfig(self, roomID, quality):
        self.roomID = roomID
        self.quality = quality

    def run(self):
        api = r'https://api.live.bilibili.com/room/v1/Room/playUrl?cid=%s&platform=web&qn=%s' % (self.roomID, self.quality)
        r = requests.get(api)
        try:
            self.url.emit(QMediaContent(QUrl(json.loads(r.text)['data']['durl'][0]['url'])))
        except Exception as e:
            print(str(e))


class VideoWidget(QWidget):
    mutedChanged = pyqtSignal(list)
    volumeChanged = pyqtSignal(list)
    addMedia = pyqtSignal(list)  # 发送新增的直播
    deleteMedia = pyqtSignal(int)  # 删除选中的直播
    exchangeMedia = pyqtSignal(list)  # 交换播放窗口
    setDanmu = pyqtSignal(list)  # 发射弹幕关闭信号
    setTranslator = pyqtSignal(list)  # 发送同传关闭信号
    changeQuality = pyqtSignal(list)  # 修改画质
    popWindow = pyqtSignal(list)  # 弹出悬浮窗

    def __init__(self, id, top=False, title='', resize=[]):
        super(VideoWidget, self).__init__()
        self.id = id
        self.roomID = 0
        self.pauseToken = False
        self.quality = 250
        self.leftButtonPress = False
        self.rightButtonPress = False
        self.fullScreen = False
        self.top = top
        self.opacity = 100
        if top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint)
        if title:
            self.setWindowTitle('%s %s' % (title, id + 1))
        if resize:
            self.resize(resize[0], resize[1])
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.view = GraphicsView()
        self.view.rightClicked.connect(self.rightMouseClicked)
        self.view.setScene(self.scene)
        self.view.resize(1280, 720)
        self.videoItem = GraphicsVideoItem()
        self.videoItem.dropFile.connect(self.dropFile)
        # self.videoItem.setSize(QSizeF(self.width(), self.height()))
        self.scene.addItem(self.videoItem)
        layout.addWidget(self.view, 0, 0, 12, 12)
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.videoItem)

        # self.videoWidget = QVideoWidget()
        # self.videoWidget.setStyleSheet('background-color:black')
        # self.player = QMediaPlayer()
        # self.player.setVideoOutput(self.videoWidget)
        # layout.addWidget(self.videoWidget, 0, 0, 12, 12)
        self.topLabel = QLabel()
        # self.topLabel.setAlignment(Qt.AlignCenter)
        self.topLabel.setObjectName('frame')
        self.topLabel.setStyleSheet("background-color:#BB708090")
        # self.topLabel.setFixedHeight(32)
        self.topLabel.setFont(QFont('微软雅黑', 15, QFont.Bold))
        layout.addWidget(self.topLabel, 0, 0, 1, 12)
        self.topLabel.hide()

        self.frame = QWidget()
        self.frame.setObjectName('frame')
        self.frame.setStyleSheet("background-color:#BB708090")
        self.frame.setFixedHeight(32)
        frameLayout = QHBoxLayout(self.frame)
        frameLayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame, 11, 0, 1, 12)
        self.frame.hide()

        self.titleLabel = QLabel()
        self.titleLabel.setMaximumWidth(150)
        self.titleLabel.setStyleSheet('background-color:#00000000')
        self.setTitle()
        frameLayout.addWidget(self.titleLabel)
        self.play = PushButton(self.style().standardIcon(QStyle.SP_MediaPause))
        self.play.clicked.connect(self.mediaPlay)
        frameLayout.addWidget(self.play)
        self.reload = PushButton(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.reload.clicked.connect(self.mediaReload)
        frameLayout.addWidget(self.reload)
        self.volume = PushButton(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volume.clicked.connect(self.mediaMute)
        frameLayout.addWidget(self.volume)
        self.slider = Slider()
        self.slider.setStyleSheet('background-color:#00000000')
        self.slider.value.connect(self.setVolume)
        frameLayout.addWidget(self.slider)
        self.danmuButton = PushButton(text='弹')
        self.danmuButton.clicked.connect(self.showDanmu)
        frameLayout.addWidget(self.danmuButton)
        self.stop = PushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.stop.clicked.connect(self.mediaStop)
        frameLayout.addWidget(self.stop)

        self.getMediaURL = GetMediaURL()
        self.getMediaURL.url.connect(self.setMedia)

        self.textBrowser = TextBrowser(self, self.id, '弹幕')
        self.textBrowser.closeSignal.connect(self.closeDanmu)

        self.translator = TextBrowser(self, self.id, '同传')
        self.translator.closeSignal.connect(self.closeTranslator)

        self.danmu = remoteThread(self.roomID)

        self.resizeTimer = QTimer()
        self.resizeTimer.timeout.connect(self.resizeVideoItem)

        self.fullScreenTimer = QTimer()
        self.fullScreenTimer.timeout.connect(self.hideFrame)

    def enterEvent(self, QEvent):
        self.topLabel.show()
        self.frame.show()
        if self.fullScreen:  # 如果全屏模式 等待一段时间后隐藏控制条
            self.fullScreenTimer.start(3000)

    def leaveEvent(self, QEvent):
        self.topLabel.hide()
        self.frame.hide()

    def mouseDoubleClickEvent(self, QMouseEvent):
        if not self.top:  # 非弹出类悬浮窗
            self.popWindow.emit([self.id, self.roomID, self.quality, True])
            self.mediaPlay(1)  # 暂停播放

    def closeEvent(self, QCloseEvent):  # 这个closeEvent只是给悬浮窗用的
        self.player.setMedia(QMediaContent(QUrl('')))
        self.danmu.terminate()
        self.danmu.quit()

    def hideFrame(self):
        self.fullScreenTimer.stop()
        self.topLabel.hide()
        self.frame.hide()

    def mousePressEvent(self, QMouseEvent):  # 设置drag事件 发送拖动封面的房间号
        if QMouseEvent.button() == Qt.LeftButton:
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText('exchange:%s:%s' % (self.id, self.roomID))
            drag.setMimeData(mimeData)
            drag.exec_()

    def dropFile(self, text):
        if 'roomID' in text:  # 从cover拖拽新直播间
            self.roomID = int(text.split(':')[1])
            self.addMedia.emit([self.id, self.roomID])
            self.mediaReload()
            self.textBrowser.textBrowser.clear()
            self.translator.textBrowser.clear()
        elif 'exchange' in text: # 交换窗口
            fromID, fromRoomID = map(int, text.split(':')[1:])
            if fromID != self.id:
                self.exchangeMedia.emit([self.id, fromRoomID, fromID, self.roomID])
                self.roomID = fromRoomID
                self.mediaReload()
                self.textBrowser.textBrowser.clear()
                self.translator.textBrowser.clear()

    def rightMouseClicked(self, event):
        menu = QMenu()
        openBrowser = menu.addAction('打开直播间')
        chooseQuality = menu.addMenu('选择画质')
        originQuality = chooseQuality.addAction('原画')
        if self.quality == 10000:
            originQuality.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        bluerayQuality = chooseQuality.addAction('蓝光')
        if self.quality == 400:
            bluerayQuality.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        highQuality = chooseQuality.addAction('超清')
        if self.quality == 250:
            highQuality.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        lowQuality = chooseQuality.addAction('流畅')
        if self.quality == 80:
            lowQuality.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        if not self.top:  # 非弹出类悬浮窗
            popWindow = menu.addAction('悬浮窗播放')
        else:
            opacityMenu = menu.addMenu('调节透明度')
            percent100 = opacityMenu.addAction('100%')
            if self.opacity == 100:
                percent100.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            percent80 = opacityMenu.addAction('80%')
            if self.opacity == 80:
                percent80.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            percent60 = opacityMenu.addAction('60%')
            if self.opacity == 60:
                percent60.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            percent40 = opacityMenu.addAction('40%')
            if self.opacity == 40:
                percent40.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            percent20 = opacityMenu.addAction('20%')
            if self.opacity == 20:
                percent20.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == openBrowser:
            if self.roomID:
                QDesktopServices.openUrl(QUrl(r'https://live.bilibili.com/%s' % self.roomID))
        elif action == originQuality:
            self.changeQuality.emit([self.id, 10000])
            self.quality = 10000
            self.mediaReload()
        elif action == bluerayQuality:
            self.changeQuality.emit([self.id, 400])
            self.quality = 400
            self.mediaReload()
        elif action == highQuality:
            self.changeQuality.emit([self.id, 250])
            self.quality = 250
            self.mediaReload()
        elif action == lowQuality:
            self.changeQuality.emit([self.id, 80])
            self.quality = 80
            self.mediaReload()
        if not self.top:
            if action == popWindow:
                self.popWindow.emit([self.id, self.roomID, self.quality, False])
                self.mediaPlay(1)  # 暂停播放
        elif self.top:
            if action == percent100:
                self.setWindowOpacity(1)
                self.opacity = 100
            elif action == percent80:
                self.setWindowOpacity(0.8)
                self.opacity = 80
            elif action == percent60:
                self.setWindowOpacity(0.6)
                self.opacity = 60
            elif action == percent40:
                self.setWindowOpacity(0.4)
                self.opacity = 40
            elif action == percent20:
                self.setWindowOpacity(0.2)
                self.opacity = 20

    def resizeEvent(self, QEvent):
        self.scene.setSceneRect(1, 1, self.width() - 2, self.height() - 2)
        width = self.width() * 0.2
        self.textBrowser.resize(width, self.height() * 0.6)
        self.translator.resize(width, self.height() * 0.4)
        if width > 200:
            self.textBrowser.textBrowser.setFont(QFont('Microsoft JhengHei', 15, QFont.Bold))
            self.translator.textBrowser.setFont(QFont('Microsoft JhengHei', 15, QFont.Bold))
        elif 100 < width <= 200:
            self.textBrowser.textBrowser.setFont(QFont('Microsoft JhengHei', width // 20 + 5, QFont.Bold))
            self.translator.textBrowser.setFont(QFont('Microsoft JhengHei', width // 20 + 5, QFont.Bold))
        else:
            self.textBrowser.textBrowser.setFont(QFont('Microsoft JhengHei', 10, QFont.Bold))
            self.translator.textBrowser.setFont(QFont('Microsoft JhengHei', 10, QFont.Bold))
        self.textBrowser.move(0, 0)
        self.translator.move(0, self.textBrowser.height())
        self.textBrowser.textBrowser.verticalScrollBar().setValue(100000000)
        self.translator.textBrowser.verticalScrollBar().setValue(100000000)
        self.resizeTimer.start(50)  # 延迟50ms修改video窗口 否则容易崩溃

    def resizeVideoItem(self):
        self.resizeTimer.stop()
        self.videoItem.setSize(QSizeF(self.width(), self.height()))

    def setVolume(self, value):
        self.player.setVolume(value)
        self.volumeChanged.emit([self.id, value])

    def closeDanmu(self):
        self.setDanmu.emit([self.id, False])

    def closeTranslator(self):
        self.setTranslator.emit([self.id, False])

    def showDanmu(self):
        if self.textBrowser.isHidden() or self.translator.isHidden():
            self.textBrowser.show()
            self.translator.show()
        else:
            self.textBrowser.hide()
            self.translator.hide()
        self.setDanmu.emit([self.id, not self.textBrowser.isHidden()])
        self.setTranslator.emit([self.id, not self.translator.isHidden()])

    def mediaPlay(self, force=0):
        if force == 1:
            self.player.pause()
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif force == 2:
            self.player.play()
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        elif self.player.state() == 1:
            self.player.pause()
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.player.state() == 2:
            self.player.play()
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def mediaMute(self, force=0, emit=True):
        if force == 1:
            self.player.setMuted(False)
            self.volume.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        elif force == 2:
            self.player.setMuted(True)
            self.volume.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
        elif self.player.isMuted():
            self.player.setMuted(False)
            self.volume.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        else:
            self.player.setMuted(True)
            self.volume.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
        if emit:
            self.mutedChanged.emit([self.id, self.player.isMuted()])

    def mediaReload(self):
        if self.roomID:
            # self.player.stop()
            self.getMediaURL.setConfig(self.roomID, self.quality)  # 设置房号和画质
            self.getMediaURL.start()
        else:
            self.mediaStop()

    def mediaStop(self):
        self.roomID = 0
        self.url = QMediaContent(QUrl(''))
        self.topLabel.setText('    窗口%s  未定义的直播间' % (self.id + 1))
        self.titleLabel.setText('未定义')
        # self.player.stop()
        self.player.setMedia(self.url)
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.deleteMedia.emit(self.id)
        try:
            self.danmu.message.disconnect(self.playDanmu)
        except:
            pass
        self.danmu.terminate()
        self.danmu.quit()
        self.danmu.wait()

    def setMedia(self, qurl):
        self.setTitle()
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.danmu.setRoomID(str(self.roomID))
        try:
            self.danmu.message.disconnect(self.playDanmu)
        except:
            pass
        self.danmu.message.connect(self.playDanmu)
        self.danmu.terminate()
        self.danmu.start()
        self.player.setMedia(qurl)
        self.player.play()

    def setTitle(self):
        if not self.roomID:
            title = '未定义的直播间'
            uname = '未定义'
        else:
            r = requests.get(r'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id=%s' % self.roomID)
            data = json.loads(r.text)
            if data['message'] == '房间已加密':
                title = '房间已加密'
                uname = '房号: %s' % self.roomID
            elif not data['data']:
                title = '房间好像不见了-_-？'
                uname = '未定义'
            else:
                data = data['data']
                liveStatus = data['room_info']['live_status']
                title = data['room_info']['title']
                uname = data['anchor_info']['base_info']['uname']
                if liveStatus != 1:
                    uname = '（未开播）' + uname
        self.topLabel.setText('    窗口%s  %s' % (self.id + 1, title))
        self.titleLabel.setText(uname)

    def playDanmu(self, message):
        token = False
        for symbol in ['【', '[', '{']:
            if symbol in message:
                self.translator.textBrowser.append(message)
                token = True
                break
        if not token:
            self.textBrowser.textBrowser.append(message)
