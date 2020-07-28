from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import overlay
from zoo.libs.utils import zlogging, env

resizerAlpha = 1
logger = zlogging.getLogger(__name__)


class ResizeDirection:
    """ Flag attributes to tell the what position the resizer is """
    Left = 1
    Top = 2
    Right = 4
    Bottom = 8


class FramelessResizerWindow(QtWidgets.QMainWindow):

    resizeFinished = QtCore.Signal()

    def __init__(self, parent=None, target=None, flags=None, frameless=None):
        """ The main resizer window that holds the resizers

        :param parent:
        :type parent:
        :param target:
        :type target:
        :param flags:
        :type flags:
        :param frameless:
        :type frameless: zoo.libs.pyqt.widgets.framelesswindow.frameless.FramelessWindowBase
        """



        super(FramelessResizerWindow, self).__init__(parent)

        self.topResize = VerticalResize(parent=self, direction=ResizeDirection.Top, frameless=frameless)
        self.botResize = VerticalResize(parent=self, direction=ResizeDirection.Bottom, frameless=frameless)
        self.rightResize = HorizontalResize(parent=self, direction=ResizeDirection.Right, frameless=frameless)
        self.leftResize = HorizontalResize(parent=self, direction=ResizeDirection.Left, frameless=frameless)
        self.topLeftResize = CornerResize(parent=self, direction=ResizeDirection.Left | ResizeDirection.Top, frameless=frameless)
        self.topRightResize = CornerResize(parent=self, direction=ResizeDirection.Right | ResizeDirection.Top, frameless=frameless)
        self.botLeftResize = CornerResize(parent=self, direction=ResizeDirection.Left | ResizeDirection.Bottom, frameless=frameless)
        self.botRightResize = CornerResize(parent=self, direction=ResizeDirection.Right | ResizeDirection.Bottom, frameless=frameless)

        self.resizers = [self.topResize, self.topRightResize, self.rightResize,
                         self.botRightResize, self.botResize, self.botLeftResize,
                         self.leftResize, self.topLeftResize]
        self.frameless = frameless
        # Magic property for the frameless window to parent to the maya window for macs
        self.setProperty("saveWindowPref", True)
        self.resizeFrameless = True
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.frameless.window().windowFlags())
        self.setAcceptDrops(False)
        self.mainWidget = QtWidgets.QWidget()
        # self.setCentralWidget(btn)
        self.windowLayout = QtWidgets.QGridLayout()
        # self.setDebugMode(True)

        for r in self.resizers:
            r.setParent(target)
            r.windowResizeStartEvent.connect(self.resizeStart)
            r.windowResizedFinished.connect(self.resizeFinishedEvent)

        self.setCentralWidget(self.mainWidget)
        self.mainWidget.setLayout(self.windowLayout)
        self.windowContents = ResizerCenter(frameless=frameless)
        self.windowLayout.addWidget(self.topLeftResize, 0, 0, 1, 1)
        self.windowLayout.addWidget(self.topResize, 0, 1, 1, 1)
        self.windowLayout.addWidget(self.windowContents, 1, 1, 1, 1)
        self.windowLayout.addWidget(self.topRightResize, 0, 2, 1, 1)

        self.windowLayout.addWidget(self.leftResize, 1, 0, 1, 1)
        self.windowLayout.addWidget(self.rightResize, 1, 2, 1, 1)

        self.windowLayout.addWidget(self.botLeftResize, 2, 0, 1, 1)
        self.windowLayout.addWidget(self.botResize, 2, 1, 1, 1)
        self.windowLayout.addWidget(self.botRightResize, 2, 2, 1, 1)
        self.windowLayout.setContentsMargins(4,4,6,5)
        self.windowLayout.setHorizontalSpacing(0)
        self.windowLayout.setVerticalSpacing(0)

    def setDebugMode(self, debug):
        if debug:
            self.setStyleSheet("background-color: #22ff0000")

            for r in self.resizers:
                r.setStyleSheet("background-color: #22ff0000")
        else:
            self.setStyleSheet("")

    def resizeStart(self):
        pass

    def resizeFinishedEvent(self):
        self.resizeFrameless = False
        self.resizeFinished.emit()
        self.resizeFrameless = True

    def mouseReleaseEvent(self, event):
        self.frameless.show()
        self.frameless.window().activateWindow()

    def resizeEvent(self, event):
        # maybe should be put into frameless window instead
        pass
        # if self.isVisible() and self.resizeFrameless:
        #     xOffset = 0
        #     yOffset = 0
        #     xSizeOffset = 0
        #     ySizeOffset = 0
        #     if self.frameless.undocked:
        #         yOffset += 1
        #
        #         if env.isMac():
        #             yOffset -= 1
        #
        #     if env.isMac():
        #         xOffset -= 1
        #
        #     rect = QtCore.QRect(self.window().frameGeometry())
        #     rect.setWidth(rect.width() - 30 + xSizeOffset)
        #     rect.setHeight(rect.height() - 30 + ySizeOffset)
        #     rect.translate(14 + xOffset, 14 + yOffset)
        #     self.frameless.setGeometry(rect)


class ResizerCenter(QtWidgets.QFrame):
    def __init__(self, frameless=None):
        super(ResizerCenter, self).__init__()
        self.frameless = frameless

    def enterEvent(self, event):
        self.frameless.show()


class WindowResizer(QtWidgets.QFrame):
    """
    The resize widgets for the sides of the windows and the corners to resize the parent window.

    """
    windowResized = QtCore.Signal()
    windowResizeStartEvent = QtCore.Signal()
    windowResizedFinished = QtCore.Signal()

    def __init__(self, parent, direction=None, otherWindows=None, frameless=None):
        """

        :param parent:
        :type parent:  FramelessResizerWindow
        :param direction:
        :type direction:
        :param otherWindows:
        :type otherWindows:
        """
        super(WindowResizer, self).__init__(parent=parent)
        self.initUi()
        self.direction = 0  # ResizeDirection
        self.widgetMousePos = None  # QtCore.QPoint
        self.widgetGeometry = None  # type: QtCore.QRect
        self.resizerMain = parent
        self.setStyleSheet("background-color: transparent;")
        self.frameless = frameless
        self.setResizeDirection(direction)
        self.otherWindows = otherWindows or []

        self.windowResizeStartEvent.connect(self.windowResizeStart)

    def initUi(self):
        self.windowResized.connect(self.windowResizeEvent)

    def paintEvent(self, event):
        """ Mouse events seem to deactivate when its completely transparent. Hacky way to avoid that for now.

        :type event: :class:`QtCore.QEvent`
        """

        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, resizerAlpha))
        painter.end()

    def windowResizeStart(self):
        self.widgetMousePos = self.mapFromGlobal(QtGui.QCursor.pos())
        self.widgetGeometry = self.window().frameGeometry()


    def mousePressEvent(self, event):
        self.windowResizeStartEvent.emit()

    def mouseMoveEvent(self, event):
        self.windowResized.emit()

    def setParent(self, parent):
        """Set the parent and the window

        :param parent:
        :type parent: FramelessResizerWindow

        """
        super(WindowResizer, self).setParent(parent)

    def windowResizeEvent(self):
        """ Resize based on the mouse position and the current direction
        """
        self.resizeWidget(widget=self.window())
        for w in self.otherWindows:
            self.resizeWidget(w)

    def resizeWidget(self, widget):
        pos = QtGui.QCursor.pos()
        newGeometry = widget.frameGeometry()

        # Minimum Size
        mW = widget.minimumSize().width()
        mH = widget.minimumSize().height()

        # Check to see if the ResizeDirection flag is in self.direction
        if self.direction & ResizeDirection.Left == ResizeDirection.Left:
            left = newGeometry.left()
            newGeometry.setLeft(pos.x() - self.widgetMousePos.x())
            if newGeometry.width() <= mW:  # Revert back if too small
                newGeometry.setLeft(left)
        if self.direction & ResizeDirection.Top == ResizeDirection.Top:
            top = newGeometry.top()
            newGeometry.setTop(pos.y() - self.widgetMousePos.y())
            if newGeometry.height() <= mH:  # Revert back if too small
                newGeometry.setTop(top)
        if self.direction & ResizeDirection.Right == ResizeDirection.Right:
            newGeometry.setRight(pos.x() + (self.minimumSize().width() - self.widgetMousePos.x()))
        if self.direction & ResizeDirection.Bottom == ResizeDirection.Bottom:
            newGeometry.setBottom(pos.y() + (self.minimumSize().height() - self.widgetMousePos.y()))

        # Set new sizes
        x = newGeometry.x()
        y = newGeometry.y()
        w = max(newGeometry.width(), mW)  # Minimum Width
        h = max(newGeometry.height(), mH)  # Minimum height
        widget.setGeometry(x, y, w, h)
        #self.framelessResize()



    def enterEvent(self, event):
        if env.isMac():
            self.resizerMain.show()
            self.resizerMain.activateWindow()

    def leaveEvent(self, event):
        """ Turn the mouse back to original

        :type event: :class:`QtCore.QEvent`
        """
        for i in range(3):
            QtWidgets.QApplication.restoreOverrideCursor()


    def framelessResize(self):
        if self.resizerMain.isVisible() and self.resizerMain.resizeFrameless:
            xOffset = 0
            yOffset = 0
            xSizeOffset = 0
            ySizeOffset = 0
            if self.frameless.undocked:
                yOffset += 1

                if env.isMac():
                    yOffset -= 1

            if env.isMac():
                xOffset -= 1

            rect = QtCore.QRect(self.window().frameGeometry())
            rect.setWidth(rect.width() - 30 + xSizeOffset)
            rect.setHeight(rect.height() - 30 + ySizeOffset)
            rect.translate(14+xOffset, 14+yOffset)
            self.frameless.setGeometry(rect)

    def setResizeDirection(self, direction):
        """Set the resize direction. Expects an int from ResizeDirection

        .. code-block:: python

            setResizeDirection(ResizeDirection.Left | ResizeDirection.Top)

        :param direction: ResizeDirection
        :type direction: int
        """
        self.direction = direction

    def mouseReleaseEvent(self, event):
        self.windowResizedFinished.emit()


