'''
将弹幕机分离出来单独开发
'''
from PyQt5.QtWidgets import * 	# QAction,QFileDialog
from PyQt5.QtGui import *		# QIcon,QPixmap
from PyQt5.QtCore import * 		# QSize


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


class Bar(QLabel):
    moveSignal = pyqtSignal(QPoint)

    def __init__(self, text):
        super(Bar, self).__init__()
        self.setText(text)
        self.setFixedHeight(25)

    def mousePressEvent(self, event):
        self.startPos = event.pos()

    def mouseMoveEvent(self, event):
        self.moveSignal.emit(self.mapToParent(event.pos() - self.startPos))


class ToolButton(QToolButton):
    def __init__(self, icon):
        super(ToolButton, self).__init__()
        self.setStyleSheet('border-color:#CCCCCC')
        self.setFixedSize(25, 25)
        self.setIcon(icon)


class TextOpation(QWidget):
    def __init__(self, setting=[50, 1, 7, 0, '【 [ {', 10]):
        super(TextOpation, self).__init__()
        self.resize(300, 300)
        self.setWindowTitle('弹幕窗设置')
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('字体大小'), 0, 0, 1, 1)
        self.fontSizeCombox = QComboBox()
        self.fontSizeCombox.addItems([str(i) for i in range(5, 26)])
        self.fontSizeCombox.setCurrentIndex(setting[5])
        layout.addWidget(self.fontSizeCombox, 0, 1, 1, 1)
        layout.addWidget(QLabel('窗体透明度'), 1, 0, 1, 1)
        self.opacitySlider = Slider()
        self.opacitySlider.setValue(setting[0])
        layout.addWidget(self.opacitySlider, 1, 1, 1, 1)
        layout.addWidget(QLabel('窗体横向占比'), 2, 0, 1, 1)
        self.horizontalCombobox = QComboBox()
        self.horizontalCombobox.addItems(['%d' % x + '%' for x in range(10, 110, 10)])
        self.horizontalCombobox.setCurrentIndex(setting[1])
        layout.addWidget(self.horizontalCombobox, 2, 1, 1, 1)
        layout.addWidget(QLabel('窗体纵向占比'), 3, 0, 1, 1)
        self.verticalCombobox = QComboBox()
        self.verticalCombobox.addItems(['%d' % x + '%' for x in range(10, 110, 10)])
        self.verticalCombobox.setCurrentIndex(setting[2])
        layout.addWidget(self.verticalCombobox, 3, 1, 1, 1)
        layout.addWidget(QLabel('弹幕窗类型'), 4, 0, 1, 1)
        self.translateCombobox = QComboBox()
        self.translateCombobox.addItems(['弹幕和同传', '只显示弹幕', '只显示同传'])
        self.translateCombobox.setCurrentIndex(setting[3])
        layout.addWidget(self.translateCombobox, 4, 1, 1, 1)
        layout.addWidget(QLabel('同传过滤字符 (空格隔开)'), 5, 0, 1, 1)
        self.translateFitler = QLineEdit('')
        self.translateFitler.setText(setting[4])
        self.translateFitler.setFixedWidth(100)
        layout.addWidget(self.translateFitler, 5, 1, 1, 1)


class TextBrowser(QWidget):
    closeSignal = pyqtSignal()
    moveSignal = pyqtSignal(QPoint)

    def __init__(self, parent):
        super(TextBrowser, self).__init__(parent)
        self.optionWidget = TextOpation()
        self.setWindowTitle('弹幕机')

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.bar = Bar(' 弹幕机')
        self.bar.setStyleSheet('background:#AAAAAAAA')
        self.bar.moveSignal.connect(self.moveWindow)
        layout.addWidget(self.bar, 0, 0, 1, 10)

        self.optionButton = ToolButton(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.optionButton.clicked.connect(self.optionWidget.show)  # 弹出设置菜单
        layout.addWidget(self.optionButton, 0, 8, 1, 1)

        self.closeButton = ToolButton(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.closeButton.clicked.connect(self.userClose)
        layout.addWidget(self.closeButton, 0, 9, 1, 1)

        self.textBrowser = QTextBrowser()
        self.textBrowser.setFont(QFont('Microsoft JhengHei', 16, QFont.Bold))
        self.textBrowser.setStyleSheet('border-width:1')
        # textCursor = self.textBrowser.textCursor()
        # textBlockFormat = QTextBlockFormat()
        # textBlockFormat.setLineHeight(17, QTextBlockFormat.FixedHeight)  # 弹幕框行距
        # textCursor.setBlockFormat(textBlockFormat)
        # self.textBrowser.setTextCursor(textCursor)
        layout.addWidget(self.textBrowser, 1, 0, 1, 10)

        self.transBrowser = QTextBrowser()
        self.transBrowser.setFont(QFont('Microsoft JhengHei', 16, QFont.Bold))
        self.transBrowser.setStyleSheet('border-width:1')
        layout.addWidget(self.transBrowser, 2, 0, 1, 10)

    def userClose(self):
        self.hide()
        self.closeSignal.emit()

    def moveWindow(self, moveDelta):
        self.moveSignal.emit(self.pos() + moveDelta)
