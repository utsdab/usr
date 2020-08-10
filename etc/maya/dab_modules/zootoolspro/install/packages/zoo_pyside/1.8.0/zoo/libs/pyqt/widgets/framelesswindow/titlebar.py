from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.extended.clippedlabel import ClippedLabel
from zoo.libs.pyqt.widgets import iconmenu, layouts, buttons
from zoo.libs.pyqt.widgets.framelesswindow.framelesswidgets import THEMEPREF
from zoo.libs.utils import env


class TitleBar(QtWidgets.QFrame):
    _lastPos = None
    widgetMousePos = None
    moveFinished = QtCore.Signal()
    doubleClicked = QtCore.Signal()
    MinimizeButton = 1
    MaximizeButton = 2
    CloseButton = 4

    def __init__(self, parent=None, height=40, windowButtons=CloseButton):
        """ Title Bar for frameless windows

        :param parent:
        :type parent: zoo.libs.pyqt.widgets.framelesswindow.frameless.FramelessWindowBase
        :param windowButtons: For all buttons use pipe operator. MinimizeButton | MaximizeButton | CloseButton
        :type windowButtons: int
        """
        self.frameless = parent
        super(TitleBar, self).__init__()

        self._initWindowButtonVis = windowButtons

        self._moveStarted = False
        self._height = height

        self.iconSize = 13

        self._initUi()

    def _initUi(self):

        # Initialize
        self.logoButton = iconmenu.IconMenuButton(parent=self)
        self.titleButtonsLayout = layouts.hBoxLayout()
        self.contentsLayoutWgt = QtWidgets.QFrame(self)
        self.titleLayoutWgt = QtWidgets.QWidget(self)
        self.mainLayout = layouts.hBoxLayout(self)
        self.cornerContents = QtWidgets.QWidget(self)

        self.mainRightLayout = layouts.hBoxLayout()
        self.contentsLayout = layouts.hBoxLayout()
        self.cornerContentsLayout = layouts.hBoxLayout()
        self.titleLayout = layouts.hBoxLayout()

        self.isActiveWindow()

        self.closeButton = buttons.ExtendedButton(parent=self)
        self.minButton = buttons.ExtendedButton(parent=self)
        self.maxButton = buttons.ExtendedButton(parent=self)
        alwaysShowAll = False
        self.titleLabel = FramelessTitleLabel(parent=self, alwaysShowAll=alwaysShowAll)
        self.splitLayout = layouts.hBoxLayout()
        self.setFixedHeight(utils.dpiScale(self._height))

        # Layout
        self.initLogoButton()
        self._initWindowButtons()
        self.mainLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 0))
        self.mainLayout.setSpacing(0)
        self.titleLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.contentsLayout.setContentsMargins(0, 0, 0, 0)
        self.cornerContentsLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.cornerContents.setLayout(self.cornerContentsLayout)
        self.titleButtonsLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.titleButtonsLayout.addWidget(self.minButton)
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

        self._connections()

        # Left right margins have to be zero otherwise the title toolbar will flicker (eg toolsets)
        self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 7))

        self.mainRightLayout.setStretch(0, 1)
        QtCore.QTimer.singleShot(0, self.refreshTitleBar)

    def _connections(self):
        self.closeButton.leftClicked.connect(self.closeWindow)

    def _initWindowButtons(self):
        col = THEMEPREF.FRAMELESS_TITLELABEL_COLOR
        self.closeButton.setIconByName("xMark", colors=col, size=self.iconSize, colorOffset=80)
        self.minButton.setIconByName("minus", colors=col, size=self.iconSize, colorOffset=80)
        self.maxButton.setIconByName("checkbox", colors=col, size=self.iconSize, colorOffset=80)

        if self._initWindowButtonVis & TitleBar.CloseButton != TitleBar.CloseButton:
            self.closeButton.hide()
        if self._initWindowButtonVis & TitleBar.MinimizeButton != TitleBar.MinimizeButton:
            self.minButton.hide()
        if self._initWindowButtonVis & TitleBar.MaximizeButton != TitleBar.MaximizeButton:
            self.maxButton.hide()

        # Button Settings
        btns = [self.closeButton, self.minButton, self.maxButton]
        for b in btns:
            b.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            b.setDoubleClickEnabled(False)

    def mouseDoubleClickEvent(self, event):
        super(TitleBar, self).mouseDoubleClickEvent(event)
        self.doubleClicked.emit()

    def setLogoHighlight(self, highlightColor=None):

        size = uiconstants.TITLE_LOGOICON_SIZE

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

    def refreshTitleBar(self):
        """ Workaround for mainLayout not showing

        :return:
        """
        QtWidgets.QApplication.processEvents()
        self.updateGeometry()
        self.update()
        print("test if we still need to do this. Test when contents are added")

    def closeWindow(self):
        """ Close the window.

        :return:
        :rtype:
        """
        self.frameless.close()

    def initLogoButton(self):
        """Initialise logo button settings
        """
        self.setLogoHighlight(None)
        self.logoButton.setIconSize(QtCore.QSize(24, 24))
        self.logoButton.setFixedSize(QtCore.QSize(30, 24))
        self.logoButton.addAction("Create 3D Characters", connect=self.create3dCharactersAction)
        self.logoButton.setMenuAlign(QtCore.Qt.AlignLeft)

    def mousePressEvent(self, event):
        """Mouse click event to start the moving of the window

        :type event: QtGui.QMouseEvent
        """
        self._lastPos = QtGui.QCursor.pos()

        event.ignore()

    def create3dCharactersAction(self):
        """ The menu button to open to create 3d characters webpage

        :return:
        :rtype:
        """
        import webbrowser
        webbrowser.open("http://create3dcharacters.com")

    def mouseReleaseEvent(self, event):
        """Mouse release for title bar

        :type event: QtGui.QMouseEvent
        """
        self.endMove()

    def startMove(self):

        self.widgetMousePos = self.mapFromGlobal(QtGui.QCursor.pos())

        if self.frameless.shadowWidget:
            rect = QtCore.QRect(self.frameless.shadowWidget.geometry())
            rect.setHeight(rect.height()-self.shadowOffset()+1)
            self.frameless.shadowWidget.setGeometry(rect)

        if self.frameless.resizerOverlay:
            self.frameless.resizerOverlay.move(-9999, -9999)  # Move the resizer out of the way
        self.frameless.show()

    def endMove(self):

        if self.frameless.shadowWidget and not self.frameless.isDocked():
            self.frameless.shadowWidget.show()

        if self._moveStarted:
            self.moveFinished.emit()
            self.widgetMousePos = None
            self._moveStarted = False
            print (" move finished")

    def shadowOffset(self):
        return self.height() + 15

    def mouseMoveEvent(self, event):
        """Move the window based on if the titlebar has been clicked or not

        :type event: QtGui.QMouseEvent
        """
        # If docked, avoid moving
        if self.frameless.isDocked():
            return

        threshold = 1  # Threshold before the mouse registers as moving
        if not self._moveStarted and self._lastPos is not None and \
                (self._lastPos - QtGui.QCursor.pos()).manhattanLength() > threshold:
            self._moveStarted = True
            self.startMove()
            QtWidgets.QApplication.processEvents()

        if self.widgetMousePos is None:
            return

        xOffset = 0
        yOffset = 0
        # todo: fix this area
        # Move the window based on mouse position
        if env.isWindows():
            xOffset = 7
            yOffset = 0

        if self.frameless.undocked:  # figure out why we need this instead of doing it this way
            if env.isWindows():
                xOffset -= 8
                yOffset -= 30

        newPos = QtGui.QCursor.pos()

        newPos.setX(newPos.x() - self.widgetMousePos.x() + xOffset)
        newPos.setY(newPos.y() - self.widgetMousePos.y() + yOffset)
        self.window().move(newPos)
        if self.frameless.shadowWidget:
            if self.frameless.undocked:
                shadowPos = QtGui.QCursor.pos()
                shadowPos.setX(shadowPos.x() - self.widgetMousePos.x()-17)
                shadowPos.setY(shadowPos.y() - self.widgetMousePos.y()-16+self.shadowOffset())
            else:
                shadowPos = QtCore.QPoint(newPos)
                shadowPos.setX(shadowPos.x() - 21)
                shadowPos.setY(shadowPos.y() - 16 + self.shadowOffset())

            self.frameless.shadowWidget.move(shadowPos.x(), shadowPos.y())



    def minimize(self):
        """ Behaviour for when the window is minimized

        :return:
        :rtype:
        """
        self.contentsLayoutWgt.hide()
        self.cornerContents.hide()
        self.logoButton.setIconSize(QtCore.QSize(12, 12))
        self.logoButton.setFixedSize(QtCore.QSize(10, 12))
        self.closeButton.setFixedSize(QtCore.QSize(10, 18))
        self.closeButton.setIconSize(QtCore.QSize(12, 12))
        self.setFixedHeight(utils.dpiScale(20))
        self.titleLabel.setFixedHeight(utils.dpiScale(20))
        utils.setStylesheetObjectName(self.titleLabel, "Minimized")
        self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 3, 15, 7))
        self.mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))

        QtWidgets.QApplication.processEvents()

    def maximize(self):
        """ Behaviour for when the window is maximized

        :return:
        :rtype:
        """
        utils.setStylesheetObjectName(self.titleLabel, "")
        self.setFixedHeight(utils.dpiScale(self._height))

        self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 7))
        self.mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 0))
        self.logoButton.setIconSize(QtCore.QSize(24, 24))
        self.logoButton.setFixedSize(QtCore.QSize(30, 24))
        self.closeButton.setFixedSize(QtCore.QSize(28, 24))
        self.closeButton.setIconSize(QtCore.QSize(16, 16))

        self.contentsLayoutWgt.show()
        self.cornerContents.show()


class FramelessWindowContents(QtWidgets.QFrame):
    """ For CSS purposes """


class FramelessTitleLabel(ClippedLabel):
    """ For CSS purposes """
    def __init__(self, *args, **kwargs):
        super(FramelessTitleLabel, self).__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignRight)