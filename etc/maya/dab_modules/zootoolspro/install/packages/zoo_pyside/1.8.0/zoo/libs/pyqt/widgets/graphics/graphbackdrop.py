"""Mostly placeholder code until i get to doing the customisation
"""
from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt.widgets.graphics import graphicitems


class NodeHeader(QtWidgets.QGraphicsWidget):
    headerButtonStateChanged = QtCore.Signal(int)

    def __init__(self, node, text, parent=None):
        super(NodeHeader, self).__init__(parent)
        self._node = node
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))

        layout = QtWidgets.QGraphicsLinearLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setOrientation(QtCore.Qt.Horizontal)
        self.setLayout(layout)
        self._createLabel(text, layout)
        layout.addStretch(1)

    def _createLabel(self, primary, parentLayout):
        container = graphicitems.ItemContainer(QtCore.Qt.Vertical, parent=self)
        container.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self._titleWidget = graphicitems.GraphicsText(primary, self)
        self._titleWidget.setTextFlags(
            QtWidgets.QGraphicsItem.ItemIsSelectable & QtWidgets.QGraphicsItem.ItemIsFocusable &
            QtWidgets.QGraphicsItem.ItemIsMovable)
        self._titleWidget.font = QtGui.QFont("Roboto-Bold.ttf", 8)
        container.addItem(self._titleWidget, QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        parentLayout.addItem(container)

    def setText(self, text):
        self._titleWidget.setText(text)


#:todo include title and comment text
class BackDrop(QtWidgets.QGraphicsRectItem):
    handleTopLeft = 1
    handleTopRight = 2
    handleBottomLeft = 3
    handleBottomRight = 4

    handleSize = +8.0
    handleSpace = -4.0

    handleCursors = {
        handleTopLeft: QtCore.Qt.SizeFDiagCursor,
        handleTopRight: QtCore.Qt.SizeBDiagCursor,
        handleBottomLeft: QtCore.Qt.SizeBDiagCursor,
        handleBottomRight: QtCore.Qt.SizeFDiagCursor,
    }
    selectedColor = QtGui.QColor(25, 25, 25, 120)
    unSelectedColor = QtGui.QColor(25, 25, 25, 120)
    edgeColor = QtGui.QColor(0, 0, 0, 90)
    handleColor = QtGui.QColor(200, 200, 200, 200)
    headerColor = QtGui.QColor(100, 100, 100, 255)

    def __init__(self, x=0, y=0, width=120, height=60):
        """
        Initialize the shape.
        """
        super(BackDrop, self).__init__(x, y, width, height)
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.hovering = False
        self.headerBrush = QtGui.QBrush(self.headerColor)
        self.headerHeight = 30
        self.resizing = False

        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
        self.setZValue(-100)
        self.updateHandlesPos()


    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def hoverEnterEvent(self, event):
        super(BackDrop, self).hoverEnterEvent(event)
        self.hovering = True

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """

        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = QtCore.Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)

        super(BackDrop, self).hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.hovering = False
        self.setCursor(QtCore.Qt.ArrowCursor)
        super(BackDrop, self).hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()

        super(BackDrop, self).mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
            self.resizing = True
        else:
            super(BackDrop, self).mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        """
        super(BackDrop, self).mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        colliders = self.collidingItems(QtCore.Qt.IntersectsItemBoundingRect)
        sceneNodes = self.scene().nodes
        for item in colliders:
            if item not in sceneNodes:
                continue

            # skip if the item has a parent in which case the parent belongs to a backdrop
            parent = item.parentItem()
            if parent and isinstance(parent, BackDrop):
                continue
            item.setParentItem(self)
        self.resizing = False
        self.update()

    def boundingRect(self):
        """
        Returns the bounding rect of the shape (including the resize handles).
        """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft] = QtCore.QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopRight] = QtCore.QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleBottomLeft] = QtCore.QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QtCore.QRectF(b.right() - s, b.bottom() - s, s, s)

    def interactiveResize(self, mousePos):
        """
        Perform shape interactive resize.
        """
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()
        diff = QtCore.QPointF(0, 0)

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTopLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            rect.setX(mousePos.x())
            rect.setY(mousePos.y())
            self.setRect(rect)

        elif self.handleSelected == self.handleTopRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomLeft:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleBottomRight:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        self.updateHandlesPos()

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        """
        if self.isSelected():
            color = self.selectedColor
        else:
            color = self.unSelectedColor
        rect = self.boundingRect()
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtGui.QPen(self.edgeColor, 1.0, QtCore.Qt.SolidLine))
        painter.drawRect(rect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        topRect = QtCore.QRectF(rect.x(), rect.y(), rect.width(), self.headerHeight)
        painter.setBrush(self.headerBrush)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(topRect)

        if self.hovering:
            painter.setBrush(QtGui.QBrush(self.handleColor))
            painter.setPen(
                QtGui.QPen(self.edgeColor, 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)
