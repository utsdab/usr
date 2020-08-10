from Qt import QtWidgets, QtCore, QtGui
from Qt.QtWidgets import QWidget

from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.extended.clippedlabel import ClippedLabel
from zoo.libs.pyqt.widgets import mainwindow, layouts, buttons, dpiscaling
from zoo.libs.pyqt.widgets import overlay, iconmenu
from zoo.libs.utils import zlogging
from zoo.preferences.core import preference

logger = zlogging.getLogger(__name__)


class ResizeDirection:
    """ Flag attributes to tell the what position the resizer is """
    Left = 1
    Top = 2
    Right = 4
    Bottom = 8


class Resizers:
    Vertical = 1
    Horizontal = 2
    Corners = 4
    All = Vertical | Horizontal | Corners


class FramelessWindow(mainwindow.MainWindow):
    """ Custom window with the frame removed, with our own customizations
    """

    dockChanged = QtCore.Signal(object)
    windowResizedFinished = QtCore.Signal()
    framelessChanged = QtCore.Signal(object)

    maximizeEnabled = False
    minimizeEnabled = False


    def __init__(self, title="", parent=None, width=100, height=100, framelessChecked=True, titleBarClass=None,
                 titleShrinksFirst=True, alwaysShowAllTitle=False):
        """ Frameless Window

        :param title:
        :param parent:
        :param width:
        :param height:
        :param framelessChecked:
        """

        self.minimizedWidth = 390
        self.savedSize = None  # type: QtCore.QSize
        self.preferences = preference.interface("core_interface")
        self.topResize = VerticalResize()
        self.botResize = VerticalResize()
        self.rightResize = HorizontalResize()
        self.leftResize = HorizontalResize()
        self.topLeftResize = CornerResize()
        self.topRightResize = CornerResize()
        self.botLeftResize = CornerResize()
        self.botRightResize = CornerResize()
        self.centralWidget = None  # type: QtWidgets.QWidget
        self._minimized = False

        self.resizers = [self.topResize, self.topRightResize, self.rightResize,
                         self.botRightResize, self.botResize, self.botLeftResize,
                         self.leftResize, self.topLeftResize]

        self.horizontalResizers = (self.leftResize, self.rightResize)
        self.verticalResizers = (self.topResize, self.botResize)
        self.cornerResizers = (self.topLeftResize, self.topRightResize, self.botLeftResize, self.botRightResize)

        super(FramelessWindow, self).__init__(title=title, parent=parent, width=width, height=height,
                                              showOnInitialize=False, transparent=True)

        for r in self.resizers:
            r.setParent(self)

        self.framelessChecked = framelessChecked

        if titleBarClass is not None:
            self.titleBar = titleBarClass(self, alwaysShowAll=alwaysShowAllTitle)
        else:
            self.titleBar = FramelessTitleBar(self, alwaysShowAll=alwaysShowAllTitle)

        self.windowLayout = QtWidgets.QGridLayout()
        self.windowContents = FramelessWindowContents(self)
        self.initFramelessUi()
        self.prevGeometryMin = None

        self.framelessConnections()
        self.initWindowLayout()

        self.currentDocked = None
        self.setProperty("framelessWindow", True)
        self.setDefaultStyleSheet()
        self.setWindowTitle(title)
        self.setMinimiseVisible(False)

        # This could be done better
        if not framelessChecked:
            self.setResizerActive(False)
        else:
            self.setFrameless(True)

        self.overlay = FramelessOverlay(self, self.titleBar,
                                        topLeft=self.topLeftResize,
                                        topRight=self.topRightResize,
                                        botLeft=self.botLeftResize,
                                        botRight=self.botRightResize
                                        )
        self.overlay.setEnabled(False)  # Disabled for now. Re-enable when click through behaviour is added

        self.centralWidget = None  # type: QtWidgets.QWidget

        self.overlay.widgetMousePress.connect(self.mousePressEvent)
        self.overlay.widgetMouseMove.connect(self.mouseMoveEvent)
        self.overlay.widgetMouseRelease.connect(self.mouseReleaseEvent)

        self.titleBar.setTitleClosesFirst(titleShrinksFirst)
        self.titleBar.maxButton.setVisible(self.maximizeEnabled)
        self.setProperty("tool", self)


    def initFramelessUi(self):
        """ Initialize frameless code

        :return:
        """

        # Setup resizers
        for r in self.resizers:
            r.windowResizedFinished.connect(self.windowResizedFinished)

        self.centralWidget = QtWidgets.QWidget(self)
        self.setCustomCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.windowLayout)

        # Window settings
        self.setMouseTracking(True)

        self.setResizeDirections()

    def setWindowTitle(self, title):
        """ Set the window title

        :param title:
        :return:
        """
        super(FramelessWindow, self).setWindowTitle(title)
        if hasattr(self, "titleBar"):
            self.titleBar.setTitleText(title)

    def setResizersEnabled(self, enabled, resizers=Resizers.All):
        """ Set resizers enabled. Can be set for the vertical, horizontal or corners

        eg. Resizers.Vertical | Resizers.Horizontal for both vertical and horizontal

        :param enabled:
        :type enabled:
        :param resizers:
        :type resizers:
        :return:
        :rtype:
        """
        toEnable = []
        if resizers & Resizers.Corners == Resizers.Corners:
            toEnable += self.cornerResizers
        if resizers & Resizers.Vertical == Resizers.Vertical:
            toEnable += self.verticalResizers
        if resizers & Resizers.Horizontal == Resizers.Horizontal:
            toEnable += self.horizontalResizers

        [r.setEnabled(enabled) for r in toEnable]

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

        self.setStyleSheet(result.data)

    def closeEvent(self, ev):
        super(FramelessWindow, self).closeEvent(ev)

    def keyPressEvent(self, event):
        if event.modifiers() == self.overlay.overlayActiveKey and self.overlay.isEnabled():

            self.overlay.show()

    def keyReleaseEvent(self, event):
        if self.overlay.isEnabled():
            self.overlay.hide()

    def titleDoubleClicked(self):
        if not self.isMinimized():
            self.minimize()
        else:
            self.maximize()

    def isMinimized(self):
        return self._minimized

    def enterEvent(self, event):
        """ Show overlay on mouse enter

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self.displayOverlay()

    def mouseMoveEvent(self, event):
        """ Show overlay on mouse move

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self.displayOverlay()

    def displayOverlay(self):
        if QtWidgets.QApplication.keyboardModifiers() == self.overlay.overlayActiveKey:
            self.overlay.show()
        else:
            self.overlay.hide()

    def setFrameless(self, frameless=True):
        """ Use this to turn off frameless if need be

        :param frameless:
        """
        window = self.window()

        # Set Frameless
        if frameless and not self.isFrameless():
            window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            window.setWindowFlags(window.windowFlags() |
                                  QtCore.Qt.FramelessWindowHint |
                                  QtCore.Qt.NoDropShadowWindowHint)
            window.setWindowFlags(window.windowFlags() ^ QtCore.Qt.WindowMinMaxButtonsHint)

            self.setResizerActive(True)
        elif not frameless and self.isFrameless():
            # Set not frameless
            window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            window.setWindowFlags(window.windowFlags() |
                                  QtCore.Qt.FramelessWindowHint |
                                  QtCore.Qt.NoDropShadowWindowHint)
            self.setResizerActive(False)
        window.show()

    def setTitleBarIconSize(self, size):
        """ Set Icon size of the title icon

        :param size:
        :type size: QtCore.QSize
        :return:
        """
        self.titleBar.setLogoButtonSize(size)

    def setWindowStyleSheet(self, style):
        """Set the style sheet of the window

        :param style:
        :return:
        """
        # if not self.isDocked():
        #    self.window().setStyleSheet(style)

        self.setStyleSheet(style)

    def connectMinimizeButton(self, connect):
        """Connect minimize button

        :param connect:
        :return:
        """
        self.titleBar.minimizeButton.leftClicked.connect(connect)

    def isFrameless(self):
        """Checks to see if the FramelessWindowHint flag in windowFlags
        """
        return self.window().windowFlags() & QtCore.Qt.FramelessWindowHint == QtCore.Qt.FramelessWindowHint

    def isDocked(self):
        """ For autocompletion

        :return:
        :rtype:
        """
        pass

    def resizerHeight(self):
        """Calculates the total height of the vertical resizers
        """
        resizers = [self.topResize, self.botResize]
        ret = 0
        for r in resizers:
            if not r.isHidden():
                ret += r.minimumSize().height()

        return ret

    def resizerWidth(self):
        """ Calculates the total width of the vertical resizers
        """
        resizers = [self.leftResize, self.rightResize]
        ret = 0
        for r in resizers:
            if not r.isHidden():
                ret += r.minimumSize().width()

        return ret

    def setResizerActive(self, active):
        """Enable or disable the resizers

        :param active:
        """

        if active:
            for r in self.resizers:
                r.show()
        else:
            for r in self.resizers:
                r.hide()

    def initWindowLayout(self):
        """Initialise the window layout. Eg the title, the side resizers and the contents
        """

        self.windowLayout.addWidget(self.titleBar, 1, 1, 1, 1)
        self.windowLayout.addWidget(self.windowContents, 2, 1, 1, 1)
        self.windowLayout.setHorizontalSpacing(0)
        self.windowLayout.setVerticalSpacing(0)

        self.windowLayout.setContentsMargins(0, 0, 0, 0)

        self.windowLayout.addWidget(self.topLeftResize, 0, 0, 1, 1)
        self.windowLayout.addWidget(self.topResize, 0, 1, 1, 1)
        self.windowLayout.addWidget(self.topRightResize, 0, 2, 1, 1)

        self.windowLayout.addWidget(self.leftResize, 1, 0, 2, 1)
        self.windowLayout.addWidget(self.rightResize, 1, 2, 2, 1)

        self.windowLayout.addWidget(self.botLeftResize, 3, 0, 1, 1)
        self.windowLayout.addWidget(self.botResize, 3, 1, 1, 1)
        self.windowLayout.addWidget(self.botRightResize, 3, 2, 1, 1)

        self.windowLayout.setColumnStretch(1, 1)
        self.windowLayout.setRowStretch(2, 1)

        # Shadow effects
        self.setShadowEffectEnabled(True)

    def setShadowEffectEnabled(self, enabled):
        if enabled:
            self.shadowEffect = QtWidgets.QGraphicsDropShadowEffect(self)
            self.shadowEffect.setBlurRadius(utils.dpiScale(15))
            self.shadowEffect.setColor(QtGui.QColor(0, 0, 0, 150))
            self.shadowEffect.setOffset(utils.dpiScale(0))
            self.setGraphicsEffect(self.shadowEffect)
        else:
            self.setGraphicsEffect(None)


    def setResizeDirections(self):
        """Set the resize directions for the resize widgets for the window
        """
        # Horizontal/Vertical Resizers
        self.topResize.setResizeDirection(ResizeDirection.Top)
        self.botResize.setResizeDirection(ResizeDirection.Bottom)
        self.rightResize.setResizeDirection(ResizeDirection.Right)
        self.leftResize.setResizeDirection(ResizeDirection.Left)

        # Corner Resizers
        self.topLeftResize.setResizeDirection(ResizeDirection.Left | ResizeDirection.Top)
        self.topRightResize.setResizeDirection(ResizeDirection.Right | ResizeDirection.Top)
        self.botLeftResize.setResizeDirection(ResizeDirection.Left | ResizeDirection.Bottom)
        self.botRightResize.setResizeDirection(ResizeDirection.Right | ResizeDirection.Bottom)

    def framelessConnections(self):
        self.dockChanged.connect(self.dockEvent)
        self.connectMinimizeButton(self.minimize)
        self.titleBar.maxButton.leftClicked.connect(self.maximize)
        self.titleBar.doubleClicked.connect(self.titleDoubleClicked)

    def maximize(self):
        self.setUiMinimized(False)
        self._minimized = False
        # Use the resized height
        self.window().resize(self.savedSize)

    def minimize(self):
        self.savedSize = self.window().size()
        self._minimized = True

        self.setUiMinimized(True)
        utils.processUIEvents()
        utils.singleShotTimer(0, lambda: self.window().resize(utils.dpiScale(self.minimizedWidth), 0))

    def setUiMinimized(self, minimized):
        """ Resizes the spacing, icons and hides only. It doesn't resize the window.

        """
        if minimized:
            self.windowContents.hide()
            self.titleBar.contentsLayoutWgt.hide()
            self.titleBar.cornerContents.hide()
            self.titleBar.logoButton.setIconSize(QtCore.QSize(12, 12))
            self.titleBar.logoButton.setFixedSize(QtCore.QSize(10, 12))
            self.titleBar.closeButton.setFixedSize(QtCore.QSize(10, 18))
            self.titleBar.closeButton.setIconSize(QtCore.QSize(12, 12))
            self.titleBar.setFixedHeight(utils.dpiScale(20))
            self.titleBar.titleLabel.setFixedHeight(utils.dpiScale(20))

            utils.setStylesheetObjectName(self.titleBar.titleLabel, "Minimized")

            self.titleBar.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 3, 15, 7))
            self.titleBar.mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        else:
            utils.setStylesheetObjectName(self.titleBar.titleLabel, "")
            self.windowContents.show()
            self.titleBar.setFixedHeight(utils.dpiScale(self.titleBar.titleBarHeight))

            self.titleBar.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 7))
            self.titleBar.mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 0))
            self.titleBar.logoButton.setIconSize(QtCore.QSize(24, 24))
            self.titleBar.logoButton.setFixedSize(QtCore.QSize(30, 24))
            self.titleBar.closeButton.setFixedSize(QtCore.QSize(28, 24))
            self.titleBar.closeButton.setIconSize(QtCore.QSize(16, 16))

            self.titleBar.contentsLayoutWgt.show()
            self.titleBar.cornerContents.show()

    def setMaximiseVisible(self, vis=True):
        self.titleBar.setMaximiseVisible(vis)

    def setMinimiseVisible(self, vis=True):
        self.titleBar.setMinimiseVisible(vis)

    def setMainLayout(self, layout):
        self.windowContents.setLayout(layout)

    def showEvent(self, event):
        """
        When the frameless window gets showed
        :param event:
        :return:
        """
        # Triggering docking changed because couldn't get MayaQWidgetDockableMixin.floatingChanged() to work
        if self.isDocked() != self.currentDocked:
            self.currentDocked = self.isDocked()
            self.dockChanged.emit(self.currentDocked)

        super(FramelessWindow, self).showEvent(event)

    def dockEvent(self, docked):
        """
        Ran when the window gets docked or undocked
        :param docked:
        :return:
        """
        if docked:
            self.setResizerActive(not docked)

    def settingsName(self):
        return self.objectName()

    def setLogoColor(self, color):
        self.titleBar.logoButton.setIconColor(color)

    def titlebarContentsLayout(self):
        return self.titleBar.contentsLayout

    def cornerContentsLayout(self):
        return self.titleBar.cornerContentsLayout


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


