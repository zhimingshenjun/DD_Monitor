from PyQt5.Qt import *


class Label(QLabel):
    def __init__(self, text):
        super(Label, self).__init__()
        self.setText(text)
        self.setFont(QFont('微软雅黑', 13, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('background-color:#4682B4')


class LayoutWidget(QLabel):
    clicked = pyqtSignal(int)

    def __init__(self, layout, number):
        super(LayoutWidget, self).__init__()
        self.number = number
        mainLayout = QGridLayout(self)
        for index, rect in enumerate(layout):
            y, x, h, w = rect
            mainLayout.addWidget(Label(str(index + 1)), y, x, h, w)

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit(self.number)

    def enterEvent(self, QEvent):
        self.setStyleSheet('background-color:#AFEEEE')

    def leaveEvent(self, QEvent):
        self.setStyleSheet('background-color:#00000000')


class LayoutSettingPanel(QWidget):
    layoutConfig = pyqtSignal(list)

    def __init__(self):
        super(LayoutSettingPanel, self).__init__()
        self.resize(1280, 720)
        self.setWindowTitle('选择布局方式')
        mainLayout = QGridLayout(self)
        mainLayout.setSpacing(15)
        mainLayout.setContentsMargins(15, 15, 15, 15)
        self.layoutList = [
            [(0, 0, 1, 1)], [(0, 0, 1, 1), (0, 1, 1, 1)], [(0, 0, 1, 1), (1, 0, 1, 1), (2, 0, 1, 1)],
            [(0, 0, 1, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)],
            [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1)],
            [(0, 0, 2, 2), (0, 2, 1, 1), (1, 2, 1, 1), (2, 0, 1, 1), (2, 1, 1, 1), (2, 2, 1, 1)],
            [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1), (0, 3, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1), (1, 3, 1, 1)],
            [(0, 0, 3, 3), (0, 3, 1, 1), (1, 3, 1, 1), (2, 3, 1, 1), (3, 0, 1, 1), (3, 1, 1, 1), (3, 2, 1, 1), (3, 3, 1, 1)],
            [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1), (2, 0, 1, 1), (2, 1, 1, 1), (2, 2, 1, 1)]
        ]
        layoutWidgetList = []
        for index, layout in enumerate(self.layoutList):
            widget = LayoutWidget(layout, index)
            widget.clicked.connect(self.sendLayout)
            mainLayout.addWidget(widget, index // 3, index % 3)
            layoutWidgetList.append(widget)

    def sendLayout(self, number):
        self.layoutConfig.emit(self.layoutList[number])
        self.hide()