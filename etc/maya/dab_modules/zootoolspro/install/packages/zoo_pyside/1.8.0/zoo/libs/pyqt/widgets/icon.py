from Qt import QtCore, QtGui


class Icon(QtGui.QIcon):
    def setColor(self, color, size=None):
        icon = self
        size = size or icon.actualSize(QtCore.QSize(256, 256))
        pixmap = icon.pixmap(size)
        rect = QtCore.QRect(0, 0, size.width(), size.height())
        if not self.isNull():
            painter = QtGui.QPainter(pixmap)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawRect(pixmap.rect())
            painter.end()
        icon = QtGui.QIcon(pixmap)
        self.swap(icon)