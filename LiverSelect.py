"""
DD监控室主界面上方的控制条里的ScrollArea里面的卡片模块
包含主播开播/下播检测和刷新展示 置顶排序 录制管理等功能
"""
import requests, json, time, codecs, logging, os
from PyQt5.QtWidgets import * 	# QAction,QFileDialog
from PyQt5.QtGui import *		# QIcon,QPixmap
from PyQt5.QtCore import * 		# QSize


header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
}


class CardLabel(QLabel):
    def __init__(self, text='NA', fontColor='#f1fefb', size=11):
        super(CardLabel, self).__init__()
        self.setFont(QFont('微软雅黑', size, QFont.Bold))
        self.setStyleSheet('color:%s;background-color:#00000000' % fontColor)
        self.setText(text)

    def setBrush(self, fontColor):
        self.setStyleSheet('color:%s;background-color:#00000000' % fontColor)


class OutlinedLabel(QLabel):
    def __init__(self, text='NA', fontColor='#FFFFFF', outColor='#222222', size=11):
        super().__init__()
        self.setFont(QFont('微软雅黑', size, QFont.Bold))
        self.setStyleSheet('background-color:#00000000')
        self.setText(text)
        self.setBrush(fontColor)
        self.setPen(outColor)
        self.w = self.font().pointSize() / 15
        self.metrics = QFontMetrics(self.font())

    def setBrush(self, brush):
        brush = QColor(brush)
        if not isinstance(brush, QBrush):
            brush = QBrush(brush)
        self.brush = brush

    def setPen(self, pen):
        pen = QColor(pen)
        if not isinstance(pen, QPen):
            pen = QPen(pen)
        pen.setJoinStyle(Qt.RoundJoin)
        self.pen = pen

    def paintEvent(self, event):
        rect = self.rect()
        indent = self.indent()
        x = rect.left() + indent - min(self.metrics.leftBearing(self.text()[0]), 0)
        y = (rect.height() + self.metrics.ascent() - self.metrics.descent()) / 2
        path = QPainterPath()
        path.addText(x, y, self.font(), self.text())
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        self.pen.setWidthF(self.w * 2)
        qp.strokePath(path, self.pen)
        qp.fillPath(path, self.brush)


class CircleImage(QWidget):
    """圆形头像框"""
    def __init__(self, parent=None):
        super(CircleImage, self).__init__(parent)
        self.setFixedSize(60, 60)
        self.circle_image = None

    def set_image(self, image):
        self.circle_image = image
        self.update()

    def paintEvent(self, event):
        if self.circle_image:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = Qt.NoPen
            painter.setPen(pen)
            brush = QBrush(self.circle_image)
            painter.setBrush(brush)
            painter.drawRoundedRect(self.rect(), self.width() / 2, self.height() / 2)


class PushButton(QPushButton):
    def __init__(self, name, pushToken=False):
        super().__init__()
        self.setText(name)
        self.pushToken = pushToken
        if self.pushToken:
            self.setStyleSheet('background-color:#3daee9;border-width:1px')
        else:
            self.setStyleSheet('background-color:#31363b;border-width:1px')


# class RequestAPI(QThread):
#     data = pyqtSignal(dict)
#
#     def __init__(self, roomID):
#         super(RequestAPI, self).__init__()
#         self.roomID = roomID
#
#     def run(self):
#         r = requests.get(r'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id=%s' % self.roomID)
#         self.data.emit(json.loads(r.text))


class RecordThread(QThread):
    """获取直播推流并录制
    TODO: 换用 bilibili_api.live.get_room_play_url(room_id)
    """
    downloadTimer = pyqtSignal(str)
    downloadError = pyqtSignal(str)

    def __init__(self, roomID):
        super(RecordThread, self).__init__()
        self.roomID = roomID
        self.recordToken = False
        self.downloadToken = False
        self.downloadTime = 0  # s
        self.checkTimer = QTimer()
        self.checkTimer.timeout.connect(self.checkDownlods)
        self.reconnectCount = 0

    def checkDownlods(self):
        if self.downloadToken:
            self.downloadToken = False
            if not self.downloadTime % 60:  # 每分钟刷新一次
                self.downloadTimer.emit('%dmin' % (self.downloadTime / 60))
            self.downloadTime += 3
        else:
            self.reconnectCount += 1
            if self.reconnectCount > 60:  # 60 x 3s = 180s重试 超时了就退出
                self.downloadError.emit(self.roomID)

    def setSavePath(self, savePath):
        self.savePath = savePath

    def run(self):
        self.reconnectCount = 0
        api = r'https://api.live.bilibili.com/room/v1/Room/playUrl?cid=%s&platform=web&qn=10000' % self.roomID
        r = requests.get(api)
        try:
            url = json.loads(r.text)['data']['durl'][0]['url']
            download = requests.get(url, stream=True, headers=header)
            self.recordToken = True
            self.downloadTime = 0  # 初始化下载时间为0s
            self.cacheVideo = open(self.savePath, 'wb')
            for chunk in download.iter_content(chunk_size=512):
                if not self.recordToken:
                    break
                if chunk:
                    self.downloadToken = True
                    self.cacheVideo.write(chunk)
            self.cacheVideo.close()
        except:
            logging.exception("下载视频到缓存失败")


