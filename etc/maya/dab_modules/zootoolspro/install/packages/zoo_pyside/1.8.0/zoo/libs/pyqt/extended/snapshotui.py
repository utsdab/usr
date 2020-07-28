import os

from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.extended.lineedit import LineEdit, IntLineEdit
from zoo.libs.pyqt.widgets.buttons import styledButton
from zoo.libs.pyqt.widgets.framelessmaya import FramelessWindowMaya
import maya.api.OpenMaya as om2
from zoo.libs.pyqt.widgets.label import Label
from zoo.libs.pyqt.widgets.layouts import vBoxLayout, hBoxLayout


class SnapshotUi(FramelessWindowMaya):
    saved = QtCore.Signal(object)

    def __init__(self, parent=None, path=None, onSave=None, imageType="png", width=512, height=512, ):
        """ Snapshot ui

        :param parent:
        :type parent:
        :param path:
        :type path:
        :param onSave:
        :type onSave:
        """
        self.defaultWidth = width
        self.defaultHeight = height
        self.imageSizeLabel = None  # type: Label
        self.bottomBar = None  # type: SnapshotFrame
        super(SnapshotUi, self).__init__(parent=parent, title="Snapshot Ui", width=self.defaultHeight, height=self.defaultHeight)
        self._savePath = path
        self.lastSavedLocation = None
        self.snapshotPx = None  # type: QtGui.QPixmap
        self.mainLayout = None  # type: vBoxLayout
        self.snapLayout = None  # type: hBoxLayout
        self.snapWidget = None  # type: QtWidgets.QWidget
        self.widthEdit = None  # type: LineEdit
        self.heightEdit = None  # type: LineEdit
        self.keepAspect = True
        self.snapshotBtn = None  # type: ExtendedButton
        self.aspectLinkBtn = None  # type: ExtendedButton
        self.lockedBtn = None  # type: ExtendedButton
        self.cancelBtn = None  # type: ExtendedButton
        self.imageType = imageType

        self.window().setWindowFlags(self.window().windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.locked = False
        self.hide()
        self.initUi()
        self.connections()
        if onSave:
            self.saved.connect(onSave)

        self.setSnapshotSize(self.defaultWidth, self.defaultHeight)




    def initUi(self):

        self.setupTitleBar()
        self.mainLayout = vBoxLayout(spacing=0)

        self.windowContents.setLayout(self.mainLayout)
        self.windowContents.setStyleSheet("FramelessWindowContents { background-color: transparent; }")
        self.snapLayout = hBoxLayout(spacing=0)
        self.mainLayout.addLayout(self.snapLayout, stretch=1)
        sidePanelLeft = SnapshotFrame(self)
        sidePanelLeft.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding))
        sidePanelLeft.setFixedWidth(utils.dpiScale(5))

        sidePanelRight = SnapshotFrame(self)
        sidePanelRight.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding))
        sidePanelRight.setFixedWidth(utils.dpiScale(5))
        self.snapWidget = QtWidgets.QWidget()
        self.snapWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.snapLayout.addWidget(sidePanelLeft)
        self.snapLayout.addWidget(self.snapWidget, stretch=1)
        self.snapLayout.addWidget(sidePanelRight)

        self.bottomBar = SnapshotFrame(self)
        self.mainLayout.addWidget(self.bottomBar)

        bottomLayout = hBoxLayout(margins=(5, 5, 5, 5))
        self.bottomBar.setLayout(bottomLayout)
        self.bottomBar.setFixedHeight(utils.dpiScale(33))

        self.imageSizeLabel = Label("Image Size")
        bottomLayout.addWidget(self.imageSizeLabel, 4)
        utils.setHSizePolicy(self.imageSizeLabel, QtWidgets.QSizePolicy.Ignored)
        self.imageSizeLabel.setMaximumWidth(self.imageSizeLabel.sizeHint().width())

        self.widthEdit = IntLineEdit()
        self.widthEdit.setMinimumWidth(utils.dpiScale(19))
        self.heightEdit = IntLineEdit()
        self.heightEdit.setMinimumWidth(utils.dpiScale(19))
        utils.setSizeHint(self.widthEdit, utils.sizeByDpi(QtCore.QSize(40, self.widthEdit.sizeHint().height())))
        utils.setSizeHint(self.heightEdit, utils.sizeByDpi(QtCore.QSize(40, self.widthEdit.sizeHint().height())))
        utils.setStylesheetObjectName(self.bottomBar, "bottomBar")
        bottomLayout.addWidget(self.widthEdit)
        self.aspectLinkBtn = styledButton(icon="linkConnected")
        iconBtnWidth = utils.dpiScale(24)
        self.aspectLinkBtn.setMinimumWidth(iconBtnWidth)

        bottomLayout.addWidget(self.aspectLinkBtn)
        bottomLayout.addWidget(self.heightEdit)
        self.lockedBtn = styledButton(icon="unlock", style=uiconstants.BTN_TRANSPARENT_BG)
        bottomLayout.addWidget(self.lockedBtn)
        bottomLayout.addStretch(1)
        self.snapshotBtn = styledButton(text="Snapshot", icon="cameraSolid")
        self.snapshotBtn.setStyleSheet("text-align:left;")
        self.snapshotBtn.setMinimumWidth(iconBtnWidth)
        self.cancelBtn = styledButton(text="Cancel", icon="xMark", style=uiconstants.BTN_DEFAULT_QT)
        self.cancelBtn.setStyleSheet("text-align:left;")
        self.cancelBtn.setMinimumWidth(iconBtnWidth)
        bottomLayout.addWidget(self.snapshotBtn, 3)
        bottomLayout.addWidget(self.cancelBtn, 3)
        utils.setHSizePolicy(self.cancelBtn, QtWidgets.QSizePolicy.Ignored)
        utils.setHSizePolicy(self.cancelBtn, QtWidgets.QSizePolicy.Ignored)
        self.snapshotBtn.setMaximumWidth(self.snapshotBtn.sizeHint().width())
        self.cancelBtn.setMaximumWidth(self.cancelBtn.sizeHint().width())
        self.window().setMinimumSize(98, 98 + 44)

    def updateUi(self):
        utils.processUIEvents()
        self.updateWidgets()
        self.resizeEvent(QtGui.QResizeEvent(self.size(), self.size()))

    def setupTitleBar(self):
        """ Make the title bar smaller

        :return:
        :rtype:
        """
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

    def connections(self):
        """ UI Connections

        :return:
        :rtype:
        """
        [r.windowResized.connect(self.windowResize) for r in self.horizontalResizers]
        [v.windowResized.connect(self.verticalResize) for v in self.verticalResizers]
        [c.windowResized.connect(self.windowResize) for c in self.cornerResizers]
        self.aspectLinkBtn.leftClicked.connect(self.toggleAspectClicked)
        self.lockedBtn.leftClicked.connect(self.toggleLockClicked)
        self.widthEdit.editingFinished.connect(self.sizeEditChanged)
        self.heightEdit.editingFinished.connect(self.sizeEditChanged)
        self.snapshotBtn.leftClicked.connect(self.snapshot)
        self.cancelBtn.clicked.connect(self.hide)

    def leaveEvent(self, event):
        super(SnapshotUi, self).leaveEvent(event)

    def snapshot(self, hide=False):
        """ Take the snapshot

        :return:
        :rtype:
        """
        rect = QtCore.QRect(self.snapWidget.rect())
        pos = self.snapWidget.mapToGlobal(QtCore.QPoint(0, 0))
        rect.translate(pos.x(), pos.y())
        self.setWindowOpacity(0)
        self.snapshotPx = utils.desktopPixmapFromRect(rect)
        self.setWindowOpacity(1)
        if hide:
            self.hide()

        dirPath = os.path.dirname(self._savePath)
        if not os.path.exists(os.path.dirname(dirPath)):
            os.makedirs(dirPath)

        self.save(self._savePath, self.imageType)


    def setSavePath(self, path):
        """ Path to save the snapshot to

        :param path:
        :type path:
        :return:
        :rtype:
        """
        self._savePath = path

    def save(self, path, imageType="png"):
        """ Save the screen shot to

        :param path: path to image to save eg: "d:\\path\\to\\image.jpg"
        :type path:
        :param imageType: png or jpg
        :type imageType: basestring
        :return:
        :rtype:
        """
        saved = None
        if path == "" or path is None:
            om2.MGlobal.displayError("Path not specified for Snapshot UI")
            self.saved.emit(saved)
            return
        saved = self.snapshotPx.save(path, imageType)
        self.lastSavedLocation = path
        self.saved.emit(path if saved else None)

    def heightOffset(self):
        return self.window().size().height() - self.snapWidget.height()

    def widthOffset(self):
        return self.window().size().width() - self.snapWidget.width()

    def sizeEditChanged(self):
        if self.locked or (self.sender() is not None and self.sender().signalsBlocked()):
            return

        width = int(self.widthEdit.text())
        height = int(self.heightEdit.text())
        self.setSnapshotSize(width, height)

    def setSnapshotSize(self, width, height):
        """ Sets the size of the snapshot widget

        :return:
        """
        widthOffset = self.widthOffset()
        heightOffset = self.heightOffset()

        if self.keepAspect:  # Keep aspect ratio
            if self.sender() == self.widthEdit:
                self.window().resize(width + widthOffset, width + heightOffset)
            elif self.sender() == self.heightEdit:
                self.window().resize(height + widthOffset, height + heightOffset)
            else:
                self.window().resize(width + widthOffset, width + heightOffset)
        else:  # Otherwise just use the text edit values
            self.window().resize(width + widthOffset, height + heightOffset)

        self.updateWidgets()

    def toggleAspectClicked(self):
        """ Toggle Aspect button

        :return:
        :rtype:
        """
        self.keepAspect = not self.keepAspect
        if self.keepAspect:
            self.aspectLinkBtn.setIconByName("linkConnected")
            self.aspectLinkBtn.setIconColor((192, 192, 192))  # todo: this needs to be fixed at styledbutton, and not done here
            self.window().resize(self.window().height()+self.widthOffset(), self.window().height()+self.heightOffset())
            self.updateWidgets()
        else:
            self.aspectLinkBtn.setIconByName("linkBroken")
            self.aspectLinkBtn.setIconColor(
                (255, 255, 255))  # todo: this needs to be fixed at styledbutton, and not done here

    def toggleLockClicked(self):
        """ Toggle Lock button

        :return:
        :rtype:
        """
        self.locked = not self.locked
        if self.locked:
            self.setResizersEnabled(False)
            self.lockedBtn.setIconByName("lock")
            self.lockedBtn.setIconColor((192, 192, 192))  # todo: this needs to be fixed at styledbutton, and not done here
            self.widthEdit.setEnabled(False)
            self.heightEdit.setEnabled(False)
            self.aspectLinkBtn.setEnabled(False)
        else:
            self.setResizersEnabled(True)
            self.lockedBtn.setIconByName("unlock")
            self.lockedBtn.setIconColor(
                (192, 192, 192))  # todo: this needs to be fixed at styledbutton, and not done here
            self.widthEdit.setEnabled(True)
            self.aspectLinkBtn.setEnabled(True)
            self.heightEdit.setEnabled(True)

    def bottomSize(self):
        return self.bottomBar.height() + self.botResize.height() + utils.dpiScale(2)

    def windowResize(self):
        """ Window resize (width and corner)

        :return:
        :rtype:
        """
        if self.keepAspect:
            self.window().resize(self.window().width(), self.window().width() + self.bottomSize())
        self.updateWidgets()

    def verticalResize(self):
        """ Vertical Resize

        :return:
        :rtype:
        """
        if self.keepAspect:
            self.window().resize(self.window().height() - self.bottomSize(), self.window().height())
        self.updateWidgets()

    def resizeEvent(self, event):
        super(SnapshotUi, self).resizeEvent(event)
        if self.imageSizeLabel is None:
            return

        hiders = ((self.imageSizeLabel, 250),
                  (self.lockedBtn, 240),
                  (self.aspectLinkBtn, 185),
                  (self.cancelBtn, 155),
                  )

        for widget, size in hiders:
            widget.setVisible(self.width() > utils.dpiScale(size))

        spacerThreshold = 120

        if self.width() < spacerThreshold:
            self.bottomBar.layout().setSpacing(0)
        else:
            self.bottomBar.layout().setSpacing(6)

    def updateWidgets(self):
        """ Update the text edits

        :return:
        :rtype:
        """
        self.widthEdit.blockSignals(True)
        self.heightEdit.blockSignals(True)
        self.widthEdit.setText(str(self.snapWidget.width()))
        self.heightEdit.setText(str(self.snapWidget.height()))
        self.setFocus()
        self.widthEdit.blockSignals(False)
        self.heightEdit.blockSignals(False)

    def showEvent(self, event):
        super(SnapshotUi, self).showEvent(event)

        if hasattr(self, "snapWidget"):
            self.setSnapshotSize(512, 512)
            self.updateUi()


class SnapshotFrame(QtWidgets.QFrame):
    """ For CSS Purposes"""
    pass