class CornerResize(WindowResizer):
    """ Resizers in the corner of the window

    """

    def __init__(self, parent=None, direction=None, otherWindows=None, frameless=None):
        super(CornerResize, self).__init__(parent=parent, direction=direction, otherWindows=otherWindows, frameless=frameless)

    def initUi(self):
        super(CornerResize, self).initUi()
        self.setFixedSize(utils.sizeByDpi(QtCore.QSize(10, 10)))

    def enterEvent(self, event):
        """ Set cursor based on corner hovered

        :type event: :class:`QtCore.QEvent`
        """
        super(CornerResize, self).enterEvent(event)
        # Top Left or Bottom Right
        if self.direction == ResizeDirection.Left | ResizeDirection.Top or \
                self.direction == ResizeDirection.Right | ResizeDirection.Bottom:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeFDiagCursor)

            # Top Right or Bottom Left
        elif self.direction == ResizeDirection.Right | ResizeDirection.Top or \
                self.direction == ResizeDirection.Left | ResizeDirection.Bottom:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeBDiagCursor)



class VerticalResize(WindowResizer):
    """ Resizers for the top and bottom of the window

    """

    def __init__(self, parent=None, direction=None, otherWindows=None, frameless=None):
        super(VerticalResize, self).__init__(parent=parent, direction=direction, otherWindows=otherWindows, frameless=frameless)

    def initUi(self):
        super(VerticalResize, self).initUi()
        self.setFixedHeight(utils.dpiScale(8))

    def enterEvent(self, event):
        """Change cursor on hover

        :type event: :class:`QtCore.QEvent`
        """
        super(VerticalResize, self).enterEvent(event)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeVerCursor)


class HorizontalResize(WindowResizer):
    """ Resizers for the left and right of the window

    """

    def __init__(self, parent=None, direction=None, otherWindows=None, frameless=None):
        super(HorizontalResize, self).__init__(parent=parent, direction=direction, otherWindows=otherWindows, frameless=frameless)

    def initUi(self):
        super(HorizontalResize, self).initUi()
        self.setFixedWidth(utils.dpiScale(8))

    def enterEvent(self, event):
        """Change cursor on hover

        :type event: :class:`QtCore.QEvent`
        """
        super(HorizontalResize, self).enterEvent(event)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeHorCursor)

    def mouseReleaseEvent(self, event):
        print("release event")



