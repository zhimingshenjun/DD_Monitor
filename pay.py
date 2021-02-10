"""
赞助页弹窗
"""
import requests
from PyQt5.QtWidgets import * 	# QAction,QFileDialog
from PyQt5.QtGui import *		# QIcon,QPixmap
from PyQt5.QtCore import * 		# QSize


class DownloadImage(QThread):
    """下载图片 - 二维码"""
    img = pyqtSignal(QPixmap)

    def __init__(self):
        super(DownloadImage, self).__init__()

    def run(self):
        try:
            r = requests.get(r'http://i0.hdslb.com/bfs/album/a4d2644425634cb8568570b77f4ba45f2b84fe67.png')
            img = QPixmap.fromImage(QImage.fromData(r.content))
            self.img.emit(img)
        except Exception as e:
            print(str(e))


class thankToBoss(QThread):
    """获取感谢名单"""
    bossList = pyqtSignal(list)

    def __init__(self, parent=None):
        super(thankToBoss, self).__init__(parent)

    def run(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'}
        response = requests.get(r'https://github.com/jiafangjun/DD_KaoRou2/blob/master/感谢石油王.csv', headers=headers)
        bossList = []
        html = response.text.split('\n')
        for cnt, line in enumerate(html):
            if 'RMB<' in line:
                boss = html[cnt - 1].split('>')[1].split('<')[0]
                rmb = line.split('>')[1].split('<')[0]
                bossList.append([boss, rmb])
        if bossList:
            self.bossList.emit(bossList)
        else:
            self.bossList.emit([['名单列表获取失败', '']])


class pay(QDialog):
    """投喂弹窗"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('赞助和支持')
        self.resize(564, 500)
        layout = QGridLayout()
        self.setLayout(layout)
        txt = u'DD监控室由B站up：神君Channel 业余时间独立开发制作。\n\
\n所有功能全部永久免费给广大DD使用\n\
\n有独立经济来源的老板们如觉得监控室好用的话，不妨小小支持亿下\n\
\n一元也是对我继续更新监控室的莫大鼓励。十分感谢！\n'
        label = QLabel(txt)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label, 0, 0, 1, 2)

        self.QR = QLabel()
        layout.addWidget(self.QR, 1, 0, 1, 1)

        self.bossTable = QTableWidget()
        self.bossTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bossTable.setRowCount(3)
        self.bossTable.setColumnCount(2)
        for i in range(2):
            self.bossTable.setColumnWidth(i, 105)
        self.bossTable.setHorizontalHeaderLabels(['石油王', '投喂了'])
        self.bossTable.setItem(0, 0, QTableWidgetItem('石油王鸣谢名单'))
        self.bossTable.setItem(0, 1, QTableWidgetItem('正在获取...'))
        layout.addWidget(self.bossTable, 1, 1, 1, 1)

        self.getQR = DownloadImage()
        self.getQR.img.connect(self.updateQR)
        self.getQR.start()

        self.thankToBoss = thankToBoss()
        self.thankToBoss.bossList.connect(self.updateBossList)
        # self.thankToBoss.start()

    def updateQR(self, img):
        self.QR.setPixmap(img)

    def updateBossList(self, bossList):
        self.bossTable.clear()
        self.bossTable.setColumnCount(2)
        self.bossTable.setRowCount(len(bossList))
        if len(bossList) > 3:
            biggestBossList = []
            for _ in range(3):
                sc = 0
                for cnt, i in enumerate(bossList):
                    money = float(i[1].split(' ')[0])
                    if money > sc:
                        sc = money
                        bossNum = cnt
                biggestBossList.append(bossList.pop(bossNum))
            for y, i in enumerate(biggestBossList):
                self.bossTable.setItem(y, 0, QTableWidgetItem(i[0]))
                self.bossTable.setItem(y, 1, QTableWidgetItem(i[1]))
                self.bossTable.item(y, 0).setTextAlignment(Qt.AlignCenter)
                self.bossTable.item(y, 1).setTextAlignment(Qt.AlignCenter)
            for y, i in enumerate(bossList):
                self.bossTable.setItem(y + 3, 0, QTableWidgetItem(i[0]))
                self.bossTable.setItem(y + 3, 1, QTableWidgetItem(i[1]))
                self.bossTable.item(y + 3, 0).setTextAlignment(Qt.AlignCenter)
                self.bossTable.item(y + 3, 1).setTextAlignment(Qt.AlignCenter)
            self.bossTable.setHorizontalHeaderLabels(['石油王', '投喂了'])
