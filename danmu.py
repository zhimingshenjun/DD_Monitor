'''
将弹幕机分离出来单独开发
'''
from PyQt5.Qt import *


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
    def __init__(self, setting=[20, 2, 6, 0, '【 [ {']):
        super(TextOpation, self).__init__()
        self.resize(300, 300)
        self.setWindowTitle('弹幕窗设置')
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        layout = QGridLayout(self)
        layout.addWidget(QLabel('窗体颜色浓度'), 0, 0, 1, 1)
        self.opacitySlider = Slider()
        self.opacitySlider.setValue(setting[0])
        layout.addWidget(self.opacitySlider, 0, 1, 1, 1)
        layout.addWidget(QLabel('窗体横向占比'), 1, 0, 1, 1)
        self.horizontalCombobox = QComboBox()
        self.horizontalCombobox.addItems(['10%', '15%', '20%', '25%', '30%', '35%', '40%', '45%', '50%'])
        self.horizontalCombobox.setCurrentIndex(setting[1])
        layout.addWidget(self.horizontalCombobox, 1, 1, 1, 1)
        layout.addWidget(QLabel('窗体纵向占比'), 2, 0, 1, 1)
        self.verticalCombobox = QComboBox()
        self.verticalCombobox.addItems(['50%', '55%', '60%', '65%', '70%', '75%', '80%', '85%', '90%', '95%', '100%'])
        self.verticalCombobox.setCurrentIndex(setting[2])
        layout.addWidget(self.verticalCombobox, 2, 1, 1, 1)
        layout.addWidget(QLabel('单独同传窗口'), 3, 0, 1, 1)
        self.translateCombobox = QComboBox()
        self.translateCombobox.addItems(['开启', '关闭'])
        self.translateCombobox.setCurrentIndex(setting[3])
        layout.addWidget(self.translateCombobox, 3, 1, 1, 1)
        layout.addWidget(QLabel('同传过滤字符 (空格隔开)'), 4, 0, 1, 1)
        self.translateFitler = QLineEdit('')
        self.translateFitler.setText(setting[4])
        self.translateFitler.setFixedWidth(100)
        layout.addWidget(self.translateFitler, 4, 1, 1, 1)


class TextBrowser(QWidget):
    closeSignal = pyqtSignal()
    moveSignal = pyqtSignal(QPoint)

    def __init__(self, parent):
        super(TextBrowser, self).__init__(parent)
        self.optionWidget = TextOpation()

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
        # newPos = self.pos() + moveDelta
        # x, y = newPos.x(), newPos.y()
        # rightBorder = self.parent().width() - self.width()
        # bottomBoder = self.parent().height() - self.height()
        # if x < 0:
        #     x = 0
        # elif x > rightBorder:
        #     x = rightBorder
        # if y < 30:
        #     y = 30
        # elif y > bottomBoder:
        #     y = bottomBoder
        # self.move(x, y)