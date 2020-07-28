from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt.widgets.graphics import graphicitems
from zoo.libs.pyqt.widgets.graphics import graphicspixmap


class GraphicsThumbnailWidget(QtWidgets.QGraphicsWidget):
    def __init__(self, pixmap, title="", parent=None):
        super(GraphicsThumbnailWidget, self).__init__(parent)
        self.selected = False
        self._size = QtCore.QSizeF()

        layout = QtWidgets.QGraphicsLinearLayout(QtCore.Qt.Vertical, self)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setContentsMargins(0, 0, 0, 0)

        self.pixmapWidget = graphicspixmap.GraphicsPixmapWidget(pixmap, self)
        self.labelWidget = graphicitems.TextContainer(title, self)

        layout.addItem(self.pixmapWidget)
        layout.addItem(self.labelWidget)

        layout.setAlignment(self.pixmapWidget, QtCore.Qt.AlignCenter)
        layout.setAlignment(self.labelWidget, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.setLayout(layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)

    def setPixmap(self, pixmap):
        self.pixmapWidget.setPixmap(pixmap)
        self._updatePixmapSize()

    def pixmap(self):
        return self.pixmapWidget.pixmap()

    def setThumbnailSize(self, size):
        if self._size != size:
            self._size = QtCore.QSizeF(size)
            self._updatePixmapSize()
            self.labelWidget.setTextWidth(max(100, size.width()))

    def setTitleWidth(self, width):
        self.labelWidget.setTextWidth(width)
        self.layout().invalidate()

    def paint(self, painter, option, widget=0):

        if not self.selected:
            return
        contents = self.contentsRect()
        painter.save()
        # temp
        painter.setPen(QtGui.QPen(QtGui.QColor(125, 162, 206, 192)))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(217, 232, 252, 192)))
        painter.drawRoundedRect(QtCore.QRectF(contents.topLeft(),
                                              self.geometry().size()), 3, 3)
        painter.restore()

    def _updatePixmapSize(self):
        pixmap = self.pixmap()
        if not pixmap.isNull() and self._size.isValid():
            pixsize = QtCore.QSizeF(self.pixmap().size())
            pixsize.scale(self._size, QtCore.Qt.KeepAspectRatio)
        else:
            pixsize = QtCore.QSizeF()
        self.pixmapWidget.setPixmapSize(pixsize)
