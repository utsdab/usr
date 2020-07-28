from Qt import QtWidgets, QtCore, QtGui
from zoo.libs import iconlib


class Dialog(QtWidgets.QDialog):
    def __init__(self, title="", width=600, height=800, icon="",
                 parent=None, showOnInitialize=True, transparent=False):
        super(Dialog, self).__init__(parent=parent)

        if transparent:
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # self.setStyleSheet(qdarkstyle.load_stylesheet(pyside=True))
        self.setContentsMargins(2, 2, 2, 2)
        self.title = title
        self.setObjectName(title)
        self.setWindowTitle(title)
        self.resize(width, height)

        if icon:
            if isinstance(icon, QtGui.QIcon):
                self.setWindowIcon(icon)
            else:
                self.setWindowIcon(iconlib.icon(icon))

        if showOnInitialize:
            self.center()
            self.show()
        self.resize(width, height)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def toggleMaximized(self):
        """Toggles the maximized window state
        """
        if self.windowState() and QtCore.Qt.WindowMaximized:
            self.showNormal()
        else:
            self.showMaximized()
