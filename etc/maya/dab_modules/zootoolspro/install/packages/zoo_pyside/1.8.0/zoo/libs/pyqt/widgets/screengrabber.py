"""qt based screen grab transparent dialog, main mission here to allow the client to select a section of their
screen using a  rectangle which can be saved to a image file of their choosing.
"""

from Qt import QtCore, QtWidgets, QtGui


class ScreenGrabDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ScreenGrabDialog, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        # the resulting captured QRect
        self.thumbnailRect = QtCore.QRect()
        # the first click global position QPoint
        self._startPos = None
        self._opacity = 0.5
        self.backgroundColor = QtGui.QColor(60, 60, 60, self._opacity)
        self._cropColor = QtGui.QColor(255, 0, 0, 64)
        self.cropPen = QtGui.QPen(self._cropColor, 3, QtCore.Qt.DotLine)

    @property
    def cropColor(self):
        return self._cropColor

    @cropColor.setter
    def cropColor(self, color):
        self._cropColor = QtGui.QColor(*color)
        self.cropPen = QtGui.QPen(self._cropColor, 3, QtCore.Qt.DotLine)

    def getOpacity(self):
        return self._opacity

    def setOpacity(self, value):
        self._opacity = value
        self.repaint()

    opacity = QtCore.Property(int, getOpacity, setOpacity)

    def fitScreenGeometry(self):
        # Compute the union of all screen geometries, and resize to fit.
        desktop = QtWidgets.QApplication.instance().desktop()
        workspace_rect = QtCore.QRect()
        for i in range(desktop.screenCount()):
            workspace_rect = workspace_rect.united(desktop.screenGeometry(i))
        self.setGeometry(workspace_rect)

    def paintEvent(self, event):
        currentMousePos = self.mapFromGlobal(QtGui.QCursor.pos())
        clickPosition = self.mapFromGlobal(self._startPos) if self._startPos is not None else None
        painter = QtGui.QPainter(self)
        # monitor background color
        painter.setBrush(QtGui.QColor(self.backgroundColor.red(),
                                      self.backgroundColor.green(),
                                      self.backgroundColor.blue(),
                                      self._opacity))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(event.rect())

        if clickPosition is not None:
            rect = QtCore.QRect(clickPosition, currentMousePos)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            painter.drawRect(rect)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            painter.drawLine(event.rect().left(), clickPosition.y(),
                             event.rect().right(), clickPosition.y())
            painter.drawLine(clickPosition.x(), event.rect().top(),
                             clickPosition.x(), event.rect().bottom())

        painter.setPen(self.cropPen)

        painter.drawLine(event.rect().left(), currentMousePos.y(),
                         event.rect().right(), currentMousePos.y())
        painter.drawLine(currentMousePos.x(), event.rect().top(),
                         currentMousePos.x(), event.rect().bottom())

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._startPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self._startPos is not None:
            self.thumbnailRect = QtCore.QRect(self._startPos, event.globalPos()).normalized()
            self._startPos = None
        self.close()

    def mouseMoveEvent(self, event):
        self.repaint()

    def showEvent(self, event):
        self.fitScreenGeometry()
        # Start fade in animation for the screen opacity
        fade_anim = QtCore.QPropertyAnimation(self, "opacity", self)
        fade_anim.setStartValue(self.opacity)
        fade_anim.setEndValue(127)
        fade_anim.setDuration(250)
        fade_anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
