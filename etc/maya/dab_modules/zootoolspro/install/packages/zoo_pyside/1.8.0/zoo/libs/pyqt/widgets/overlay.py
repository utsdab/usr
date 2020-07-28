from zoo.libs.pyqt.widgets import dialog
from Qt import QtCore, QtWidgets


class OverlayWidget(dialog.Dialog):

    widgetMousePress = QtCore.Signal(object)
    widgetMouseMove = QtCore.Signal(object)
    widgetMouseRelease = QtCore.Signal(object)
    pressed = False
    overlayActiveKey = QtCore.Qt.AltModifier

    def __init__(self, parent):
        """ Invisible overlay widget to capture mouse events and other things

        Used for the Alt-Middle mouse move and alt mouse in the frameless window

        :param parent:
        """
        super(OverlayWidget, self).__init__(parent=parent, showOnInitialize=False)
        self.layout = QtWidgets.QVBoxLayout(self)

        self.initUi()
        self.setStyleSheet("background-color: transparent;")

    def initUi(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint)
        self.setMouseTracking(True)
        self.update()

    def setDebugMode(self, debug):
        """ Debug mode to show where the dialog window is. Turns the window a transparent red

        :param debug:
        :type debug: bool
        :return:
        :rtype:
        """
        if debug:
            self.setStyleSheet("background-color: #88ff0000;")
        else:
            self.setStyleSheet("background-color: transparent;")

    def update(self):
        """ Update geometry to match the parents geometry

        :return:
        """
        self.setGeometry(0, 0, self.parent().geometry().width(), self.parent().geometry().height())

    def mousePressEvent(self, event):
        """ Send events back down to parent

        :param event:
        :return:
        """

        if not QtWidgets.QApplication.keyboardModifiers() == self.overlayActiveKey:
            event.ignore()
            return

        self.widgetMousePress.emit(event)
        self.pressed = True
        self.update()

    def enterEvent(self, event):
        """ On mouse enter, check if it is pressed

        :param event:
        :return:
        """

        if not self.pressed:
            self.hide()

        event.ignore()

    def mouseMoveEvent(self, event):
        """ Send events back down to parent

        :param event:
        :return:
        """
        pass

    def keyReleaseEvent(self, event):
        self.hide()

    def mouseReleaseEvent(self, event):
        """ Send events back down to parent

        :param event:
        :return:
        """
        self.widgetMouseRelease.emit(event)
        self.pressed = False
        self.update()

    def show(self, *args, **kwargs):
        self.pressed = True
        super(OverlayWidget, self).show(*args, **kwargs)
        self.update()

