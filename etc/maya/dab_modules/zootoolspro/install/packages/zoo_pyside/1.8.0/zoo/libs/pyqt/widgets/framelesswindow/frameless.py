from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import layouts, overlay
from zoo.libs.pyqt.widgets.framelesswindow.framelesswidgets import ShadowOverlay
from zoo.libs.pyqt.widgets.framelesswindow.titlebar import TitleBar, FramelessWindowContents, FramelessTitleLabel
from zoo.libs.pyqt.widgets.framelesswindow.resizers import ResizeDirection, FramelessResizerWindow
from zoo.libs.utils import zlogging, env
from zoo.preferences.core import preference

logger = zlogging.getLogger(__name__)

from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.maya.qt import mayaMixin


inMaya = env.isInMaya()



class FramelessWindowBase(QtWidgets.QMainWindow):
    _initWidth = None
    _initHeight = None
    _minimizedWidth = 390
    _minimized = False
    _prevDock = None
    savedSize = None

    dockChanged = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        """ Frameless Window base

        Window starts off hidden so make sure to show.

        :param parent:
        :type parent:
        :param resizable:
        :type resizable:
        :param width:
        :type width:
        :param height:
        :type height:

        """
        super(FramelessWindowBase, self).__init__(parent=kwargs["parent"])
        self.shadowWidget = None  # type: ShadowOverlay
        self.resizerOverlay = None  # type: FramelessResizerWindow
        self._initWidth = kwargs.get("width", 400)
        self._initHeight = kwargs.get("height", 300)
        self._resizable = kwargs.get("resizable", True)
        self._shadowWidgetEnabled = False
        self._roundedWindowWidth = utils.dpiScale(kwargs.get("roundedWidth", 1))
        self.preferences = preference.interface("core_interface")
        self._undocked = False  # some weird moving behaviour when undocked so we need to keep track

    def _initUi(self):
        """ Init the frameless code.

        This should be run in the subclasses

        :return:
        :rtype:
        """

        self.titleBar = TitleBar(self)
        # After dockable show maya does weird things
        self.setFrameless()

        self.initOverlays()
        self.titleBar.moveFinished.connect(self.updateOverlays)

        self.setDefaultStyleSheet()
        self._initFramelessUi()
        self.framelessConnections()
        self.initWindowLayout()

        self.altOverlay = AltOverlay(self)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.altOverlay.setEnabled(False)  # Disabled for now. Re-enable when click through behaviour is added

        self.centralWidget = None  # type: QtWidgets.QWidget

        self.altOverlay.widgetMousePress.connect(self.mousePressEvent)
        self.altOverlay.widgetMouseMove.connect(self.mouseMoveEvent)
        self.altOverlay.widgetMouseRelease.connect(self.mouseReleaseEvent)

    def setFrameless(self):
        window = self.window()
        window.hide()
        window.setWindowFlags(window.windowFlags() | QtCore.Qt.FramelessWindowHint)
        window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        window.show()
        window.setGeometry(window.x(), window.y(), self._initWidth, self._initHeight)

    def framelessConnections(self):
        self.titleBar.minButton.leftClicked.connect(self.minimize)
        self.titleBar.maxButton.leftClicked.connect(self.maximize)
        self.titleBar.doubleClicked.connect(self.titleDoubleClicked)


    def _initFramelessUi(self):
        """ Initialize frameless code

        :return:
        """

        # Setup resizers
        self.mainWidget = QtWidgets.QWidget(self)
        self.windowContents = FramelessWindowContents(self)
        self.setCentralWidget(self.mainWidget)
        self.mainLayout = layouts.vBoxLayout(margins=(0,0,0,0), spacing=0)
        self.mainWidget.setLayout(self.mainLayout)
        # Window settings
        self.setMouseTracking(True)

    @property
    def undocked(self):
        return self._undocked

    def titleDoubleClicked(self):
        if self.isDocked():
            return

        if not self.isMinimized():
            self.minimize()
        else:
            self.maximize()

    def isMinimized(self):
        return self._minimized

    def maximize(self):
        self.setUiMinimized(False)
        # Use the resized height
        if self.isFloating():
            self.window().resize(self.savedSize)
            self.resizerOverlay.show()
            self.updateOverlays()

    def minimize(self):
        self.savedSize = self.window().size()
        self.setUiMinimized(True)
        self.window().resize(utils.dpiScale(self._minimizedWidth), 0)
        self.resizerOverlay.hide()
        self.updateOverlays()

    def setUiMinimized(self, minimized):
        """ Resizes the spacing, icons and hides only. It doesn't resize the window.

        """
        self._minimized = minimized
        if minimized:
            self.windowContents.hide()
            self.titleBar.minimize()
        else:
            self.windowContents.show()
            self.titleBar.maximize()
        self.window().setMinimumHeight(self.sizeHint().height())

    def dockChangedEvent(self, docked):

        self.setDefaultStyleSheet()
        if self.isMinimized():
            self.maximize()
        self.updateDockedOverlays()

        if env.isMac() and not docked:  # seems to regain the frames when undocked in mac
            window = self.window()
            if window.windowFlags() & QtCore.Qt.FramelessWindowHint != QtCore.Qt.FramelessWindowHint:
                window.hide()
                window.setWindowFlags(window.windowFlags() | QtCore.Qt.FramelessWindowHint)
                window.show()

    def updateDockedOverlays(self):
        if self.isDocked():
            if self.shadowWidget:
                self.shadowWidget.hide()
            self.resizerOverlay.hide()

    def enterEvent(self, event):
        """ Enter event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        # Makes sure to show the overlays from when it was hidden
        if self.undocked and self.isFloating() and (not self.shadowWidget or not self.shadowWidget.isVisible()):  # when it has been undocked an extra window is used for some reason

            if self.shadowWidget:
                self.shadowWidget.move(-9999, -9999)
                self.shadowWidget.show()
            self.resizerOverlay.show()
            self.show()
            self.updateOverlays()

            if env.isMac():
                window = self.window()
                if window.windowFlags() & QtCore.Qt.FramelessWindowHint != QtCore.Qt.FramelessWindowHint:
                    window.hide()
                    window.setWindowFlags(window.windowFlags() | QtCore.Qt.FramelessWindowHint)
                    window.show()

    def dropEvent(self, event):
        pass

    def keyReleaseEvent(self, event):
        if self.altOverlay.isEnabled():
            self.altOverlay.hide()

    def initWindowLayout(self):
        """Initialise the window layout. Eg the title, the side resizers and the contents
        """
        self.mainLayout.addWidget(self.titleBar)
        self.mainLayout.addWidget(self.windowContents, stretch=1)

    def setDefaultStyleSheet(self):
        """Try to set the default stylesheet, if not, just ignore it

        :return:
        """
        try:
            from zoo.preferences.core import preference
        except ImportError:
            return

        coreInterface = preference.interface("core_interface")
        result = coreInterface.stylesheet()

        if self.isDocked():
            self.setStyleSheet(result.data)
        else:
            self.window().setStyleSheet(result.data)

    def initOverlays(self):
        windowParent = self.window().parent()
        window = self.window()

        ow = ShadowOverlay(windowParent, flags=window.windowFlags(), frameless=self)

        if not env.isMac(): # Mac doesnt need the shadow widget. Need to test in linux still
            self.setShadowWidget(ow)

        self.resizerOverlay = FramelessResizerWindow(windowParent, target=self.window(), flags=window.windowFlags(), frameless=self)
        if self._resizable:
            self.resizerOverlay.show()
        self.resizerOverlay.resizeFinished.connect(self.resizeFinishedEvent)
        #self.resizerOverlay.resizeFinished.connect(self.titleBar.endMove)
        self.updateOverlays()

    def resizeFinishedEvent(self):

        self.updateOverlays()
        self.show()



    def updateOverlays(self):
        newPos = self.window().pos()
        x = newPos.x() - 21
        y = newPos.y() - 14

        if self.undocked and not env.isMac():
            x += 8
            y += 30

        if env.isMac():
            x += 8

        size = self.size() + QtCore.QSize(30, 30)
        if self.resizerOverlay:
            self.resizerOverlay.resizeFrameless = False
            self.resizerOverlay.setGeometry(x, y, size.width(), size.height())
            self.resizerOverlay.resizeFrameless = True

        if self.shadowWidget:
            shadowWidget = self.shadowWidget
            shadowWidget.setGeometry(x, y, size.width(), size.height())

    def updateWindowMask(self):
        """ Cut out the window for rounded edges or any other transparent things

        :return:
        :rtype:
        """
        if not self.isFloating():
            return
        # set the rounded edges of window
        px = QtGui.QPixmap(self.width(), self.height())
        px.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(px)
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        painter.drawRoundedRect(px.rect(), self._roundedWindowWidth+1, self._roundedWindowWidth+1)
        painter.end()
        self.window().setMask(px)

    def setGeometry(self, rect):
        # todo: work with docked
        self.window().setGeometry(rect)
        self.updateOverlays()

    def show(self, *args, **kwargs):
        super(FramelessWindowBase, self).show(*args, **kwargs)

    def resizeEvent(self, event):
        self.updateWindowMask()

    def isFloating(self):
        return None  # todo: to work with non maya

    def close(self):
        if self.shadowWidget:
            self.shadowWidget.close()

        if self.resizerOverlay:
            self.resizerOverlay.close()

        super(FramelessWindowBase, self).close()

    def setShadowWidget(self, widget):
        self.shadowWidget = widget
        self.shadowWidget.show()

        self.shadowWidget.move(self.window().x() - 14, self.window().y() - 14)
        #self.shadowWidget.setFixedSize(QtCore.QSize(100, 100))
        self.show()

    def isDocked(self):
        return False


class FramelessWindowStandalone(FramelessWindowBase):
    def __init__(self, *args, **kwargs):
        super(FramelessWindowStandalone, self).__init__(*args, **kwargs)
        self.show()
        self._initUi()


class FramelessWindowMaya(mayaMixin.MayaQWidgetDockableMixin, FramelessWindowBase):
    def __init__(self, *args, **kwargs):
        super(FramelessWindowMaya, self).__init__(*args, **kwargs)
        self.show(dockable=True, width=kwargs.get("width"), height=kwargs.get("width"))  # x to avoid flickering
        self._initUi()

    def _initUi(self):
        super(FramelessWindowMaya, self)._initUi()

    def close(self, *args, **kwargs):
        super(FramelessWindowMaya, self).close(*args, **kwargs)
        # MayaQWidgetDockableMixin consumes the super call so we have to make sure to run the
        # frameless window close here as well.
        FramelessWindowBase.close(self)

    def isFloating(self):
        return super(FramelessWindowMaya, self).isFloating()

    def showEvent(self, event):
        """ When the frameless window gets showed
        :param event:
        :return:
        """
        # Triggering docking changed because couldn't get MayaQWidgetDockableMixin.floatingChanged() to work

        if self._prevDock is not None and self._prevDock != self.isDocked():
            self.dockChanged.emit(self.isDocked())

            # set undocked to true if it has been undocked
            if self.undocked is False and self._prevDock is True and self.isDocked() is False:
                self._undocked = True
            self._prevDock = self.isDocked()

        if self._prevDock is None:
            self._prevDock = self.isDocked()

        super(FramelessWindowMaya, self).showEvent(event)

        # Don't run dock changed event on initial show
        if (not self.isDocked() and self.undocked) or self.isDocked():
            self.dockChangedEvent(self.isDocked())

        # Run end move since mouseReleaseEvent doesn't get run for some reason when drag dropping
        if self.isDocked():
            self.titleBar.endMove()

    def isDocked(self):
        """ Helper function

        :return:
        :rtype:
        """
        return not self.isFloating()




# Might need to move these elsewhere
if inMaya:
    FramelessWindow = FramelessWindowMaya
else:  # todo: do others
    FramelessWindow = FramelessWindowStandalone

########


class AltOverlay(overlay.OverlayWidget):

    def __init__(self, parent):
        """ Handles linux like window movement.

        Eg Alt-Middle click to move entire window
        Alt Left Click corner to resize

        :param topLeft:
        :param topRight:
        :param botLeft:
        :param botRight:
        :param parent:
        :param titleBar:
        :type parent: FramelessWindowBase
        """
        super(AltOverlay, self).__init__(parent=parent)
        self.frameless = parent
        self.titleBar = self.frameless.titleBar

        self.topLeft = self.frameless.resizerOverlay.topLeftResize  # type: CornerResize
        self.topRight = self.frameless.resizerOverlay.topRightResize  # type: CornerResize
        self.botLeft = self.frameless.resizerOverlay.botLeftResize  # type: CornerResize
        self.botRight = self.frameless.resizerOverlay.botRightResize  # type: CornerResize
        self.resizeDir = 0

    def mousePressEvent(self, event):
        """ Alt-Middle click to move window

        :param event:
        :return:
        """
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
        super(AltOverlay, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.titleBar.endMove()
        self.topLeft.windowResizedFinished.emit()
        self.topRight.windowResizedFinished.emit()
        self.botLeft.windowResizedFinished.emit()
        self.botRight.windowResizedFinished.emit()
        self.resizeDir = 0
        event.ignore()
        super(AltOverlay, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
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

        super(AltOverlay, self).mouseMoveEvent(event)

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


class TitleSplitter(QtWidgets.QSplitter):

    def __init__(self):
        """ Splitter to make sure the right widget closes before the left.

        Used for title to hide the TitleLabel first before hiding the title contents layout

        """
        super(TitleSplitter, self).__init__()
        self.setHandleWidth(0)

    def resizeEvent(self, event):
        """ Makes sure the right widget closes first by keeping the left most widget size constant

        :param event:
        :return:
        """

        if self.count() > 1:
            w = self.widget(0).sizeHint().width()
            self.setSizes([w, self.width()-w])
        return super(TitleSplitter, self).resizeEvent(event)

    def addWidget(self, *args, **kwargs):
        """ Hides the handles on widget add

        :param args:
        :param kwargs:
        :return:
        """
        super(TitleSplitter, self).addWidget(*args, **kwargs)
        self.hideHandles()

    def hideHandles(self):
        """ Hides the handles and disable them

        :return:
        """
        
        for i in range(self.count()):
            handle = self.handle(i)
            handle.setEnabled(False)
            handle.setCursor(QtCore.Qt.ArrowCursor)
            handle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)


def getFramelessWindows():
    """ Gets all frameless windows in the scene

    :return: All found window widgets under the Maya window
    """
    windows = []
    from zoo.libs.maya.qt import mayaui
    for child in mayaui.getMayaWindow().children():
        # if it has a zootoolsWindow property set, use that otherwise just use the child
        w = child.property("zootoolsWindow") or child
        if isinstance(w, FramelessWindowBase):
            windows.append(w)

    return windows

