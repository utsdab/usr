from Qt import QtWidgets, QtCore
from zoo.libs import iconlib
from zoo.libs.pyqt.widgets import screengrabber
from zoo.libs.pyqt import utils


class ThumbnailWidget(QtWidgets.QFrame):
    # triggered just before the snap shot begins, use this to hide the top level window
    preSnapshotTriggered = QtCore.Signal()
    postSnapshotTriggered = QtCore.Signal()

    def __init__(self, parent=None):
        super(ThumbnailWidget, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self._initUi()
        self._thumbnail = None

    def _initUi(self):
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)
        topSpacer = QtWidgets.QSpacerItem(20, 52, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        bottomSpacer = QtWidgets.QSpacerItem(20, 52, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        leftSpacer = QtWidgets.QSpacerItem(20, 52, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        rightSpacer = QtWidgets.QSpacerItem(20, 52, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # label to hold the thumbnail image
        self.imageLabel = QtWidgets.QLabel(parent=self)
        self.imageLabel.hide()
        # camera icon
        self.iconLayout = QtWidgets.QHBoxLayout()
        self.cameraBtn = _CameraButton(parent=self)
        self.iconLayout.addItem(leftSpacer)
        self.iconLayout.addWidget(self.cameraBtn)
        self.iconLayout.addItem(rightSpacer)
        # add the items
        self.mainLayout.addItem(topSpacer)
        self.mainLayout.addLayout(self.iconLayout)
        self.mainLayout.addItem(bottomSpacer)

        self.cameraBtn.clicked.connect(self.onCameraButtonClicked)

    @property
    def thumbnail(self):
        return self._thumbnail

    @thumbnail.setter
    def thumbnail(self, pixmap):
        self._thumbnail = pixmap
        self.imageLabel.setPixmap(pixmap)
        self.updateImage()

    def onCameraButtonClicked(self):
        self.preSnapshotTriggered.emit()
        grabber = screengrabber.ScreenGrabDialog()
        grabber.exec_()
        pixmap = utils.desktopPixmapFromRect(grabber.thumbnailRect)
        self.postSnapshotTriggered.emit()
        if pixmap:
            self.thumbnail = pixmap

    def updateImage(self):
        # get this instance geometry
        geo = self.geometry()
        pixmap = self.thumbnail
        if not pixmap:
            return
        geo.moveTo(0, 0)
        width = geo.width()
        height = geo.height()

        pixmapSize = pixmap.size()
        pmHeight = pixmapSize.height()
        pmWidth = pixmapSize.width()
        h_scale = float(height) / float(pmHeight)
        w_scale = float(width) / float(pmWidth)
        scale = min(1.0, h_scale, w_scale)
        scale_contents = (scale < 1.0)

        new_height = min(int(pmHeight * scale), height)
        new_width = min(int(pmWidth * scale), width)

        new_geom = QtCore.QRect(geo)
        new_geom.moveLeft((width * 0.5 - new_width * 0.5))
        new_geom.moveTop((height * 0.5 - new_height * 0.5))
        new_geom.setWidth(new_width)
        new_geom.setHeight(new_height)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.setScaledContents(scale_contents)
        self.imageLabel.setGeometry(new_geom)
        self.imageLabel.show()


class _CameraButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(_CameraButton, self).__init__(parent)
        self.setStyleSheet("background-color: rgba( 0, 0, 0, 0 );border: none;")
        self.enterIcon = iconlib.icon("cameraSolid")
        self.leaveIcon = iconlib.icon("cameraBorder")
        self.setMaximumSize(QtCore.QSize(999999, 9999999))
        self.setIcon(self.leaveIcon)

    def enterEvent(self, event):
        self.setIcon(self.enterIcon)
        super(_CameraButton, self).enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self.leaveIcon)
        super(_CameraButton, self).leaveEvent(event)
