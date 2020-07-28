from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt.extended import searchablemenu
ZOOM_MIN = -0.95
ZOOM_MAX = 2.0


class GraphicsView(QtWidgets.QGraphicsView):
    contextMenuRequest = QtCore.Signal(object, object, object)
    # emitted whenever an event happens that requires the view to update
    updateRequested = QtCore.Signal()
    tabPress = QtCore.Signal(object)
    deletePress = QtCore.Signal(list)

    def __init__(self, config, parent=None, setAntialiasing=True):
        super(GraphicsView, self).__init__(parent)
        self.resize(850, 800)

        # apply default settings
        self.setAntialiasing(setAntialiasing)
        self.setCacheMode(self.CacheBackground)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        self.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        self.setRenderHint(QtGui.QPainter.NonCosmeticDefaultPen, True)

        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setInteractive(True)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenu)

        self.config = config
        self._scene_range = QtCore.QRectF(-(self.width()*0.5), -(self.height()*0.5), self.size().width(), self.size().height())
        self._rubber_band = QtWidgets.QRubberBand(
            QtWidgets.QRubberBand.Rectangle, self
        )

        self.pan_active = False
        self.previousMousePos = QtCore.QPoint(self.width(), self.height())
        self._last_size = self.size()

        self._update_scene()

    def getCurrentZoom(self):
        transform = self.transform()
        return float('{:0.2f}'.format(transform.m11() - 1.0))

    def centerPosition(self):
        return self.mapToScene(QtCore.QPoint(self.width() * 0.5, self.height() * 0.5))

    def setAntialiasing(self, aa):
        """ enables or disables antialiaising

        :param aa : bool
        @note This will not effect items that specify their own antialiasing
        """
        if aa:
            self.setRenderHints(self.renderHints() | QtGui.QPainter.Antialiasing)
            return
        self.setRenderHints(self.renderHints() & ~QtGui.QPainter.Antialiasing)

    def _setViewerPan(self, pos_x, pos_y):
        speed = self._scene_range.width() * 0.0015
        x = -pos_x * speed
        y = -pos_y * speed
        self._scene_range.adjust(x, y, x, y)
        self._update_scene()

    def _setZoom(self, value, sensitivity=None, position=None):
        if position:
            position = self.mapToScene(position)
        if sensitivity is None:
            scale = 1.001 ** value
            self.scale(scale, scale, position)
            return

        if value == 0.0:
            return
        scale = (0.9 + sensitivity) if value < 0.0 else (1.1 - sensitivity)
        zoom = self.get_zoom()
        if ZOOM_MIN >= zoom:
            if scale == 0.9:
                return
        if ZOOM_MAX <= zoom:
            if scale == 1.1:
                return
        self.scale(scale, scale, position)

    def scale(self, sx, sy, pos=None):
        scale = [sx, sx]

        center = pos or self._scene_range.center()

        w = self._scene_range.width() / scale[0]
        h = self._scene_range.height() / scale[1]
        self._scene_range = QtCore.QRectF(center.x() - (center.x() - self._scene_range.left()) / scale[0],
                                          center.y() - (center.y() - self._scene_range.top()) / scale[1], w, h)

        self._update_scene()

    def _update_scene(self):
        self.setSceneRect(self._scene_range)
        self.fitInView(self._scene_range, QtCore.Qt.KeepAspectRatio)

    # EVENTS
    def wheelEvent(self, event):
        try:
            delta = event.delta()
        except AttributeError:
            delta = event.angleDelta().y()
            if delta == 0:
                delta = event.angleDelta().x()
        self._setZoom(delta, position=event.pos())

    def resizeEvent(self, event):
        delta = max(self.size().width() / self._last_size.width(),
                    self.size().height() / self._last_size.height())
        self._setZoom(delta)
        self._last_size = self.size()
        super(GraphicsView, self).resizeEvent(event)

    def mousePressEvent(self, event):
        button = event.buttons()
        self._origin_pos = event.pos()
        self.previousMousePos = event.pos()
        item = self.itemAt(event.pos())

        if button == QtCore.Qt.LeftButton and not self.scene().selectedItems() and not item:
            rect = QtCore.QRect(self.previousMousePos, QtCore.QSize())
            rect = rect.normalized()
            map_rect = self.mapToScene(rect).boundingRect()
            self.scene().update(map_rect)
            self._rubber_band.setGeometry(rect)
            self._rubber_band.show()

        elif event.button() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.AltModifier:
            self.pan_active = True
            self.setCursor(QtCore.Qt.OpenHandCursor)

        elif button == QtCore.Qt.RightButton:
            self._contextMenu(event.pos())

        super(GraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.pan_active:
            pos_x = event.x() - self.previousMousePos.x()
            pos_y = event.y() - self.previousMousePos.y()
            self._setViewerPan(pos_x, pos_y)

        if self._rubber_band.isVisible():
            rect = QtCore.QRect(self._origin_pos, event.pos()).normalized()
            map_rect = self.mapToScene(rect).boundingRect()
            path = QtGui.QPainterPath()
            path.addRect(map_rect)
            self._rubber_band.setGeometry(rect)
            self.scene().setSelectionArea(path, QtCore.Qt.IntersectsItemShape)
            self.scene().update(map_rect)
        self.previousMousePos = event.pos()
        super(GraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.pan_active:
            self.pan_active = False
            self.setCursor(QtCore.Qt.ArrowCursor)
        # hide selection marquee
        if self._rubber_band.isVisible():
            rect = self._rubber_band.rect()
            map_rect = self.mapToScene(rect).boundingRect()
            self._rubber_band.hide()
            self.scene().update(map_rect)
        super(GraphicsView, self).mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Tab and event.modifiers() == QtCore.Qt.ControlModifier:
            self.tabPress.emit(QtGui.QCursor.pos())
        elif key == QtCore.Qt.Key_Delete:
            self.deletePress.emit(self.scene().selectedItems())
        super(GraphicsView, self).keyPressEvent(event)

    def frameSelectedItems(self):
        selection = self.scene().selectedItems()
        if selection:
            rect = self._getItemsBoundingBox(selection)
        else:
            rect = self.scene().itemsBoundingRect()
        self.fitInView(rect, QtCore.Qt.KeepAspectRatio)

    def _getItemsBoundingBox(self, items):
        bbx = set()
        bby = set()

        for item in items:
            pos = item.scenePos()
            rect = item.boundingRect()
            x, y, = pos.x(), pos.y()
            bbx.add(x)
            bby.add(y)
            bbx.add(x + rect.width())
            bby.add(y + rect.height())

        bbxMax = max(bbx)
        bbxMin = min(bbx)
        bbyMin = min(bby)
        bbyMax = max(bby)
        return QtCore.QRectF(QtCore.QRect(bbxMin, bbyMin, bbxMax - bbxMin, bbyMax - bbyMin))

    def frameSceneItems(self):
        itemsArea = self.scene().itemsBoundingRect()
        self.fitInView(itemsArea, QtCore.Qt.KeepAspectRatio)

    def getViewRect(self):
        """Return the boundaries of the view in scene coordinates"""
        r = QtCore.QRectF(self.rect())
        return self.viewportTransform().inverted()[0].mapRect(r)

    def _contextMenu(self, pos):
        menu = searchablemenu.SearchableMenu(objectName=self.objectName()+"|graphicsMenu")
        item = self.itemAt(pos)
        self.contextMenuRequest.emit(menu, item, pos)
        if menu.isEmpty():
            return
        menu.exec_(self.mapToGlobal(pos))

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, self.config.graphBackgroundColor)
        if not self.config.drawGrid:
            return super(GraphicsView, self).drawBackground(painter, rect)
        self._drawSubdivisionGrid(painter, rect)
        # main axis
        if self.config.drawMainGridAxis:
            self._drawMainAxis(painter, rect)
        return super(GraphicsView, self).drawBackground(painter, rect)

    def _drawSubdivisionGrid(self, painter, rect):
        left = int(rect.left()) - (int(rect.left()) % self.config.gridSize)
        top = int(rect.top()) - (int(rect.top()) % self.config.gridSize)
        # Draw horizontal fine lines
        gridLines = []
        painter.setPen(self.config.gridColor)
        y = float(top)
        while y < float(rect.bottom()):
            gridLines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
            y += self.config.gridSize
        painter.drawLines(gridLines)

        # Draw vertical fine lines
        gridLines = []
        painter.setPen(self.config.gridColor)
        x = float(left)
        while x < float(rect.right()):
            gridLines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
            x += self.config.gridSize
        painter.drawLines(gridLines)

    def _drawMainAxis(self, painter, rect):

        painter.setPen(self.config.overlayAxisPen)

        xLine, yLine = QtCore.QLineF(), QtCore.QLineF()
        if rect.y() < 0 < (rect.height() - rect.y()):
            xLine = QtCore.QLineF(rect.x(), 0, rect.width() + rect.x(), 0)

        if rect.x() < 0 < (rect.height() - rect.x()):
            yLine = QtCore.QLineF(0, rect.y(), 0, rect.height() + rect.y())

        painter.drawLines([xLine, yLine])