class DownloadImage(QThread):
    """下载图片"""
    img = pyqtSignal(QPixmap)
    img_origin = pyqtSignal(QPixmap)

    def __init__(self, scaleW, scaleH, keyFrame=False):
        super(DownloadImage, self).__init__()
        self.W = scaleW
        self.H = scaleH
        self.keyFrame = keyFrame

    def setUrl(self, url):
        self.url = url

    def run(self):
        if self.W == 60:
            r = requests.get(self.url + '@100w_100h.jpg')
        else:
            r = requests.get(self.url)
        img = QPixmap.fromImage(QImage.fromData(r.content))
        self.img.emit(img.scaled(self.W, self.H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        if self.keyFrame:
            self.img_origin.emit(img)


class CoverLabel(QLabel):
    """封面的文字"""
    addToWindow = pyqtSignal(list)
    deleteCover = pyqtSignal(str)
    changeTopToken = pyqtSignal(list)

    def __init__(self, roomID, topToken=False):
        super(CoverLabel, self).__init__()
        QToolTip.setFont(QFont('微软雅黑', 16, QFont.Bold))
        self.setAcceptDrops(True)
        self.roomID = roomID
        self.topToken = topToken
        self.isPlaying = False  # 正在播放
        self.title = 'NA'  # 这里其实一开始设计的时候写错名字了 实际这里是用户名不是房间号 将错就错下去了
        self.roomTitle = ''  # 这里才是真的存放房间名的地方
        self.recordState = 0  # 0 无录制任务  1 录制中  2 等待开播录制
        self.savePath = ''
        self.setFixedSize(160, 90)
        self.setObjectName('cover')
        self.setFrameShape(QFrame.Box)
        self.firstUpdateToken = True
        self.layout = QGridLayout(self)
        self.profile = CircleImage()
        self.layout.addWidget(self.profile, 0, 4, 2, 2)
        if topToken:
            brush = '#FFC125'
            self.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:#dfa616;background-color:#5a636d}')
        else:
            brush = '#f1fefb'
            self.setStyleSheet('background-color:#5a636d')  # 灰色背景
        self.titleLabel = OutlinedLabel(fontColor=brush)
        # self.titleLabel = CardLabel(fontColor=brush)
        self.layout.addWidget(self.titleLabel, 0, 0, 1, 6)
        # self.roomIDLabel = OutlinedLabel(roomID, fontColor=brush)
        # self.roomIDLabel = CardLabel(roomID, fontColor=brush)
        # self.layout.addWidget(self.roomIDLabel, 1, 0, 1, 6)
        self.stateLabel = OutlinedLabel(size=13)
        # self.stateLabel = CardLabel(size=13)
        self.stateLabel.setText('检测中')
        self.liveState = 0  # 0 未开播  1 直播中  2 投稿视频   -1 错误
        self.layout.addWidget(self.stateLabel, 1, 0, 1, 6)
        self.downloadFace = DownloadImage(60, 60)
        self.downloadFace.img.connect(self.updateProfile)
        self.downloadKeyFrame = DownloadImage(160, 90, True)
        self.downloadKeyFrame.img.connect(self.updateKeyFrame)
        self.downloadKeyFrame.img_origin.connect(self.setToolTipKeyFrame)

        self.recordThread = RecordThread(roomID)
        self.recordThread.downloadTimer.connect(self.refreshStateLabel)
        self.recordThread.downloadError.connect(self.recordError)

    def updateLabel(self, info):
        if not info[0]:  # 用户或直播间不存在
            self.liveState = -1
            self.roomTitle = ''
            self.setToolTip(self.roomTitle)
            if info[2]:
                self.titleLabel.setText(info[2])
                self.stateLabel.setText('房间可能被封')
            else:
                self.titleLabel.setText(info[1])
                self.stateLabel.setText('无该房间或已加密')
            self.setStyleSheet('background-color:#8B3A3A')  # 红色背景
        else:
            if self.firstUpdateToken:  # 初始化
                self.firstUpdateToken = False
                self.downloadFace.setUrl(info[3])  # 启动下载头像线程
                self.downloadFace.start()
                # self.roomIDLabel.setText(info[1])  # 房间号
                self.titleLabel.setText(info[2])  # 名字
                self.title = info[2]
            if info[4] == 1:  # 直播中
                self.liveState = 1
                self.downloadKeyFrame.setUrl(info[5])  # 启动下载关键帧线程
                self.downloadKeyFrame.start()
                self.roomTitle = info[6]  # 房间直播标题
                # self.setToolTip(self.roomTitle)  # 改用self.setToolTipKeyFrame里面设置tooltip
            else:  # 未开播
                self.liveState = 0
                self.roomTitle = ''  # 房间直播标题
                self.setToolTip(self.roomTitle)
                self.clear()
                if self.isPlaying:
                    self.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:red;background-color:#5a636d}')
                elif self.topToken:
                    self.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:#dfa616;background-color:#5a636d}')
                else:
                    self.setStyleSheet('background-color:#5a636d')  # 灰色背景
            self.refreshStateLabel()

    def refreshStateLabel(self, downloadTime=''):
        if self.liveState == 1:
            if self.recordState == 1:  # 录制中
                self.stateLabel.setBrush('#87CEFA')  # 录制中为蓝色字体
                if downloadTime:
                    self.stateLabel.setText('· 录制中 %s' % downloadTime)
            else:
                self.stateLabel.setBrush('#7FFFD4')  # 直播中为绿色字体
                self.stateLabel.setText('· 直播中')
        else:
            if self.recordState == 2:  # 等待录制
                self.stateLabel.setBrush('#FFA500')  # 待录制为橙色字体
                self.stateLabel.setText('· 等待开播')
            else:
                self.stateLabel.setBrush('#FF6A6A')  # 未开播为红色字体
                self.stateLabel.setText('· 未开播')

    def recordError(self, roomID):
        self.recordThread.checkTimer.stop()
        self.refreshStateLabel()
        QMessageBox.information(self, '录制中止', '%s %s 录制结束 请检查网络或主播是否掉线' % (self.title, roomID), QMessageBox.Ok)

    def updateProfile(self, img):
        self.profile.set_image(img)

    def updateKeyFrame(self, img):
        self.setPixmap(img)

    def setToolTipKeyFrame(self, img):
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        img.save(buffer, "PNG", quality=100)
        image = bytes(buffer.data().toBase64()).decode()
        html = '<img src="data:image/png;base64,{}">'.format(image)
        self.setToolTip('<div style="text-align:center">%s</div><br>%s<br/>' % (self.roomTitle.strip(), html))

    def dragEnterEvent(self, QDragEnterEvent):
        QDragEnterEvent.acceptProposedAction()

    def mousePressEvent(self, QMouseEvent):  # 设置drag事件 发送拖动封面的房间号
        if QMouseEvent.button() == Qt.LeftButton:
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText('roomID:%s' % self.roomID)
            drag.setMimeData(mimeData)
            drag.exec_()
        elif QMouseEvent.button() == Qt.RightButton:
            menu = QMenu()
            addTo = menu.addMenu('添加至窗口 ►')
            addWindow = []
            for win in range(1, 10):
                addWindow.append(addTo.addAction('窗口%s' % win))
            if not self.topToken:
                top = menu.addAction('添加置顶')
            else:
                top = menu.addAction('取消置顶')
            record = None
            if self.recordState == 0:  # 无录制任务
                if self.liveState == 1:
                    record = menu.addAction('录制(最高画质)')
                elif self.liveState in [0, 2]:  # 未开播或轮播
                    record = menu.addAction('开播自动录制')
            else:  # 录制中或等待录制
                record = menu.addAction('取消录制')
            openBrowser = menu.addAction('打开直播间')
            copyRoomID = menu.addAction('复制房号 %s' % self.roomID)
            menu.addSeparator()  # 添加分割线，防止误操作
            delete = menu.addAction('删除')
            action = menu.exec_(self.mapToGlobal(QMouseEvent.pos()))
            if action == delete:
                self.deleteCover.emit(self.roomID)
                self.roomID = '0'
                self.hide()
            elif action == top:
                if self.topToken:
                    self.titleLabel.setBrush('#f1fefb')
                    # self.roomIDLabel.setBrush('#f1fefb')
                    if self.isPlaying:
                        self.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:red;background-color:#5a636d}')
                    else:
                        self.setStyleSheet('border-width:0px')
                else:
                    self.titleLabel.setBrush('#FFC125')
                    # self.roomIDLabel.setBrush('#FFC125')
                    if self.isPlaying:
                        self.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:red;background-color:#5a636d}')
                    else:
                        self.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:#dfa616;background-color:#5a636d}')
                self.topToken = not self.topToken
                self.changeTopToken.emit([self.roomID, self.topToken])  # 发送修改后的置顶token
            elif action == record:
                if self.roomID != '0':
                    if self.recordState == 0:  # 无录制任务
                        saveName = '%s_%s_%s' % (self.title, self.roomTitle,
                                                 time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time())))
                        self.savePath = QFileDialog.getSaveFileName(self, "选择保存路径", saveName, "*.flv")[0]
                        if self.savePath:  # 保存路径有效
                            if self.liveState == 1:  # 直播中
                                self.recordThread.setSavePath(self.savePath)
                                self.recordThread.start()
                                self.recordThread.checkTimer.start(3000)
                                self.recordState = 1  # 改为录制状态
                                self.refreshStateLabel('0min')
                            elif self.liveState in [0, 2]:  # 未开播或轮播中
                                self.recordState = 2  # 改为等待录制状态
                                self.refreshStateLabel()
                    elif self.recordState == 1:  # 录制中→取消录制
                        self.recordState = 0  # 取消录制
                        self.recordThread.checkTimer.stop()
                        self.recordThread.recordToken = False  # 设置录像线程标志位让它自行退出结束
                        self.refreshStateLabel()
                    elif self.recordState == 2:  # 等待录制→取消录制
                        self.recordState = 0  # 取消录制
                        self.recordThread.checkTimer.stop()
                        self.refreshStateLabel()
            elif action == openBrowser:
                if self.roomID != '0':
                    QDesktopServices.openUrl(QUrl(r'https://live.bilibili.com/%s' % self.roomID))
            elif action == copyRoomID:
                clipboard = QApplication.clipboard()
                clipboard.setText(self.roomID)
            elif action == addTo:
                for index, i in enumerate(addWindow):
                    if action == i:
                        self.addToWindow.emit([index, self.roomID])  # 添加至窗口 窗口 房号
                        break


