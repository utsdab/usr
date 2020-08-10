from Qt import QtWidgets, QtCore, QtGui
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import layouts
from zoo.preferences.core import preference


class ImageButton(QtWidgets.QPushButton):
    DEFAULT = 0
    HOVER = 1
    PRESSED = 2
    resized = QtCore.Signal()
    TEXTSPACE = utils.dpiScale(30)

    def __init__(self, parent=None, text="", image="save", icon="save", imageHeight=110, imageWidth=110, toolTip="",
                 square=True, iconCentered=True):
        """ An ImageButton

        :param parent:
        :param text:
        :param image:
        :param icon:
        """
        super(ImageButton, self).__init__(parent=parent)

        self.imageName = image
        self.iconName = icon
        self.labelIcon = QtWidgets.QLabel(parent=self)
        self.image = QtWidgets.QLabel(text)
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.buttonLabel = QtWidgets.QLabel(parent=self, text=text)
        self.mainLayout = layouts.vBoxLayout(margins=(0, 1, 0, 3))
        self.buttonLayout = layouts.hBoxLayout(margins=(3, 3, 3, 3))
        self._square = square
        self._iconCentered = iconCentered
        self._pressedColor = None
        self._iconColor = None
        self._imageButtonHover = None
        self.updateZooStyle()
        self.initUi()

        self._imagePixmap = None  # type: QtGui.QPixmap
        self._imagePixmapHover = None  # type: QtGui.QPixmap
        self._imagePixmapPressed = None  # type: QtGui.QPixmap
        self.setIconSize(QtCore.QSize(imageHeight, imageWidth))
        self.resizeEvent(QtGui.QResizeEvent(self.size(), self.size()))

        self.setToolTip(toolTip)

    def initUi(self):
        """ Initialize Ui

        :return:
        :rtype:
        """
        self.buttonLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.setLayout(self.mainLayout)

        if self._iconCentered:
            self.buttonLayout.addWidget(QtWidgets.QWidget())
            self.buttonLayout.addWidget(self.labelIcon)
            self.buttonLayout.addWidget(self.buttonLabel)
            self.buttonLayout.addWidget(QtWidgets.QWidget())
        else:
            self.buttonLayout.addWidget(self.labelIcon)
            self.buttonLayout.addWidget(self.buttonLabel)

        self.mainLayout.addWidget(self.image)
        self.mainLayout.addLayout(self.buttonLayout)

        self.mainLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumWidth(utils.dpiScale(32))

    def updateZooStyle(self):
        """ Update the zoo style

        :return:
        :rtype:
        """
        from zoo.preferences.core import preference
        themePref = preference.interface("core_interface")
        self._pressedColor = themePref.PRIMARY_COLOR
        self._iconColor = themePref.ICON_PRIMARY_COLOR
        self._imageButtonHover = themePref.IMAGEBUTTON_HOVER_COLOR

    def setIconSize(self, size):
        """ Set Icon Size

        :param size:
        :type size:
        :return:
        :rtype:
        """
        size = QtCore.QSize(size)


        themePref = preference.interface("core_interface")
        self._pressedColor = themePref.PRIMARY_COLOR
        self._iconColor = themePref.ICON_PRIMARY_COLOR
        self._imageButtonHover = themePref.IMAGEBUTTON_HOVER_COLOR
        # Image
        self._imagePixmap = iconlib.icon(self.imageName, size=size.width()).pixmap(size)
        self._imagePixmapHover = iconlib.iconColorizedLayered(self.imageName, size=size.width(),
                                                              tintColor=self._imageButtonHover,
                                                              tintComposition=QtGui.QPainter.CompositionMode_Multiply).pixmap(
            size)
        self._imagePixmapPressed = iconlib.iconColorizedLayered(self.imageName, size=size.width(),
                                                                tintColor=self._pressedColor).pixmap(size)
        self.updatePixmap()

        # Label Icon
        self.labelIcon.setPixmap(iconlib.iconColorizedLayered(self.iconName, size=utils.dpiScale(16), colors=self._iconColor).pixmap(
            utils.sizeByDpi(QtCore.QSize(16, 16))))
        self.labelIcon.setFixedSize(self.labelIcon.sizeHint())

    def resizeEvent(self, event):
        """ Resize Event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        super(ImageButton, self).resizeEvent(event)
        self.updatePixmap()
        self.image.setFixedSize(self.image.pixmap().size())
        if self._square:
            self.setFixedHeight(event.size().width() + self.TEXTSPACE)
        else:
            self.setFixedHeight(self.image.pixmap().size().height() + self.TEXTSPACE)

        self.mainLayout.setSpacing(event.size().width()*0.1)

    def sizeHint(self):
        """ Size Hint

        :return:
        :rtype:
        """
        sh = super(ImageButton, self).sizeHint()
        return QtCore.QSize(sh.width(), sh.width()+utils.dpiScale(30))

    def enterEvent(self, event):
        """ Enter Event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        super(ImageButton, self).enterEvent(event)
        self.updatePixmap(ImageButton.HOVER)

    def leaveEvent(self, event):
        """ Leave Event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        super(ImageButton, self).leaveEvent(event)
        self.updatePixmap()

    def mousePressEvent(self, event):
        """ Mouse Press event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        super(ImageButton, self).mousePressEvent(event)
        self.updatePixmap(ImageButton.PRESSED)

    def mouseReleaseEvent(self, event):
        """ Mouse Release Event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        super(ImageButton, self).mouseReleaseEvent(event)

        if self.underMouse():
            self.updatePixmap(ImageButton.HOVER)
        else:
            self.updatePixmap(ImageButton.DEFAULT)

    def updatePixmap(self, pixType=DEFAULT):
        """ Update Pixmap

        :param pixType:
        :type pixType:
        :return:
        :rtype:
        """
        size = self.size()
        if pixType == ImageButton.DEFAULT:
            self.image.setPixmap(self._imagePixmap.scaledToWidth(size.width() - utils.dpiScale(1), QtCore.Qt.SmoothTransformation))
        elif pixType == ImageButton.HOVER:
            self.image.setPixmap(
                self._imagePixmapHover.scaledToWidth(size.width() - utils.dpiScale(1), QtCore.Qt.SmoothTransformation))
        elif pixType == ImageButton.PRESSED:
            self.image.setPixmap(
                self._imagePixmapPressed.scaledToWidth(size.width() - utils.dpiScale(1), QtCore.Qt.SmoothTransformation))