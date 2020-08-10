from Qt import QtWidgets, QtCore, QtGui


class GraphicsPixmapWidget(QtWidgets.QGraphicsWidget):
    def __init__(self, pixmapPath, parent=None):
        super(GraphicsPixmapWidget, self).__init__(parent)
        self.setCacheMode(self.ItemCoordinateCache)
        self._pixmap = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap(pixmapPath))
        self._pixmapSize = QtCore.QSizeF()
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def setPixmap(self, pixmap):
        if self._pixmap != pixmap:
            self._pixmap = QtGui.QPixmap(pixmap)
            self.updateGeometry()

    def pixmap(self):
        return QtGui.QPixmap(self._pixmap)

    def setPixmapSize(self, size):
        if self._pixmapSize != size:
            self._pixmapSize = QtCore.QSizeF(size)
            self.updateGeometry()

    def pixmapSize(self):
        if self._pixmapSize.isValid():
            return QtCore.QSizeF(self._pixmapSize)
        return QtCore.QSizeF(self._pixmap.pixmap().size())

    def sizeHint(self, which, constraint=QtCore.QSizeF()):
        if which == QtCore.Qt.PreferredSize:
            return self.pixmapSize()
        return super(GraphicsPixmapWidget, self).sizeHint(which, constraint)

    def paint(self, painter, option, widget=0):
        if self._pixmap.pixmap().isNull():
            return

        rect = self.contentsRect()

        pixsize = self.pixmapSize()
        pixrect = QtCore.QRectF(QtCore.QPointF(0, 0), pixsize)
        pixrect.moveCenter(rect.center())

        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 50), 3))
        painter.drawRoundedRect(pixrect, 2, 2)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        source = QtCore.QRectF(QtCore.QPointF(0, 0), QtCore.QSizeF(self._pixmap.pixmap().size()))
        painter.drawPixmap(pixrect, self._pixmap.pixmap(), source)
        painter.restore()