class GetHotLiver(QThread):
    """获取指定分区的 热榜"""
    roomInfoSummary = pyqtSignal(list)

    def __init__(self):
        super(GetHotLiver, self).__init__()

    def run(self):
        try:
            roomInfoSummary = []
            for area in [9, 2, 3, 6, 1]:
                pageSummary = []
                for p in range(1, 6):
                    api = 'https://api.live.bilibili.com/xlive/web-interface/v1/second/getList?platform=web&parent_area_id=%s&page=%s' % (area, p)
                    r = requests.get(api)
                    data = json.loads(r.text)['data']['list']
                    if data:
                        for info in data:
                            pageSummary.append([info['uname'], info['title'], str(info['roomid'])])
                    time.sleep(0.1)
                roomInfoSummary.append(pageSummary)
            if roomInfoSummary:
                self.roomInfoSummary.emit(roomInfoSummary)
        except:
            logging.exception('房间信息获取失败')


class GetFollows(QThread):
    """获取指定用户的关注列表
    TODO: 换用
        + 获取关注列表：bilibili_api.user.get_followings_g(uid)
        + 获取直播间地址：bilibili_api.user.get_live_info(uid)
    """
    roomInfoSummary = pyqtSignal(list)

    def __init__(self):
        super(GetFollows, self).__init__()
        self.uid = None

    def setUID(self, uid):
        self.uid = uid

    def run(self):
        if self.uid:
            followsIDs = []
            roomIDList = []
            for p in range(1, 6):
                r = requests.get(r'https://api.bilibili.com/x/relation/followings?vmid=%s&pn=%s' % (self.uid, p))
                followList = json.loads(r.text)['data']['list']
                if followList:
                    for i in followList:
                        followsIDs.append(i['mid'])
            if followsIDs:
                data = json.dumps({'uids': followsIDs})
                r = requests.post(r'https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids', data=data)
                r.encoding = 'utf8'
                data = json.loads(r.text)['data']
                for followID in followsIDs:
                    for uid, info in data.items():
                        if uid == str(followID):
                            roomIDList.append([info['uname'], info['title'], str(info['room_id'])])
                            break
            else:
                logging.error('未获取到有效房号列表或房号列表为空')
            if roomIDList:
                self.roomInfoSummary.emit(roomIDList)