class FramelessTitleBar(QtWidgets.QFrame):
    """
    Title bar of the frameless window. Click drag this widget to move the window widget
    """
    doubleClicked = QtCore.Signal()

    def __init__(self, window=None, parent=None, showTitle=True, alwaysShowAll=False):
        """

        :param window:
        :type window: FramelessWindow
        :param parent:
        :type parent: QtWidgets.QWidget
        """
        super(FramelessTitleBar, self).__init__(parent=parent or window)

        self.titleBarHeight = 40
        self.contentsLayoutWgt = QtWidgets.QFrame(self)
        self.titleLayoutWgt = QtWidgets.QWidget(self)
        self.mainLayout = layouts.hBoxLayout(self)
        self.cornerContents = QtWidgets.QWidget(self)
        self.mainRightLayout = layouts.hBoxLayout()
        self.contentsLayout = layouts.hBoxLayout()
        self.cornerContentsLayout = layouts.hBoxLayout()
        self.titleLayout = layouts.hBoxLayout()

        self.frameless = window
        self.mousePos = None  # type: QtCore.QPoint
        self.widgetMousePos = None  # type: QtCore.QPoint
        self.themePref = preference.interface("core_interface")

        # Title bar buttons
        self.logoButton = iconmenu.IconMenuButton(parent=self)

        self.titleButtonsLayout = layouts.hBoxLayout()

        self.toggle = True

        self.iconSize = 13
        self.closeButton = buttons.ExtendedButton(parent=self)
        self.minimizeButton = buttons.ExtendedButton(parent=self)
        self.maxButton = buttons.ExtendedButton(parent=self)
        self.titleLabel = FramelessTitleLabel(parent=self, alwaysShowAll=alwaysShowAll)
        self.splitLayout = layouts.hBoxLayout()

        if not showTitle:
            self.titleLabel.hide()

        self.initUi()
        self.connections()

    def mouseDoubleClickEvent(self, event):
        super(FramelessTitleBar, self).mouseDoubleClickEvent(event)
        self.doubleClicked.emit()

    def setLogoHighlight(self, highlightColor=None):
        smaller = 0.5 if self.frameless.isMinimized() else 1
        size = uiconstants.TITLE_LOGOICON_SIZE * smaller

        if highlightColor is not None:
            self.logoButton.setIconByName(["zooToolsZ"],
                                          colors=[None],
                                          tint=(0, 200, 0, 50),
                                          tintComposition=QtGui.QPainter.CompositionMode_Plus,
                                          size=size,
                                          iconScaling=[1],
                                          colorOffset=40, grayscale=True)
        else:
            self.logoButton.setIconByName(["zooToolsZ"],
                                          colors=[None, None],
                                          size=size,
                                          iconScaling=[1],
                                          colorOffset=40)
            
    def initUi(self):
        self.setFixedHeight(utils.dpiScale(self.titleBarHeight))
        self.setLogoHighlight(None)

        col = self.themePref.FRAMELESS_TITLELABEL_COLOR
        self.closeButton.setIconByName("xMark", colors=col, size=self.iconSize, colorOffset=80)
        self.minimizeButton.setIconByName("minus", colors=col, size=self.iconSize, colorOffset=80)
        self.maxButton.setIconByName("checkbox", colors=col, size=self.iconSize, colorOffset=80)

        # Button Settings
        btns = [self.closeButton, self.minimizeButton, self.maxButton]
        for b in btns:
            b.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            b.setDoubleClickEnabled(False)

        # Layout
        self.mainLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 0))
        # self.setLayout(self.mainLayout)
        self.mainLayout.setSpacing(0)

        self.titleLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.initLogoButton()

        self.contentsLayout.setContentsMargins(0, 0, 0, 0)
        self.cornerContents = QtWidgets.QWidget(self)
        self.cornerContentsLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.cornerContents.setLayout(self.cornerContentsLayout)
        self.titleButtonsLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))

        self.titleButtonsLayout.addWidget(self.minimizeButton)
        self.titleButtonsLayout.addWidget(self.maxButton)
        self.titleButtonsLayout.addWidget(self.closeButton)

        self.titleLayoutWgt.setLayout(self.titleLayout)

        self.mainLayout.addSpacing(utils.dpiScale(8))
        self.mainLayout.addWidget(self.logoButton)
        self.mainLayout.addSpacing(utils.dpiScale(6))
        self.mainLayout.addLayout(self.mainRightLayout)

        self.contentsLayoutWgt.setLayout(self.contentsLayout)

        self.splitLayout.addWidget(self.contentsLayoutWgt)
        self.splitLayout.addWidget(self.titleLayoutWgt)


        self.mainRightLayout.addLayout(self.splitLayout)
        self.mainRightLayout.addWidget(self.cornerContents)
        self.mainRightLayout.addLayout(self.titleButtonsLayout)
        self.mainRightLayout.setAlignment(QtCore.Qt.AlignVCenter)
        self.titleButtonsLayout.setAlignment(QtCore.Qt.AlignVCenter)
        self.mainRightLayout.addSpacing(utils.dpiScale(6))

        self.titleLayout.addWidget(self.titleLabel)

        # Left right margins have to be zero otherwise the title toolbar will flicker (eg toolsets)
        self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 7))
        self.mainRightLayout.setStretch(0, 1)
        QtCore.QTimer.singleShot(0, self.refreshTitleBar)

    def refreshTitleBar(self):
        """ Workaround for mainLayout not showing

        :return:
        """
        QtWidgets.QApplication.processEvents()
        self.updateGeometry()
        self.update()

    def setTitleClosesFirst(self, closeFirst):
        """ Enabled means the title will disappear first after resizing if the width is too small

        If its disabled, the contentsLayout will resize at the same speed as the titleLayout

        :param closeFirst:
        :return:
        """
        widgets = []
        firstWgt = self.splitLayout.itemAt(0).widget()

        # Use Splitter
        if closeFirst is True and not isinstance(firstWgt, TitleSplitter):
            widgets.append(self.splitLayout.takeAt(0).widget())

            for i in range(self.splitLayout.count()):
                widgets.append(self.splitLayout.takeAt(0).widget())

            split = TitleSplitter()

            for w in widgets:
                split.addWidget(w)

            self.splitLayout.addWidget(split)

        # Use Layout
        elif closeFirst is False and isinstance(firstWgt, TitleSplitter):
            split = firstWgt  # type: QtWidgets.QSplitter

            for i in range(split.count()):
                wgt = split.widget(i)
                if wgt is None:
                    continue

                self.splitLayout.addWidget(wgt)

    def setTitleText(self, value=""):
        """ The text of the title bar in the window

        :param value:
        :type value:
        :return:
        :rtype:
        """
        self.titleLabel.setText(value.upper())

    def connections(self):
        self.closeButton.leftClicked.connect(self.closeWindow)

    def closeWindow(self):
        """ Close the window.

        :return:
        :rtype:
        """

        if self.frameless.isDocked():
            self.frameless.close()
        else:
            self.window().close()

    def initLogoButton(self):
        """Initialise logo button settings
        """
        self.logoButton.setIconSize(QtCore.QSize(24, 24))
        self.logoButton.setFixedSize(QtCore.QSize(30, 24))
        toggleFrameless = self.logoButton.addAction("Toggle Custom Window",
                                                    connect=self.setFramelessEnabled,
                                                    checkable=True)
        self.logoButton.addAction("Create 3D Characters", connect=self.create3dCharactersAction)
        self.frameless.framelessChecked = self.frameless.framelessChecked or False
        toggleFrameless.setChecked(self.frameless.framelessChecked)
        self.logoButton.setMenuAlign(QtCore.Qt.AlignLeft)

    def create3dCharactersAction(self):
        """ The menu button to open to create 3d characters webpage

        :return:
        :rtype:
        """
        import webbrowser
        webbrowser.open("http://create3dcharacters.com")

    def setLogoButtonSize(self, size):
        pass

    def setWindowIconSize(self, size):
        """
        Sets the icon size of the titlebar icons
        :param size:
        :return:
        """
        self.iconSize = size

    def setFramelessEnabled(self, action=None):
        """ Enable frameless or switch back to operating system default.

        This is maya specific, may need to change this in the future. Will need to rework all this code

        :param action:
        :return:
        :rtype: FramelessWindow
        """

        from zoo.apps.toolpalette import run

        a = run.show()

        toolDef = a.pluginFromTool(self.frameless)
        frameless = action.isChecked()

        offset = QtCore.QPoint()

        if self.frameless.isDocked():
            rect = self.frameless.rect()
            pos = self.frameless.mapToGlobal(QtCore.QPoint(-10, -10))
            rect.setWidth(rect.width() + 21)
            self.frameless.close()
        else:
            rect = self.window().rect()
            pos = self.window().pos()
            offset = QtCore.QPoint(3, 15)
            self.window().close()

        toolDef._execute(executeFrameless=frameless)

        newTool = toolDef.latestTool()
        # Make sure the size and position is correct. Use a timer because doing it instantly doesn't work. Bit yucky D=
        QtCore.QTimer.singleShot(0, lambda: newTool.window().setGeometry(pos.x() + offset.x(),
                                                                         pos.y() + offset.y(),
                                                                         rect.width(),
                                                                         rect.height()))
        newTool.framelessChanged.emit(frameless)
        QtWidgets.QApplication.processEvents()
        return newTool

    def setMaximiseVisible(self, show=True):
        """Set Maximise button visible

        :param show:
        """
        if show:
            self.maxButton.show()
        else:
            self.maxButton.hide()

    def setMinimiseVisible(self, show=True):
        """Set minimize button visibility

        :param show:
        """
        if show:
            self.minimizeButton.show()
        else:
            self.minimizeButton.hide()

    def toggleContents(self):
        """Show or hide the additional contents in the titlebar
        """
        if self.contentsLayout.count() > 0:
            for i in range(1, self.contentsLayout.count()):
                widget = self.contentsLayout.itemAt(i).widget()
                if widget.isHidden():
                    widget.show()
                else:
                    widget.hide()

    def mousePressEvent(self, event):
        """Mouse click event to start the moving of the window

        :type event: :class:`QtCore.QEvent`
        """
        if event.buttons() & QtCore.Qt.LeftButton:
            self.startMove()

        event.ignore()

    def mouseReleaseEvent(self, event):
        """Mouse release for title bar

        :type event: :class:`QtCore.QEvent`
        """
        self.endMove()

    def startMove(self):
        self.widgetMousePos = self.frameless.mapFromGlobal(QtGui.QCursor.pos())

    def endMove(self):
        self.widgetMousePos = None

    def mouseMoveEvent(self, event):
        """Move the window based on if the titlebar has been clicked or not

        :type event: :class:`QtCore.QEvent`
        """
        if self.widgetMousePos is None:
            return

        # If its normal windows mode, then disable mouseMove
        if not self.frameless.isFrameless():
            return

        pos = QtGui.QCursor.pos()
        newPos = pos

        newPos.setX(pos.x() - self.widgetMousePos.x())
        newPos.setY(pos.y() - self.widgetMousePos.y())

        self.window().move(newPos)


