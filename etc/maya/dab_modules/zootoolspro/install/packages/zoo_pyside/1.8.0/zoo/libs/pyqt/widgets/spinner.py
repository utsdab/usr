import math
import time

from Qt import QtCore, QtGui, QtWidgets


class Spinner(QtWidgets.QWidget):
    """Classic widget which spins in a circle, useful for when loading operations happen
    """

    def __init__(self, size=(200, 200), parent=None):
        """
        :param size: The width and height of the widget
        :type size: tuple(int)
        :param parent: The parent widget
        :type parent: :class:`PySide2.QtGui.QWidget`
        """
        super(Spinner, self).__init__(parent)

        # public properties:
        self.fps = 20
        self.border = 2
        self.edgeWidth = 2
        self.length = 280
        self.secPerSpin = 4

        # to force repaint
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.onTimerOut)

        self._startAngle = 0
        self.setFixedSize(QtCore.QSize(*size))

    def paintEvent(self, event):
        super(Spinner, self).paintEvent(event)

        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # use the foreground colour to paint with:
        pen = QtGui.QPen(self.palette().color(self.foregroundRole()))
        pen.setWidth(self.edgeWidth)
        painter.setPen(pen)

        border = self.border + int(math.ceil(self.edgeWidth * 0.5))
        r = QtCore.QRect(0, 0, self.width(), self.height())
        r.adjust(border, border, -border, -border)

        # draw the arc:
        painter.drawArc(r, -self._startAngle * 16, self.length * 16)

        painter.end()

    def showEvent(self, event):
        """Called when the widget is being shown
        """
        if not self._timer.isActive():
            self._timer.start(1000 / max(1, self.fps))
        super(Spinner, self).showEvent(event)

    def hideEvent(self, event):
        """Called when the widget is being hidden
        """
        self._timer.stop()
        super(Spinner, self).hideEvent(event)

    def closeEvent(self, event):
        """Called when the widget is being closed - ensures the timer is stopped
        to avoid unnecessary painting
        """
        self._timer.stop()
        super(Spinner, self).closeEvent(event)

    def onTimerOut(self):
        """Triggered when the timer times out and used to trigger a repaint of
        the widget.
        """
        if not self.isVisible():
            return

        # calculate the spin angle as a function of the current time so that all
        t = time.time()
        whole_seconds = int(t)
        p = (whole_seconds % self.secPerSpin) + (t - whole_seconds)
        angle = int((360 * p) / self.secPerSpin)

        if angle == self._startAngle:
            return

        self._startAngle = angle
        self.update()
