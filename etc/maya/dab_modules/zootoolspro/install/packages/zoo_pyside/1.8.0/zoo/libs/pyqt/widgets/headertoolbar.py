from Qt import QtWidgets, QtCore
from zoo.libs import iconlib


class HeaderToolbar(QtWidgets.QToolBar):
    """Header tool bar for a window, comes prebuilt with a label, minimize,maximize and close buttons, parent
    must implement showMinimized, toggleMaximized, close
    """
    def __init__(self, name, title, parent=None):
        super(HeaderToolbar, self).__init__(parent)
        self.setObjectName(name)
        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.setMovable(False)
        self.isFloatable = False
        self.spacer = QtWidgets.QWidget()
        self.spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.minimizeBtn = QtWidgets.QToolButton(self)
        self.minimizeBtn.setText("-")
        self.minimizeBtn.clicked.connect(self.parent().showMinimized)
        self.minimizeBtn.setMaximumWidth(20)
        self.minimizeBtn.setMaximumHeight(20)

        self.maximizeBtn = QtWidgets.QToolButton(self)
        self.maximizeBtn.setText('+')
        self.maximizeBtn.clicked.connect(self.parent().toggleMaximized)
        self.maximizeBtn.setMaximumWidth(20)
        self.maximizeBtn.setMaximumHeight(20)

        self.closeBtn = QtWidgets.QToolButton(self)
        self.closeBtn.setText('X')
        self.closeBtn.clicked.connect(self.parent().close)
        self.closeBtn.setMaximumWidth(20)
        self.closeBtn.setMaximumHeight(20)

        self.addWidget(self.spacer)
        self.addWidget(self.minimizeBtn)
        self.addWidget(self.maximizeBtn)
        self.addWidget(self.closeBtn)

        self.minimizeBtn.setIcon(iconlib.icon("minusHollow"))
        self.minimizeBtn.setIcon(iconlib.icon("window"))
        self.minimizeBtn.setIcon(iconlib.icon("close"))
