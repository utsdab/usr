from Qt import QtWidgets, QtCore, QtGui
from zoo.libs import iconlib


shadowPxSize = 128


class ShadowPixmap():

    _shadowpx = iconlib.icon("framelessshadow", size=shadowPxSize).pixmap(shadowPxSize, shadowPxSize)
    _cornerSize = 24
    _width = 50
    _height = 50

    def __init__(self, width=50, height=50):
        """ Creates a pixmap for a window with a shadow.

        :param width:
        :type width:
        :param height:
        :type height:
        """
        self._width = width
        self._height = height
        cs = self._cornerSize
        self._topLeftRect = QtCore.QRect(0, 0, cs, cs)
        self._topRightRect = QtCore.QRect(shadowPxSize - cs, 0, cs, cs)
        self._botLeftRect = QtCore.QRect(0, shadowPxSize - cs, cs, cs)
        self._botRightRect = QtCore.QRect(shadowPxSize - cs, shadowPxSize - cs, cs, cs)
        self._leftRect = QtCore.QRect(0, cs, cs, 1)
        self._rightRect = QtCore.QRect(shadowPxSize - cs, cs, cs, 1)
        self._topRect = QtCore.QRect(cs, 0, 1, cs)
        self._botRect = QtCore.QRect(cs, shadowPxSize - cs, 1, cs)


        self._topLeftPx = self._shadowpx.copy(self._topLeftRect)
        self._topRightPx = self._shadowpx.copy(self._topRightRect)
        self._botLeftPx = self._shadowpx.copy(self._botLeftRect)
        self._botRightPx = self._shadowpx.copy(self._botRightRect)
        self._leftPx = self._shadowpx.copy(self._leftRect)
        self._rightPx = self._shadowpx.copy(self._rightRect)
        self._topPx = self._shadowpx.copy(self._topRect)
        self._botPx = self._shadowpx.copy(self._botRect)

    def pixmap(self, width=None, height=None):
        width = max(width or self._width, 50)
        height = height or self._height
        height = max(height, 50)
        px = QtGui.QPixmap(width, height)
        cs = self._cornerSize

        pxWidth = max(0, width - (cs * 2))
        pxHeight = max(0, height - (cs * 2))

        px.fill(QtCore.Qt.black)

        # Stretch out the vertical and horizontal pixmaps
        leftPx = self._leftPx.scaled(cs, pxHeight)
        rightPx = self._rightPx.scaled(cs, pxHeight)
        botPx = self._botPx.scaled(pxWidth, cs)
        topPx = self._topPx.scaled(pxWidth, cs)

        # Draw it out
        painter = QtGui.QPainter(px)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        # Corners
        painter.drawPixmap(QtCore.QPoint(0,0), self._topLeftPx)
        painter.drawPixmap(QtCore.QPoint(width - cs, 0), self._topRightPx)
        painter.drawPixmap(QtCore.QPoint(0, height - cs), self._botLeftPx)
        painter.drawPixmap(QtCore.QPoint(width - cs, height - cs), self._botRightPx)

        # Sides
        painter.drawPixmap(QtCore.QPoint(0, cs), leftPx)
        painter.drawPixmap(QtCore.QPoint(width - cs, cs), rightPx)
        painter.drawPixmap(QtCore.QPoint(cs, 0), topPx)
        painter.drawPixmap(QtCore.QPoint(cs, height - cs), botPx)
        appRect = QtCore.QRect(10,10, width-32, height-32)
        painter.setPen(QtCore.Qt.black)
        painter.setBrush(QtCore.Qt.black)
        painter.drawRoundedRect(appRect, 1,1)
        painter.end()

        return px