class FramelessWindowContents(QtWidgets.QFrame):
    """ For CSS purposes """


class FramelessTitleLabel(ClippedLabel):
    """ For CSS purposes """
    def __init__(self, *args, **kwargs):
        super(FramelessTitleLabel, self).__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignRight)


class WindowResizer(QtWidgets.QFrame):
    """
    The resize widgets for the sides of the windows and the corners to resize the parent window.

    """
    windowResized = QtCore.Signal()
    windowResizeStartEvent = QtCore.Signal()
    windowResizedFinished = QtCore.Signal()

    def __init__(self, parent):
        super(WindowResizer, self).__init__(parent=parent)
        self.initUi()
        self.direction = 0  # ResizeDirection
        self.widgetMousePos = None  # QtCore.QPoint
        self.widgetGeometry = None  # type: QtCore.QRect
        self.setStyleSheet("background:transparent;")
        self.frameless = None  # type: FramelessWindow

        self.windowResizeStartEvent.connect(self.windowResizeStart)

    def initUi(self):
        self.windowResized.connect(self.windowResizeEvent)

    def paintEvent(self, event):
        """ Mouse events seem to deactivate when its completely transparent. Hacky way to avoid that for now.

        :type event: :class:`QtCore.QEvent`
        """

        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(255, 0, 0, 1))
        painter.end()

    def leaveEvent(self, event):
        """ Turn the mouse back to original

        :type event: :class:`QtCore.QEvent`
        """
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.restoreOverrideCursor()

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
        """
        self.frameless = parent
        super(WindowResizer, self).setParent(parent)

    def windowResizeEvent(self):
        """ Resize based on the mouse position and the current direction
        """
        pos = QtGui.QCursor.pos()
        newGeometry = self.window().frameGeometry()

        # Minimum Size
        mW = self.window().minimumSize().width()
        mH = self.window().minimumSize().height()

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

        self.window().setGeometry(x, y, w, h)

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

    def __init__(self, parent=None):
        super(CornerResize, self).__init__(parent=parent)

    def initUi(self):
        super(CornerResize, self).initUi()

        self.setFixedSize(utils.sizeByDpi(QtCore.QSize(10, 10)))

    def enterEvent(self, event):
        """ Set cursor based on corner hovered

        :type event: :class:`QtCore.QEvent`
        """
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

    def __init__(self, parent=None):
        super(VerticalResize, self).__init__(parent=parent)

    def initUi(self):
        super(VerticalResize, self).initUi()
        self.setFixedHeight(utils.dpiScale(8))

    def enterEvent(self, event):
        """Change cursor on hover

        :type event: :class:`QtCore.QEvent`
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeVerCursor)


class HorizontalResize(WindowResizer):
    """ Resizers for the left and right of the window

    """

    def __init__(self, parent=None):
        super(HorizontalResize, self).__init__(parent=parent)

    def initUi(self):
        super(HorizontalResize, self).initUi()
        self.setFixedWidth(utils.dpiScale(8))

    def enterEvent(self, event):
        """Change cursor on hover

        :type event: :class:`QtCore.QEvent`
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.SizeHorCursor)


def getFramelessWindows():
    """ Gets all frameless windows in the scene

    :return: All found window widgets under the Maya window
    """
    windows = []
    from zoo.libs.maya.qt import mayaui
    for child in mayaui.getMayaWindow().children():
        # if it has a zootoolsWindow property set, use that otherwise just use the child
        w = child.property("zootoolsWindow") or child
        if isinstance(w, FramelessWindow):
            windows.append(w)

    return windows

