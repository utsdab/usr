import math
from Qt import QtWidgets, QtGui, QtCore
from zoo.libs.pyqt.widgets import layouts


class ItemContainer(QtWidgets.QGraphicsWidget):
    def __init__(self, orientation=QtCore.Qt.Vertical, parent=None):
        super(ItemContainer, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.setWindowFrameMargins(0, 0, 0, 0)
        if orientation == QtCore.Qt.Vertical:
            layout = layouts.vGraphicsLinearLayout(parent=self)
        else:
            layout = layouts.hGraphicsLinearLayout(parent=self)
        self._mainLayout = layout

    def count(self):
        return len(self._mainLayout.count())

    def items(self):
        layout = self.layout()
        for i in range(layout.count()):
            yield layout.itemAt(i)

    def addItem(self, item, alignment=None):
        """Adds a QWidget to the container layout
        :param item:
        """
        self.layout().addItem(item)
        if alignment:
            self.layout().setAlignment(item, alignment)

    def indexOf(self, item):
        layout = self.layout()
        for i in range(layout.count()):
            indexedItem = layout.itemAt(i)
            if indexedItem == item:
                return i
        return -1

    def insertItem(self, index, item, alignment=None):
        self.layout().insertItem(index, item)
        if alignment:
            self.layout().setAlignment(item, alignment)

    def clear(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            layout.removeItem(item)
            self.scene().removeItem(item)

    def removeItem(self, item):
        self.layout().removeItem(item)
        self.scene().removeItem(item)

    def removeItemAtIndex(self, index):
        """Adds a QWidget to the container layout

        """
        self.prepareGeometryChange()
        layout = self.layout()
        if index in range(self.layout().count()):
            item = layout.itemAt(index)
            layout.removeAt(index)
            self.scene.removeItem(item)


class TextContainer(QtWidgets.QGraphicsWidget):
    textChanged = QtCore.Signal(str)

    def __init__(self, text, *args, **kwargs):
        super(TextContainer, self).__init__(*args, **kwargs)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        layout = layouts.hGraphicsLinearLayout(parent=self)
        self.title = GraphicsText(text, parent=self)
        layout.addItem(self.title)
        layout.setAlignment(self.title, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    @property
    def text(self):
        return self._title

    @text.setter
    def text(self, title):
        self.title.text = title


class ConnectionEdge(QtWidgets.QGraphicsPathItem):
    """Class to deal with the Connection path between two plugs
    You set the style of the path with setLineStyle(QtCore.Qt.Style)
    """
    contextMenuRequested = QtCore.Signal(object)
    defaultColor = QtGui.QColor(138, 200, 0)
    selectedColor = QtGui.QColor(255, 255, 255)
    hoverColor = QtGui.QColor(255, 255, 255)
    CUBIC = 0
    LINEAR = 1

    def __init__(self, source, destination=None, curveType=CUBIC, colour=defaultColor):
        super(ConnectionEdge, self).__init__()
        self.setZValue(-1)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        self.curveType = curveType
        self._sourcePlug = source
        self._destinationPlug = destination
        self._sourcePoint = source.center()
        self._destinationPoint = destination.center() if destination is not None else None

        self.defaultPen = QtGui.QPen(colour, 1.25, style=QtCore.Qt.DashLine)
        self.defaultPen.setDashPattern([1, 2, 2, 1])
        self.selectedPen = QtGui.QPen(self.selectedColor, 1.7, style=QtCore.Qt.DashLine)
        self.selectedPen.setDashPattern([1, 2, 2, 1])

        self.hoverPen = QtGui.QPen(self.hoverColor, 1.7, style=QtCore.Qt.DashLine)
        self.selectedPen.setDashPattern([1, 2, 2, 1])
        self.hovering = False

        self.setPen(self.defaultPen)

        self.setCurveType(curveType)
        if destination is not None:
            self.updatePosition()

    def setWidth(self, width):
        lineWidth = width * 1.25
        self.defaultPen.setWidth(width)
        self.selectedPen.setWidth(lineWidth)
        self.hoverPen.setWidth(lineWidth)

    def setCurveType(self, cType):
        if cType == "Linear":
            self.setAsLinearPath()
        elif cType == "Cubic":
            self.setAsCubicPath()

    def setLineStyle(self, qStyle):

        self.defaultPen.setStyle(qStyle)
        self.selectedPen.setStyle(qStyle)
        self.hoverPen.setStyle(qStyle)

    def setAsLinearPath(self):
        path = QtGui.QPainterPath()
        path.moveTo(self._sourcePoint)
        path.lineTo(self._destinationPoint)
        self.curveType = ConnectionEdge.LINEAR
        self.setPath(path)

    def setAsCubicPath(self):
        path = QtGui.QPainterPath()

        path.moveTo(self._sourcePoint)
        dx = self._destinationPoint.x() - self._sourcePoint.x()
        dy = self._destinationPoint.y() - self._sourcePoint.y()
        ctrl1 = QtCore.QPointF(self._sourcePoint.x() + dx * 0.50, self._sourcePoint.y() + dy * 0.1)
        ctrl2 = QtCore.QPointF(self._sourcePoint.x() + dx * 0.50, self._sourcePoint.y() + dy * 0.9)
        path.cubicTo(ctrl1, ctrl2, self._destinationPoint)
        self.curveType = ConnectionEdge.CUBIC
        self.setPath(path)

    def hoverLeaveEvent(self, event):
        super(ConnectionEdge, self).hoverEnterEvent(event)
        self.hovering = False
        self.update()

    def hoverEnterEvent(self, event):
        super(ConnectionEdge, self).hoverEnterEvent(event)
        self.hovering = True
        self.update()

    def paint(self, painter, option, widget):

        if self.isSelected():
            painter.setPen(self.selectedPen)
        elif self.hovering:
            painter.setPen(self.hoverPen)
        else:
            painter.setPen(self.defaultPen)
        painter.drawPath(self.path())

    def updatePosition(self):
        """Update the position of the start and end of the edge
        """
        self._destinationPoint = self.destinationPlug.center()
        self._sourcePoint = self.sourcePlug.center()
        self.updatePath()

    def updatePath(self):
        if self.curveType == ConnectionEdge.CUBIC:
            self.setAsCubicPath()
        else:
            self.setAsLinearPath()

    def connect(self, src, dest):
        """Create a connection between the src plug and the destination plug
        :param src: Plug
        :param dest: Plug
        :return: None
        """
        if not src and dest:
            return
        self._sourcePlug = src
        self._destinationPlug = dest
        src.addConnection(self)
        dest.addConnection(self)

    def disconnect(self):
        """Remove the connection between the source and destination plug
        """
        self._sourcePlug.removeConnection(self)
        self._destinationPlug.removeConnection(self)
        self._sourcePlug = None
        self._destinationPlug = None

    @property
    def sourcePoint(self):
        """Return the source point
        :return: QtCore.QPointF()
        """
        return self._sourcePoint

    @sourcePoint.setter
    def sourcePoint(self, point):
        """Sets the source point and updates the path
        :param point: QtCore.QPointF
        """
        self._sourcePoint = point
        self.updatePath()

    @property
    def destinationPoint(self):
        """return the destination point
        :return: QtCore.QPointF
        """
        return self._destinationPoint

    @destinationPoint.setter
    def destinationPoint(self, point):
        """Sets the destination point and updates the path
        :param point: QtCore.QPointF
        """
        self._destinationPoint = point
        self.updatePath()

    @property
    def sourcePlug(self):
        """Return the source plug
        :return: Plug
        """
        return self._sourcePlug

    @sourcePlug.setter
    def sourcePlug(self, plug):
        """Sets the source plug and update the path
        :param plug: Plug
        """
        self._sourcePlug = plug
        self._sourcePoint = plug.center()
        self._sourcePlug.parentObject().connections.add(plug)
        self.updatePath()

    @property
    def destinationPlug(self):
        """Returns the destination plug
        :return: Plug
        """
        return self._destinationPlug

    @destinationPlug.setter
    def destinationPlug(self, plug):
        self._destinationPlug = plug
        self._destinationPoint = plug.center()
        self._destinationPlug.parentObject().connections.add(self)
        self.updatePath()

    def close(self):
        """
        """
        if self.scene() is not None:
            self.scene().removeItem(self)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            event.accept()
            if self.isSelected():
                self.setSelected(False)
            else:
                self.setSelected(True)

            self.update()
        self._destinationPoint = event.pos()

    def mouseMoveEvent(self, event):
        self._destinationPoint = self.mapToScene(event.pos())

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        self.contextMenuRequested.emit(menu)
        menu.exec_(event.scenePos())
        event.setAccepted(True)


class InteractiveEdge(ConnectionEdge):
    def __init__(self, source, destination=None, curveType=ConnectionEdge.CUBIC, colour=ConnectionEdge.defaultColor):
        super(InteractiveEdge, self).__init__(source, destination=destination, curveType=curveType, colour=colour)
        self.defaultBrush = QtGui.QBrush(colour)

    def paint(self, painter, option, widget):
        super(InteractiveEdge, self).paint(painter, option, widget)
        cen_x = self.path().pointAtPercent(0.5).x()
        cen_y = self.path().pointAtPercent(0.5).y()
        tgt_pt = self.path().pointAtPercent(1.0)
        dist = math.hypot(tgt_pt.x() - cen_x, tgt_pt.y() - cen_y)
        if dist < 0.10:
            return
        # draw circle
        size = 10.0
        if dist < 50.0:
            size *= (dist / 50.0)
        rect = QtCore.QRectF(cen_x - (size / 2), cen_y - (size / 2), size, size)
        painter.setBrush(self.defaultBrush)
        painter.setPen(self.defaultPen)
        painter.drawEllipse(rect)


class SelectionRect(QtWidgets.QGraphicsWidget):
    def __init__(self, mouseDownPos):
        super(SelectionRect, self).__init__()
        self.setZValue(100)
        self._color = QtGui.QColor(80, 80, 80, 50)
        self._pen = QtGui.QPen(QtGui.QColor(20, 20, 20), 1.0, QtCore.Qt.DashLine)
        self._mouseDownPos = mouseDownPos
        self.setPos(self._mouseDownPos)
        self.resize(0, 0)

    def setColor(self, color):
        self._color = color
        self.update()

    def setPen(self, pen):
        self._pen = pen
        self.update()

    def setStartPoint(self, point):
        self._mouseDownPos = point

    def setDragPoint(self, dragPoint):
        topLeft = QtCore.QPointF(self._mouseDownPos)
        bottomRight = QtCore.QPointF(dragPoint)
        xdown = self._mouseDownPos.x()
        ydown = self._mouseDownPos.y()
        if dragPoint.x() < xdown:
            topLeft.setX(dragPoint.x())
            bottomRight.setX(xdown)
        if dragPoint.y() < ydown:
            topLeft.setY(dragPoint.y())
            bottomRight.setY(ydown)
        self.setPos(topLeft)
        self.resize(bottomRight.x() - topLeft.x(), bottomRight.y() - topLeft.y())

    def paint(self, painter, option, widget):
        rect = self.windowFrameRect()
        painter.setBrush(self._color)
        painter.setPen(self._pen)
        painter.drawRect(rect)


class GraphicsText(QtWidgets.QGraphicsWidget):
    _font = QtGui.QFont("Roboto-Bold.ttf", 8)
    _font.setLetterSpacing(QtGui.QFont.PercentageSpacing, 110)
    _fontMetrics = QtGui.QFontMetrics(_font)
    textChanged = QtCore.Signal(str)
    _color = QtGui.QColor(200, 200, 200)

    def __init__(self, text, parent=None):
        super(GraphicsText, self).__init__(parent=parent)
        self._previousText = text
        self._item = QtWidgets.QGraphicsTextItem(text, parent=self)
        self._item.setDefaultTextColor(self._color)
        self._item.setFont(self._font)
        self._item.document().contentsChanged.connect(self.onTextChanged)
        self.setPreferredSize(self.size)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self._item.setFlags(QtWidgets.QGraphicsItem.ItemIsFocusable)
        self._item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        option = self._item.document().defaultTextOption()
        option.setWrapMode(QtGui.QTextOption.NoWrap)
        self._item.document().setDefaultTextOption(option)
        self.allowHoverHighlight = False
        self.setAcceptHoverEvents(True)
        self.adjustSize()

    def onTextChanged(self):
        newText = self._item.document().toPlainText()
        if newText != self._previousText:
            self._previousText = newText
            self.textChanged.emit(newText)

    def setTextFlags(self, flags):
        self._item.setFlags(flags)

    def setTextInteractionFlags(self, flags):
        self._item.setTextInteractionFlags(flags)

    @property
    def font(self):
        return self._item.font()

    @font.setter
    def font(self, value):
        return self._item.setFont(value)

    @property
    def text(self):
        return self._item.toPlainText()

    @text.setter
    def text(self, text):
        self._item.setPlainText(text)
        self._item.update()
        self.setPreferredSize(QtCore.QSizeF(self._item.textWidth(),
                                            self._font.pointSizeF() + 10))

    def onResize(self, width):
        fmWidth = self._fontMetrics.width(self.item.toPlainText())
        newWidth = min(fmWidth, width)
        if width > fmWidth:
            newWidth = width

        self._item.setTextWidth(newWidth)
        self.setPreferredSize(newWidth, self.textHeight())

    @property
    def size(self):
        return QtCore.QSizeF(self._item.textWidth(), self.height)

    @property
    def height(self):
        return self._item.document().documentLayout().documentSize().height() + 2

    @property
    def color(self):
        return self._item.defaultTextColor()

    @color.setter
    def color(self, color):
        self._item.setDefaultTextColor(color)
        self.update()

    def highlight(self):
        highlightColor = self.color.lighter(150)
        self.color = highlightColor

    def unhighlight(self):
        self.color = self._color

    def sizeHint(self, *args):
        return self._item.boundingRect().size()

    def boundingRect(self):
        return self._item.boundingRect()

    def hoverEnterEvent(self, event):
        if self.allowHoverHighlight:
            self.highlight()
        super(GraphicsText, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.allowHoverHighlight:
            self.unhighlight()
        super(GraphicsText, self).hoverLeaveEvent(event)