class DownloadVTBList(QThread):
    """更新 VTB 信息"""
    vtbList = pyqtSignal(list)

    def __init__(self, parent=None):
        super(DownloadVTBList, self).__init__(parent)

    def run(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            r = requests.get(r'https://github.com/zhimingshenjun/DD_Monitor/blob/master/utils/vtb.csv', headers=headers)
            # r.encoding = 'utf8'
            vtbList = []
            html = r.text.split('\n')
            for cnt, line in enumerate(html):
                if 'blob-num js-line-number' in line:
                    vtbID = html[cnt + 1].split('>')[1].split('<')[0]
                    roomID = html[cnt + 2].split('>')[1].split('<')[0]
                    haco = html[cnt + 3].split('>')[1].split('<')[0]
                    vtbList.append('%s,%s,%s\n' % (vtbID, roomID, haco))
            if vtbList:
                self.vtbList.emit(vtbList)
        except:
            logging.exception("vtbs 列表获取失败")


class HotLiverTable(QTableWidget):
    """关注列表"""
    addToWindow = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        addTo = self.menu.addMenu('添加至窗口 ►')
        addWindow = []
        for win in range(1, 10):
            addWindow.append(addTo.addAction('窗口%s' % win))
        action = self.menu.exec_(self.mapToGlobal(event.pos()))
        for index, i in enumerate(addWindow):
            if action == i:
                text=self.item(self.currentRow(), 2).text()
                self.addToWindow.emit([index, text])
                break


class AddLiverRoomWidget(QWidget):
    """添加直播间 - 独立弹窗"""
    roomList = pyqtSignal(dict)

    def __init__(self,application_path):
        super(AddLiverRoomWidget, self).__init__()
        self.application_path = application_path
        self.resize(600, 900)
        self.setWindowTitle('添加直播间（房号太多的话尽量分批次添加 避免卡死）')
        self.hotLiverDict = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
        self.followLiverList = []
        layout = QGridLayout(self)
        layout.addWidget(QLabel('请输入B站直播间房号 多个房号之间用空格隔开'), 0, 0, 1, 4)
        self.roomEditText = ''
        self.roomEdit = QLineEdit()
        # self.roomEdit.textChanged.connect(self.editChange)  # 手感不好 还是取消了
        layout.addWidget(self.roomEdit, 1, 0, 1, 5)
        confirm = QPushButton('完成')
        confirm.setFixedHeight(28)
        confirm.clicked.connect(self.sendSelectedRoom)
        confirm.setStyleSheet('background-color:#3daee9')
        layout.addWidget(confirm, 0, 4, 1, 1)

        tab = QTabWidget()
        layout.addWidget(tab, 2, 0, 5, 5)

        hotLiverPage = QWidget()
        hotLiverLayout = QGridLayout(hotLiverPage)
        hotLiverLayout.setContentsMargins(1, 1, 1, 1)

        self.virtual = PushButton('虚拟主播', True)
        self.virtual.clicked.connect(lambda: self.switchHotLiver(0))
        hotLiverLayout.addWidget(self.virtual, 0, 0, 1, 1)
        self.onlineGame = PushButton('网游')
        self.onlineGame.clicked.connect(lambda: self.switchHotLiver(1))
        hotLiverLayout.addWidget(self.onlineGame, 0, 1, 1, 1)
        self.mobileGame = PushButton('手游')
        self.mobileGame.clicked.connect(lambda: self.switchHotLiver(2))
        hotLiverLayout.addWidget(self.mobileGame, 0, 2, 1, 1)
        self.consoleGame = PushButton('单机')
        self.consoleGame.clicked.connect(lambda: self.switchHotLiver(3))
        hotLiverLayout.addWidget(self.consoleGame, 0, 3, 1, 1)
        self.entertainment = PushButton('娱乐')
        self.entertainment.clicked.connect(lambda: self.switchHotLiver(4))
        hotLiverLayout.addWidget(self.entertainment, 0, 4, 1, 1)
        # self.broadcasting = PushButton('电台')
        # self.broadcasting.clicked.connect(lambda: self.switchHotLiver(5))
        # hotLiverLayout.addWidget(self.broadcasting, 0, 5, 1, 1)
        self.buttonList = [self.virtual, self.onlineGame, self.mobileGame, self.consoleGame, self.entertainment]
        self.currentPage = 0

        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(0, 0, self.width(), 20)
        self.progressBar.setRange(0,0)

        self.hotLiverTable = HotLiverTable()
        self.hotLiverTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.hotLiverTable.verticalScrollBar().installEventFilter(self)
        self.hotLiverTable.verticalHeader().sectionClicked.connect(self.hotLiverAdd)
        self.hotLiverTable.setColumnCount(3)
        self.hotLiverTable.setRowCount(100)
        self.hotLiverTable.setVerticalHeaderLabels(['添加'] * 100)
        self.hotLiverTable.setHorizontalHeaderLabels(['主播名', '直播间标题', '直播间房号'])
        self.hotLiverTable.setColumnWidth(0, 130)
        self.hotLiverTable.setColumnWidth(1, 240)
        self.hotLiverTable.setColumnWidth(2, 130)
        self.hotLiverTable.setEnabled(False) #启动时暂时禁用table
        hotLiverLayout.addWidget(self.hotLiverTable, 1, 0, 1, 5)
        self.getHotLiver = GetHotLiver()
        self.getHotLiver.roomInfoSummary.connect(self.collectHotLiverInfo)

        followsPage = QWidget()
        followsLayout = QGridLayout(followsPage)
        followsLayout.setContentsMargins(0, 0, 0, 0)
        followsLayout.addWidget(QLabel(), 0, 2, 1, 1)
        followsLayout.addWidget(QLabel('自动添加你关注的up直播间 （只能拉取最近关注的100名）'), 0, 3, 1, 3)
        self.uidEdit = QLineEdit()
        self.uidEdit.setPlaceholderText('请输入你的uid')
        self.uidEdit.setMinimumWidth(120)
        self.uidEdit.setMaximumWidth(300)
        followsLayout.addWidget(self.uidEdit, 0, 0, 1, 1)
        uidCheckButton = QPushButton('查询')
        uidCheckButton.setFixedHeight(27)
        uidCheckButton.setStyleSheet('background-color:#3daee9')
        uidCheckButton.clicked.connect(self.checkFollows)  # 查询关注
        followsLayout.addWidget(uidCheckButton, 0, 1, 1, 1)
        self.followsTable = QTableWidget()
        self.followsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.followsTable.verticalScrollBar().installEventFilter(self)
        self.followsTable.verticalHeader().sectionClicked.connect(self.followLiverAdd)
        self.followsTable.setColumnCount(3)
        self.followsTable.setRowCount(100)
        self.followsTable.setVerticalHeaderLabels(['添加'] * 100)
        self.followsTable.setHorizontalHeaderLabels(['主播名', '直播间标题', '直播间房号'])
        self.followsTable.setColumnWidth(0, 130)
        self.followsTable.setColumnWidth(1, 240)
        self.followsTable.setColumnWidth(2, 130)
        followsLayout.addWidget(self.followsTable, 1, 0, 6, 6)
        self.getFollows = GetFollows()
        self.getFollows.roomInfoSummary.connect(self.collectFollowLiverInfo)

        hacoPage = QWidget()  # 添加内置的vtb列表
        hacoLayout = QGridLayout(hacoPage)
        hacoLayout.setContentsMargins(1, 1, 1, 1)
        self.refreshButton = PushButton('更新名单')
        self.refreshButton.clicked.connect(self.refreshHacoList)
        hacoLayout.addWidget(self.refreshButton, 0, 0, 1, 1)
        self.vtbSearchButton = PushButton('查询VUP')
        self.vtbSearchButton.clicked.connect(self.vtbSearch)
        hacoLayout.addWidget(self.vtbSearchButton, 0, 1, 1, 1)
        self.hacoTable = QTableWidget()
        self.hacoTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.hacoTable.verticalScrollBar().installEventFilter(self)
        self.hacoTable.verticalHeader().sectionClicked.connect(self.hacoAdd)
        self.hacoTable.setColumnCount(3)
        try:
            self.vtbList = []
            vtbs = codecs.open(os.path.join(self.application_path,'utils/vtb.csv'), 'r', encoding='utf-8')
            for line in vtbs:
                line = line.strip()
                if line:
                    self.vtbList.append(line.split(','))
                else:
                    self.vtbList.append(['', '', ''])
            vtbs.close()
            self.hacoTable.setRowCount(len(self.vtbList))
            self.hacoTable.setVerticalHeaderLabels(['添加'] * len(self.vtbList))
            for y, line in enumerate(self.vtbList):
                for x in range(3):
                    self.hacoTable.setItem(y, x, QTableWidgetItem(line[x]))
        except:
            logging.exception('vtb.csv 解析失败')

        self.hacoTable.setHorizontalHeaderLabels(['主播名', '直播间房号', '所属'])
        self.hacoTable.setColumnWidth(0, 160)
        self.hacoTable.setColumnWidth(1, 160)
        self.hacoTable.setColumnWidth(2, 160)
        hacoLayout.addWidget(self.hacoTable, 1, 0, 10, 5)
        self.downloadVTBList = DownloadVTBList()
        self.downloadVTBList.vtbList.connect(self.collectVTBList)
        # self.downloadVTBList.start()

        tab.addTab(hotLiverPage, '正在直播')
        tab.addTab(hacoPage, '个人势/箱')
        tab.addTab(followsPage, '关注添加')

    def editChange(self):  # 提取输入文本中的数字
        if len(self.roomEdit.text()) > len(self.roomEditText):
            roomEditText = ''
            roomIDList = self.roomEdit.text().split(' ')
            for roomID in roomIDList:
                strList = map(lambda x: x if x.isdigit() else '', roomID)
                roomID = ''
                digitToken = False
                for s in strList:
                    if s:
                        roomID += s
                        digitToken = True
                    elif digitToken:
                        roomID += ' '
                        if roomID not in roomEditText:
                            roomEditText += roomID
                        roomID = ''
                        digitToken = False
                if roomID:
                    roomID += ' '
                    if roomID not in roomEditText:
                        roomEditText += roomID
            self.roomEdit.setText(roomEditText)
            self.roomEditText = roomEditText

    def closeEvent(self, event):
        if self.getHotLiver.isRunning():
            self.getHotLiver.terminate()

    def collectHotLiverInfo(self, info):
        self.hotLiverDict = {}
        self.progressBar.hide()
        self.hotLiverTable.setEnabled(True)
        for page, hotLiverList in enumerate(info):
            self.hotLiverDict[page] = hotLiverList
            for y, line in enumerate(hotLiverList):
                for x, txt in enumerate(line):
                    if page == self.currentPage:
                        try:
                            self.hotLiverTable.setItem(y, x, QTableWidgetItem(txt))
                        except:
                            logging.exception('热门直播表插入失败')

    def switchHotLiver(self, index):
        if not self.buttonList[index].pushToken:
            self.currentPage = index
            for cnt, button in enumerate(self.buttonList):
                if cnt == index:  # 点击的按钮
                    button.pushToken = True
                    button.setStyleSheet('background-color:#3daee9;border-width:1px')
                else:
                    button.pushToken = False
                    button.setStyleSheet('background-color:#31363b;border-width:1px')
            self.hotLiverTable.clear()
            self.hotLiverTable.setColumnCount(3)
            self.hotLiverTable.setRowCount(100)
            self.hotLiverTable.setVerticalHeaderLabels(['添加'] * 100)
            self.hotLiverTable.setHorizontalHeaderLabels(['主播名', '直播间标题', '直播间房号'])
            self.hotLiverTable.setColumnWidth(0, 130)
            self.hotLiverTable.setColumnWidth(1, 240)
            self.hotLiverTable.setColumnWidth(2, 130)
            hotLiverList = self.hotLiverDict[index]
            for y, line in enumerate(hotLiverList):
                for x, txt in enumerate(line):
                    try:
                        self.hotLiverTable.setItem(y, x, QTableWidgetItem(txt))
                    except:
                        logging.exception('热门直播表更换失败')

    def refreshHacoList(self):
        self.refreshButton.clicked.disconnect(self.refreshHacoList)
        self.refreshButton.setText('更新中...')
        self.downloadVTBList.start()

    def vtbSearch(self):
        QDesktopServices.openUrl(QUrl(r'https://vtbs.moe/detail'))

    def collectVTBList(self, vtbList):
        try:
            vtbs = codecs.open(os.path.join(self.application_path, 'utils/vtb.csv'), 'w', encoding='utf-8')
            for line in vtbList:
                vtbs.write(line)
            vtbs.close()
            self.vtbList = []
            for line in vtbList:
                self.vtbList.append(line.split(','))
            self.hacoTable.clear()
            self.hacoTable.setRowCount(len(self.vtbList))
            self.hacoTable.setVerticalHeaderLabels(['添加'] * len(self.vtbList))
            self.hacoTable.setHorizontalHeaderLabels(['主播名', '直播间房号', '所属'])
            for y, line in enumerate(self.vtbList):
                for x in range(3):
                    self.hacoTable.setItem(y, x, QTableWidgetItem(line[x]))
            QMessageBox.information(self, '更新VUP名单', '更新完成', QMessageBox.Ok)
        except:
            logging.exception('vtb.csv 写入失败')
            QMessageBox.information(self, '更新VUP名单', '更新失败 请检查网络', QMessageBox.Ok)
        self.refreshButton.setText('更新名单')
        self.refreshButton.clicked.connect(self.refreshHacoList)

    def sendSelectedRoom(self):
        self.closeEvent(None)
        tmpList = self.roomEdit.text().strip().replace('\t', ' ').split(' ')
        roomList = {}
        for i in tmpList:
            if i.isnumeric():
                roomList[i] = False  # 全部统一为字符串格式的roomid
        self.roomList.emit(roomList)
        self.roomEdit.clear()
        self.hide()

    def hotLiverAdd(self, row):
        try:
            hotLiverList = self.hotLiverDict[self.currentPage]
            roomID = hotLiverList[row][2]
            addedRoomID = self.roomEdit.text()
            if roomID not in addedRoomID:
                addedRoomID += ' %s' % roomID
                self.roomEdit.setText(addedRoomID)
        except:
            logging.exception('热门主播添加失败')

    def hacoAdd(self, row):
        try:
            roomID = self.vtbList[row][1]
            if roomID:
                addedRoomID = self.roomEdit.text()
                if roomID not in addedRoomID:
                    addedRoomID += ' %s' % roomID
                    self.roomEdit.setText(addedRoomID)
        except:
            logging.exception('hacoAdd 失败')

    def checkFollows(self):
        if self.uidEdit.text().isdigit():
            self.getFollows.setUID(self.uidEdit.text())
            self.getFollows.start()

    def collectFollowLiverInfo(self, info):
        self.followLiverList = []
        for y, line in enumerate(info):
            self.followLiverList.append(line[2])
            for x, txt in enumerate(line):
                try:
                    self.followsTable.setItem(y, x, QTableWidgetItem(txt))
                except:
                    logging.exception('关注列表添加失败')

    def followLiverAdd(self, row):
        try:
            roomID = self.followLiverList[row]
            addedRoomID = self.roomEdit.text()
            if roomID not in addedRoomID:
                addedRoomID += ' %s' % roomID
                self.roomEdit.setText(addedRoomID)
        except:
            logging.exception('关注列表添加失败')


class CollectLiverInfo(QThread):
    """批量获取直播间信息
    + 直播状态 'live_status'
    + 标题 'title'
    + 封面 'cover'
    + 关键帧 'keyframe'
    + 头像 'face'

    TODO:
    + bilibili_api.live.get_room_info(room_id)
    """
    liverInfo = pyqtSignal(list)

    def __init__(self, roomIDList):
        super(CollectLiverInfo, self).__init__()
        self.roomIDList = roomIDList

    def setRoomIDList(self, roomIDList):
        self.roomIDList = roomIDList

    def run(self):
        logging.debug("Collecting Liver Info...")
        while 1:
            try:
                liverInfo = []
                data = json.dumps({'ids': self.roomIDList})  # 根据直播间房号批量获取直播间信息
                r = requests.post(r'https://api.live.bilibili.com/room/v2/Room/get_by_ids', data=data)
                r.encoding = 'utf8'
                data = json.loads(r.text)['data']
                uidList = []
                for roomID in data:
                    uidList.append(data[roomID]['uid'])
                data = json.dumps({'uids': uidList})
                r = requests.post(r'https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids', data=data)
                r.encoding = 'utf8'
                data = json.loads(r.text)['data']
                if data:
                    for roomID in self.roomIDList:
                        exist = False
                        for uid, info in data.items():
                            if roomID == info['room_id']:
                                title = info['title']
                                uname = info['uname']
                                face = info['face']
                                liveStatus = info['live_status']
                                keyFrame = info['keyframe']
                                exist = True
                                liverInfo.append([uid, str(roomID), uname, face, liveStatus, keyFrame, title])
                                break
                        try:
                            if not exist:
                                r = requests.get(r'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id=%s' % roomID)
                                r.encoding = 'utf8'
                                banData = json.loads(r.text)['data']
                                if banData:
                                    try:
                                        uname = banData['anchor_info']['base_info']['uname']
                                    except:
                                        uname = ''
                                else:
                                    uname = ''
                                liverInfo.append([None, str(roomID), uname])
                        except Exception as e:
                            print(str(e))
                if liverInfo:
                    self.liverInfo.emit(liverInfo)
                time.sleep(60)  # 冷却时间
            except Exception as e:
                logging.error(str(e))


class LiverPanel(QWidget):
    """关注的直播间"""
    addToWindow = pyqtSignal(list)
    dumpConfig = pyqtSignal()
    refreshIDList = pyqtSignal(list)
    startLiveList = pyqtSignal(list)

    def __init__(self, roomIDDict, app_path):
        super(LiverPanel, self).__init__()
        self.application_path = app_path
        self.refreshCount = 0
        self.oldLiveStatus = {}
        self.addLiverRoomWidget = AddLiverRoomWidget(self.application_path)
        self.addLiverRoomWidget.roomList.connect(self.addLiverRoomList)
        self.addLiverRoomWidget.hotLiverTable.addToWindow.connect(self.addCoverToPlayer)
        self.multiple = 1
        self.layout = QGridLayout(self)
        self.layout.setSpacing(9)
        self.layout.setContentsMargins(7, 7, 7, 7)
        self.coverList = []
        for roomID, topToken in roomIDDict.items():
            self.coverList.append(CoverLabel(roomID, topToken))
            self.coverList[-1].addToWindow.connect(self.addCoverToPlayer)  # 添加至窗口播放信号
            self.coverList[-1].deleteCover.connect(self.deleteCover)
            self.coverList[-1].changeTopToken.connect(self.changeTop)
        for cover in self.coverList:  # 先添加置顶卡片
            if cover.topToken:
                self.layout.addWidget(cover)
        for cover in self.coverList:  # 再添加普通卡片
            if not cover.topToken:
                self.layout.addWidget(cover)
        self.roomIDDict = roomIDDict
        self.collectLiverInfo = CollectLiverInfo(list(map(int, self.roomIDDict.keys())))  # 转成整型
        self.collectLiverInfo.liverInfo.connect(self.refreshRoomPanel)
        self.collectLiverInfo.start()

    def openLiverRoomPanel(self):
        self.addLiverRoomWidget.getHotLiver.start()
        self.addLiverRoomWidget.hide()
        self.addLiverRoomWidget.show()

    def addLiverRoomList(self, roomDict):
        logging.debug("接收到新的主播列表")
        newID = []
        for roomID, topToken in roomDict.items():  # 如果id不在老列表里面 则添加
            if len(roomID) <= 4:  # 查询短号
                try:
                    r = requests.get('https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id=%s' % roomID)
                    data = json.loads(r.text)['data']
                    roomID = str(data['room_info']['room_id'])
                    # print(roomID)
                except:
                    logging.exception('房间号查询失败')
            if roomID not in self.roomIDDict:
                newID.append(roomID)
            else:
                for cover in self.coverList:
                    if cover.roomID == roomID:
                        cover.topToken = topToken
                        break
        for index, roomID in enumerate(newID):  # 添加id并创建新的预览图卡
            if roomID in roomDict:
                self.coverList.append(CoverLabel(roomID, roomDict[roomID]))
            else:
                self.coverList.append(CoverLabel(roomID, False))  # 添加短号的原长号
            self.coverList[-1].addToWindow.connect(self.addCoverToPlayer)  # 添加至播放窗口
            self.coverList[-1].deleteCover.connect(self.deleteCover)
            self.coverList[-1].changeTopToken.connect(self.changeTop)
            self.roomIDDict[str(roomID)] = False  # 添加普通卡片 字符串类型
        self.collectLiverInfo.setRoomIDList(list(map(int, self.roomIDDict.keys())))  # 更新需要刷新的房间列表
        self.collectLiverInfo.terminate()
        self.collectLiverInfo.wait()
        self.collectLiverInfo.start()
        self.dumpConfig.emit()  # 发送保存config信号
        self.refreshPanel()

    def refreshRoomPanel(self, liverInfo):  # 异步刷新图卡
        self.refreshCount += 1  # 刷新计数+1
        roomIDToRefresh = []
        roomIDStartLive = []
        firstRefresh = False
        for index, info in enumerate(liverInfo):
            if info[0]:  # uid有效
                for cover in self.coverList:
                    if cover.roomID == info[1]:  # 字符串房号
                        if cover.recordState == 2 and cover.liveState == 0 and info[4] == 1:  # 满足等待开播录制的3个条件
                            cover.recordThread.setSavePath(cover.savePath)  # 启动录制线程
                            cover.recordThread.start()
                            cover.recordThread.checkTimer.start(3000)
                            cover.recordState = 1  # 改为录制状态
                        elif cover.recordState == 1 and info[4] != 1:  # 满足停止录制的2个条件
                            cover.recordState = 0  # 取消录制
                            cover.recordThread.recordToken = False  # 设置录像线程标志位让它自行退出结束
                        cover.updateLabel(info)  # 更新数据
                if info[1] not in self.oldLiveStatus:  # 软件启动后第一次更新添加
                    self.oldLiveStatus[info[1]] = info[4]  # 房号: 直播状态
                    firstRefresh = True  # 第一次刷新
                elif self.oldLiveStatus[info[1]] != info[4]:  # 状态发生变化
                    if info[4] == 1:
                        roomIDStartLive.append(info[2])  # 添加开播主播名字
                    roomIDToRefresh.append(info[1])  # 发送给主界面要刷新的房间号
                    self.oldLiveStatus[info[1]] = info[4]  # 更新旧的直播状态列表
            else:  # 错误的房号
                for cover in self.coverList:
                    if cover.roomID == info[1]:
                        cover.updateLabel(info)
        if roomIDStartLive:
            self.startLiveList.emit(roomIDStartLive)  # 发送开播列表
        # if roomIDToRefresh:
        #     self.refreshIDList.emit(roomIDToRefresh)
        #     self.refreshPanel()  # 修改刷新策略 只有当有主播直播状态发生变化后才会刷新 降低闪退风险
        # elif firstRefresh:
        #     self.refreshPanel()
        # elif not self.refreshCount % 3:  # 每20s x 3 = 1分钟强制刷新一次
        #     self.refreshPanel()
        self.refreshPanel()

    def addCoverToPlayer(self, info):
        self.addToWindow.emit(info)

    def deleteCover(self, roomID):
        del self.roomIDDict[roomID]  # 删除roomID
        self.collectLiverInfo.setRoomIDList(list(map(int, self.roomIDDict.keys())))  # 更新需要刷新的房间列表
        self.refreshPanel()
        self.dumpConfig.emit()  # 发送保存config信号

    def deleteAll(self):  # 清空卡片槽
        self.roomIDDict.clear()
        self.roomIDList = []
        for cover in self.coverList:
            cover.roomID = '0'
        self.refreshPanel()
        self.dumpConfig.emit()

    def changeTop(self, info):
        self.roomIDDict[int(info[0])] = info[1]  # 房号 置顶token
        self.refreshPanel()
        self.dumpConfig.emit()  # 发送保存config信号

    def updatePlayingStatus(self, playerList):
        for cover in self.coverList:
            if cover.roomID in playerList:
                cover.isPlaying = True
                cover.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:red;background-color:#5a636d}')
            else:
                cover.isPlaying = False
                if cover.topToken:
                    cover.setStyleSheet('#cover{border-width:3px;border-style:solid;border-color:#dfa616;background-color:#5a636d}')
                else:
                    cover.setStyleSheet('#cover{border-width:0px;background-color:#5a636d}')

    def refreshPanel(self):
        tmpList = []
        for topToken in [True, False]:
            for liveState in [1, 0, -1]:  # 按顺序添加正在直播的 没在直播的 还有错误的卡片
                for cover in self.coverList:
                    if cover.liveState == liveState and cover.topToken == topToken and cover.roomID != '0':  # 符合条件的卡片
                        tmpList.append(cover)
                    else:
                        cover.hide()
                        # self.layout.addWidget(cover)
        # for cover in self.coverList:
        #     cover.hide()
        #     if cover.liveState in [1, 0, -1] and cover.roomID != '0':
        #         cover.show()
        for cnt, cover in enumerate(tmpList):
            self.layout.addWidget(cover, cnt // self.multiple, cnt % self.multiple)
            cover.show()
        self.adjustSize()
