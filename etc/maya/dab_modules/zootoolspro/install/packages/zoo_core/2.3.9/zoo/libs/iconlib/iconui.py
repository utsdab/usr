import random

from Qt import QtWidgets, QtCore

from . import iconlib
from zoo.libs.pyqt.widgets import dialog, flowlayout


class IconUI(dialog.Dialog):
    def __init__(self, title="", width=600, height=800, icon="", parent=None, showOnInitialize=True):
        super(IconUI, self).__init__(title, width, height, icon, parent, showOnInitialize)
        self.icons = []
        self.initUI()

    def initUI(self):
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.scrollArea = QtWidgets.QScrollArea(parent=self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollLayout = flowlayout.FlowLayout()

        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea.setWidget(self.scrollWidget)
        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)
        for i in iconlib.Icon.iconCollection:
            colorRandom = (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))
            btn = QtWidgets.QToolButton(parent=self)
            icon = iconlib.Icon.iconColorized(i, size=256, color=colorRandom)
            btn.setIcon(icon)
            btn.setText(i)
            btn.clicked.connect(self.copyNameToClipboard)
            self.scrollLayout.addWidget(btn)

    def copyNameToClipboard(self):
        text = self.sender().text()
        app = QtCore.QCoreApplication.instance()
        app.clipboard().setText(text)