class FramelessOverlay(overlay.OverlayWidget):

    def __init__(self, parent, titleBar, topLeft=None, topRight=None,
                 botLeft=None, botRight=None):
        """ Handles linux like window movement.

        Eg Alt-Middle click to move entire window
        Alt Left Click corner to resize

        :param topLeft:
        :param topRight:
        :param botLeft:
        :param botRight:
        :param parent:
        :param titleBar:
        """
        super(FramelessOverlay, self).__init__(parent=parent)
        self.titleBar = titleBar

        self.topLeft = topLeft  # type: CornerResize
        self.topRight = topRight  # type: CornerResize
        self.botLeft = botLeft  # type: CornerResize
        self.botRight = botRight  # type: CornerResize
        self.resizeDir = 0

    def mousePressEvent(self, event):
        """ Alt-Middle click to move window

        :param event:
        :return:
        """
        if not self.isEnabled():
            event.ignore()
            super(FramelessOverlay, self).mousePressEvent(event)
            return

        if event.modifiers() == QtCore.Qt.AltModifier and event.buttons() & QtCore.Qt.MiddleButton:
            self.titleBar.startMove()

        if event.modifiers() == QtCore.Qt.AltModifier and event.buttons() & QtCore.Qt.LeftButton:
            self.resizeDir = self.quadrant()

            if self.resizeDir == ResizeDirection.Top | ResizeDirection.Right:
                self.topRight.windowResizeStart()
            elif self.resizeDir == ResizeDirection.Top | ResizeDirection.Left:
                self.topLeft.windowResizeStart()
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Left:
                self.botLeft.windowResizeStart()
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Right:
                self.botRight.windowResizeStart()

        if (event.modifiers() != QtCore.Qt.AltModifier and event.buttons() & QtCore.Qt.MiddleButton) or \
                (event.modifiers() != QtCore.Qt.AltModifier and event.buttons() & QtCore.Qt.LeftButton):
            self.hide()

        event.ignore()
        super(FramelessOverlay, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):

        if not self.isEnabled():
            event.ignore()
            super(FramelessOverlay, self).mouseReleaseEvent(event)
            return

        self.titleBar.endMove()
        self.topLeft.windowResizedFinished.emit()
        self.topRight.windowResizedFinished.emit()
        self.botLeft.windowResizedFinished.emit()
        self.botRight.windowResizedFinished.emit()
        self.resizeDir = 0
        event.ignore()
        super(FramelessOverlay, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            super(FramelessOverlay, self).mouseMoveEvent(event)
            return

        self.titleBar.mouseMoveEvent(event)

        if self.resizeDir is not 0:
            if self.resizeDir == ResizeDirection.Top | ResizeDirection.Right:
                self.topRight.windowResized.emit()
            elif self.resizeDir == ResizeDirection.Top | ResizeDirection.Left:
                self.topLeft.windowResized.emit()
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Left:
                self.botLeft.windowResized.emit()
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Right:
                self.botRight.windowResized.emit()

        event.ignore()

        super(FramelessOverlay, self).mouseMoveEvent(event)

    def quadrant(self):
        """ Get the quadrant of where the mouse is pointed, and return the direction

        :return: The direction ResizeDirection
        :rtype: ResizeDirection
        """
        midX = self.geometry().width()/2
        midY = self.geometry().height()/2
        ret = 0

        pos = self.mapFromGlobal(QtGui.QCursor.pos())

        if pos.x() < midX:
            ret = ret | ResizeDirection.Left
        elif pos.x() > midX:
            ret = ret | ResizeDirection.Right

        if pos.y() < midY:
            ret = ret | ResizeDirection.Top
        elif pos.y() > midY:
            ret = ret | ResizeDirection.Bottom

        return ret

    def show(self):
        if self.isEnabled():
            super(FramelessOverlay, self).show()
        else:
            logger.warning("FramelessOverlay.show() was called when it is disabled")

    def setEnabled(self, enabled):
        self.setDebugMode(not enabled)
        self.setVisible(enabled)
        super(FramelessOverlay, self).setEnabled(enabled)
