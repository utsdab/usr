from Qt import QtCore, QtGui, QtWidgets
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dpiscaling


class SearchLineEdit(QtWidgets.QLineEdit, dpiscaling.DPIScaling):
    """Search Widget with two icons one on either side, inherits from QLineEdit
    """
    textCleared = QtCore.Signal()

    def __init__(self, searchPixmap=None, clearPixmap=None, parent=None, iconsEnabled=True):
        self._iconsEnabled = iconsEnabled

        QtWidgets.QLineEdit.__init__(self, parent)

        if searchPixmap is None:
            searchPixmap = iconlib.iconColorized("magnifier", utils.dpiScale(16), (128, 128, 128))  # these should be in layouts

        if clearPixmap is None:
            clearPixmap = iconlib.iconColorized("close", utils.dpiScale(16), (128, 128, 128))

        self.clearButton = QtWidgets.QToolButton(self)
        self.clearButton.setIcon(QtGui.QIcon(clearPixmap))

        self.searchButton = QtWidgets.QToolButton(self)
        self.searchButton.setIcon(QtGui.QIcon(searchPixmap))
        self._backgroundColor = None
        self.initUi()

    def initUi(self):

        self.clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self.clearButton.setStyleSheet("QToolButton { border: none; padding: 1px; }")
        self.clearButton.hide()
        self.clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self.updateCloseButton)

        self.searchButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")

        self.setIconsEnabled(self._iconsEnabled)

    def setBackgroundColor(self, col):
        self._backgroundColor = col
        self.setIconsEnabled(self._iconsEnabled)

    def setIconsEnabled(self, enabled):

        if self._iconsEnabled:
            frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
            self.updateStyleSheet()
            msz = self.minimumSizeHint()
            self.setMinimumSize(max(msz.width(),
                                    self.searchButton.sizeHint().width() +
                                    self.clearButton.sizeHint().width() + frameWidth * 2 + 2),
                                max(msz.height(),
                                    self.clearButton.sizeHint().height() + frameWidth * 2 + 2))

        else:
            self.searchButton.hide()
            self.clearButton.hide()

            self.setStyleSheet("")

        self._iconsEnabled = enabled

    def updateStyleSheet(self):
        backgroundStyle = "background-color: rgb{}".format(
            str(tuple(self._backgroundColor))) if self._backgroundColor is not None else ""

        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)

        if self.height() < utils.dpiScale(25):
            topPad = 0  # todo: could do this part better
        else:
            topPad = -2 if utils.dpiMult() == 1.0 else 0
        self.setStyleSheet("QLineEdit {{ padding-left: {}px; padding-right: {}px; {}; padding-top: {}px; }} ".
                           format(self.searchButton.sizeHint().width() + frameWidth + utils.dpiScale(1),
                                  self.clearButton.sizeHint().width() + frameWidth + utils.dpiScale(1),
                                  backgroundStyle,
                                  topPad))

    def resizeEvent(self, event):
        if self._iconsEnabled:
            sz = self.clearButton.sizeHint()
            frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
            rect = self.rect()
            yPos = abs(rect.bottom() - sz.height()) * 0.5 + utils.dpiScale(1)
            self.clearButton.move(self.rect().right() - frameWidth - sz.width(), yPos-2)
            self.searchButton.move(self.rect().left() + utils.dpiScale(1), yPos)
            self.updateStyleSheet()


    def updateCloseButton(self, text):
        if text and self._iconsEnabled:
            self.clearButton.setVisible(True)
            return
        self.clearButton.setVisible(False)


if __name__ == "__name__":
    app = QtWidgets.QApplication([])
    searchIcon = QtGui.QPixmap(iconlib.icon("magnifier"), 16)
    closeIcon = QtGui.QPixmap(iconlib.icon("code", 16))
    w = SearchLineEdit(searchIcon, closeIcon)
    w.show()
    app.exec_()
