from Qt import QtWidgets, QtCore
from zoo.libs.pyqt import utils
from zoo.preferences.core import preference

THEMEPREF = preference.interface("core_interface")


class ShadowOverlay(QtWidgets.QMainWindow):
    def __init__(self, parent=None, flags=None, frameless=None):
        """

        :param parent:
        :type parent:
        :param flags:
        :type flags:
        :param frameless:
        :type frameless: zoo.libs.pyqt.widgets.framelesswindow.frameless.FramelessWindowBase
        """

        super(ShadowOverlay, self).__init__(parent=parent)
        # Magic property for the frameless window to parent to the maya window for macs
        self.setProperty("saveWindowPref", True)
        self.setWindowFlags(flags | QtCore.Qt.FramelessWindowHint)

        self.frameless = frameless

        self.mainWidget = QtWidgets.QWidget()
        self.windowLayout = QtWidgets.QHBoxLayout()

        self.setCentralWidget(self.mainWidget)
        self.mainWidget.setLayout(self.windowLayout)

        self.windowContents = QtWidgets.QFrame()

        self.windowLayout.addWidget(self.windowContents)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.windowLayout.setContentsMargins(15, 15, 15, 15)
        self.move(-9999, -9999)  # avoid initial flicker

        # This needs to be here so shadow shows properly
        self.styleOpaque = "background-color: #66000000"
        self.windowContents.setStyleSheet(self.styleOpaque)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.mainWidget.setAcceptDrops(False)

        self.setAcceptDrops(False)
        for c in utils.iterChildren(self.window()):
            if hasattr(c, "setAcceptDrops"):
                c.setAcceptDrops(False)
                c.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
                c.setFocusPolicy(QtCore.Qt.NoFocus)
        effect = QtWidgets.QGraphicsBlurEffect(self.windowContents)
        effect.setBlurRadius(10)
        effect.setBlurHints(QtWidgets.QGraphicsBlurEffect.PerformanceHint)
        self.windowContents.setGraphicsEffect(effect)


    def contentsGeometry(self):
        return self.windowContents.frameGeometry()

    def mousePressEvent(self, event):
        self.frameless.resizerOverlay.activateWindow()
        self.frameless.activateWindow()

    def setTransparency(self, transparency):
        if transparency:
            self.windowContents.setStyleSheet("background-color: #00000000")
        else:
            self.windowContents.setStyleSheet(self.styleOpaque)

    def dragEnterEvent(self, event):
        super(ShadowOverlay, self).dragEnterEvent(event)

        pass


