from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended.imageview import model
from zoo.libs.pyqt.extended.imageview.models import filemodel
from zoo.libs.pyqt.widgets import listview


class ThumbScrollBar(QtWidgets.QScrollBar):
    def __init__(self, parent=None):
        super(ThumbScrollBar, self).__init__(parent)


class ThumbnailWidget(listview.ListView):

    requestZoom = QtCore.Signal(object, float)
    # QModelIndex, Treeitem
    requestDoubleClick = QtCore.Signal(object, object)
    zoomAmount = 1
    defaultMinIconSize = 20
    defaultMaxIconSize = 512
    defaultIconSize = QtCore.QSize(256, 256)
    stateChanged = QtCore.Signal()
    requestSelectionChanged = QtCore.Signal(object, object)

    WheelEvent = 1
    EnterEvent = 2
    CalcInitialEvent = 3
    CalcEvent = 4
    VerticalSliderReleasedEvent = 5

    def __init__(self, parent=None, delegate=None, iconSize=defaultIconSize, uniformIcons=False):
        self.autoScale = True
        self.defaultSize = None
        self.initialIconSize = None
        self.columnQueue = 0
        self.columnOffset = 1
        super(ThumbnailWidget, self).__init__(parent=parent)

        self.zoomable = True
        self.pagination = True
        self._iconSize = QtCore.QSize()
        self.setIconSize(iconSize or self.defaultIconSize)
        self.initUi()

        self.maxColumns = 8
        self.setVerticalScrollBar(ThumbScrollBar(self))
        self.connections()

        self._delegate = delegate(self) if delegate is not None else model.ThumbnailDelegate(self)
        self.setItemDelegate(self._delegate)
        self.setUpdatesEnabled(True)
        self._uniformIcons = uniformIcons
        self.setUniformItemSizes(uniformIcons)

    def initUi(self):
        self.setMouseTracking(True)
        self.setSelectionRectVisible(True)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setDragEnabled(False)
        self.setAcceptDrops(False)

    def setVerticalScrollBar(self, scrollbar):
        ret = super(ThumbnailWidget, self).setVerticalScrollBar(scrollbar)
        self.verticalScrollBar().valueChanged.connect(self.paginationLoadNextItems)
        return ret

    def setUniformItemSizes(self, enable):
        self._uniformIcons = enable
        if self.model():
            self.model().setUniformItemSizes(enable)

    def setIconSize(self, size):

        if size == self.iconSize():
            return
        maxSize = self.defaultMaxIconSize
        minSize = self.defaultMinIconSize
        width = size.width()
        height = size.height()
        if width > maxSize or height > maxSize:
            size = QtCore.QSize(maxSize, maxSize)
        elif width < minSize or height < minSize:
            size = QtCore.QSize(minSize, minSize)

        self._iconSize = size
        super(ThumbnailWidget, self).setIconSize(size)


    def connections(self):
        self.verticalScrollBar().sliderMoved.connect(self.verticalSliderMoved)
        self.verticalScrollBar().sliderReleased.connect(self.verticalSliderReleased)
        self.clicked.connect(lambda: self.stateChanged.emit())
        self.activated.connect(lambda: self.stateChanged.emit())
        # self.entered.connect(lambda: self.stateChanged.emit())

    def wheelEvent(self, event):
        """ Overridden to deal with scaling the listview.

        :type event: :class:`QEvent`
        """
        modifiers = event.modifiers()
        if self.zoomable and modifiers == QtCore.Qt.ControlModifier:
            if event.delta() > 0:
                self.columnOffset -= 1
            else:
                self.columnOffset += 1
                self.columnOffset = min(self.columnOffset, self.maxColumns)

            size = self.widgetSize()
            index = self.indexAt(event.pos())

            # if its an invalid index, find closest instead
            if not index.isValid():
                index = self.closestIndex(event.pos())

            self.calcResize(size)
            QtCore.QTimer.singleShot(0, lambda: self.scrollTo(index))
            event.accept()
            self.stateChanged.emit()
            return
        super(ThumbnailWidget, self).wheelEvent(event)
        self.loadVisibleIcons()
        self.stateChanged.emit()
        self.refresh()

    def state(self):
        """ Returns useful settings to copy from one list view behaviour to another

        :return:
        :rtype:
        """
        selectedIndex = self.currentIndexInt()
        ret = {"sliderPos": self.verticalScrollBar().value(),
               "sliderMin": self.verticalScrollBar().minimum(),
               "sliderMax": self.verticalScrollBar().maximum(),
               "selected": selectedIndex,
               "columns": self.columnOffset,
               "zoomAmount": self.zoomAmount,
               "iconSize": self._iconSize,
               "initialIconSize": self.initialIconSize,
               "defaultSize": self.defaultSize,
               "fixedSize": self.parentWidget().minimumSize()
               }

        return ret

    def currentIndexInt(self):
        """ Get the current index of the selected item

        :return:
        :rtype:
        """
        return self.currentIndex().row()

    def setState(self, state, scrollTo=False):
        """ Set the state of the listview with the new settings provided from ThumbListView.state()

        :param state:
        :type state:
        :return:
        :rtype:
        """
        self.columnOffset = state['columns']
        self._iconSize = state['iconSize']
        self.zoomAmount = state['zoomAmount']
        self.defaultSize = state['defaultSize']
        self.initialIconSize = state['initialIconSize']

        fixedSize = state['fixedSize']

        if fixedSize.width() != 0:
            self.parentWidget().setFixedWidth(fixedSize.width())
        if fixedSize.height() != 0:
            self.parentWidget().setFixedHeight(fixedSize.height())

        self.calcResize(self.widgetSize())
        self.verticalScrollBar().setMinimum(state['sliderMin'])
        self.verticalScrollBar().setMaximum(state['sliderMax'])
        self.verticalScrollBar().setValue(state['sliderPos'])

        self.loadVisibleIcons()

        if state['selected'] != -1:
            QtCore.QTimer.singleShot(0, lambda: self.setCurrentIndexInt(state['selected'], scrollTo))


    def setCurrentIndexInt(self, sel, scrollTo=False):
        """ Select index

        :param sel:
        :type sel: int
        :return:
        :rtype:
        """
        autoScroll = self.hasAutoScroll()
        self.setAutoScroll(scrollTo)
        self.selectionModel().setCurrentIndex(self.model().index(sel, 0),
                                              QtCore.QItemSelectionModel.ClearAndSelect)
        self.setAutoScroll(autoScroll)

    def closestIndex(self, pos):
        """ Get closest index based on pos

        :param pos:
        :type pos:
        :return:
        :rtype:
        """
        maxDist = -1
        closest = None
        for index in self.visibleItems():
            c = self.visualRect(index)
            if c.top() <= pos.y() <= c.bottom():  # Only choose the ones from the same row
                dist = pos.x() - c.center().x()
                if maxDist == -1 or dist < maxDist:
                    closest = index
                    maxDist = dist
        return closest

    def loadVisibleIcons(self):
        """ Loads visible icons in the view if they have not been loaded yet

        :return:
        :rtype:
        """

        for index in self.visibleItems(pre=5, post=5):
            try:
                treeItem = self.model().items[index.row()]
                item = treeItem.item()
                if not item.iconLoaded():
                    self.model().threadPool.start(item.iconThread)

            except IndexError:
                pass  # this should possibly be handled

    def filter(self, text, tag=None):
        filterList = self.model().filterList(text, tag)
        self.loadVisibleIcons()

    def verticalSliderReleased(self):
        self.stateChanged.emit()

    def verticalSliderMoved(self, pos):
        """ On vertical slider moved, reload the visible icons

        :return:
        :rtype:
        """
        self.loadVisibleIcons()

    def model(self):
        """ Get ListView model

        :return:
        :rtype: filemodel.FileViewModel
        """

        return super(ThumbnailWidget, self).model()

    def visibleItems(self, pre=0, post=0):
        """ Gets visible items

        Set extra to 1 or more if you want extra indices at the beginning and at the end. It will only return
        valid indices.

        :param pre: Add extra items behind the currently visible items
        :type pre: int
        :param post: Add extra items after the currently visible items
        :type post: int
        :return: List of indices that are visible plus the pre and post. It only returns valid indices
        :rtype: list of QtCore.QModelIndex
        """
        firstIndex = self.indexAt(QtCore.QPoint(0, 0))
        viewportRect = self.viewport().rect()
        items = list()
        after = post

        i = -pre  # We want to check indices behind the firstIndex
        while True:
            sibling = firstIndex.sibling(firstIndex.row() + i, 0)
            # The index is visually shown in the viewport?
            if sibling.isValid() and viewportRect.intersects(self.visualRect(sibling)):
                items.append(sibling)
            elif sibling.isValid() and i < 0:  # If it's indices behind the firstIndex
                items.append(sibling)
            elif sibling.isValid() and after > 0:  # We want some extra indices at the end so keep going
                after -= 1
                items.append(sibling)
            elif i < 0 or self.isIndexHidden(sibling):  # We want to keep going even if the behind siblings are invalid,
                # Or hidden by search
                i += 1
                continue

            else:
                break  # Either it is invalid (reached the end) or we've gone outside the screen
            i += 1

        return items

    def setItemByText(self, text):
        """ Set the item by the text of the item

        :param text:
        :type text:
        :return:
        :rtype:
        """
        for it in self.model().items:
            if text == it.itemText():
                self.setCurrentIndex(it.index())
                return

    def scrollTo(self, index, hint=None):
        """ Override default scrollTo and use our own

        :param index:
        :type index:
        :return:
        :rtype:
        """
        if hint is None:
            itemRect = self.rectForIndex(index)
            vbar = self.verticalScrollBar()
            mPos = self.mapFromGlobal(QtGui.QCursor().pos())  # Pos of mouse in listview widget
            newPos = (float(itemRect.y()) / float(self.contentsSize().height())) * \
                     (float(self.contentsSize().height())) - \
                     mPos.y() + \
                     (itemRect.height()*0.5)  # maybe better if this is the mousePosition relative to the item instead

            vbar.setValue(newPos)
        else:
            super(ThumbnailWidget, self).scrollTo(index, hint)

        self.loadVisibleIcons()

    def widgetSize(self):
        """ Size without the vertical scrollbar

        :return:
        :rtype:
        """
        size = QtCore.QSize(self.size())
        size -= QtCore.QSize(self.verticalScrollBar().size().width(), 0)
        return size

    def _calculateZoom(self, delta):
        """ Calculation of the zoom factor before applying it to the icons via the ::func:`setZoomAmount`

        :param delta: the delta value
        :type delta: float
        :return: the converted delta to zoom factor
        :rtype: float
        """
        inFactor = 1.15
        outFactor = 1 / inFactor

        if delta > 0:
            zoomFactor = inFactor
        else:
            zoomFactor = outFactor
        self.zoomAmount = zoomFactor
        return zoomFactor

    def setZoomAmount(self, value):
        """ Sets the zoom amount to this view by taking the view iconSize()*value

        :param value:
        :type value:
        :return:
        :rtype:
        """
        currentSize = QtCore.QSize(self.initialIconSize)
        newSize = currentSize.width() * value
        if newSize < self.defaultMinIconSize:
            return
        currentSize.setWidth(newSize)
        currentSize.setHeight(newSize)
        self.requestZoom.emit(newSize, self.zoomAmount)
        self.setIconSize(currentSize)

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            index = self.currentIndex()
            model = self.model()
            if model is not None:
                item = model.itemFromIndex(index)
                model.doubleClickEvent(index, item)
                self.requestDoubleClick.emit(index, item)

    def resizeEvent(self, event):
        self.calcResize(event.size())

        super(ThumbnailWidget, self).resizeEvent(event)
        self.loadVisibleIcons()

    def setColumns(self, col):
        """ Set number of columns based on current size of the widget

        :param col:
        :type col:
        :return:
        :rtype:
        """

        self.setIconSize(self.defaultIconSize)

        # Sets columns on next calcResize
        self.columnQueue = col

        # Change the default size, but only if it has been already set
        if self.defaultSize is not None:
            self.defaultSize = self.widgetSize()
            self.calcResize(self.defaultSize)

    def calcResize(self, size):
        """ Calculate resize of items

        :param size:
        :type size:
        :return:
        :rtype:
        """
        if self.defaultSize is None:
            # Initialize values
            self.defaultSize = size
            self.initialIconSize = QtCore.QSize(self._iconSize)
            self.stateChanged.emit()
            QtCore.QTimer.singleShot(0, self.refresh)
            return

        # Exclude the verticalScrollbar space
        if not self.verticalScrollBar().isVisible():
            size -= QtCore.QSize(self.verticalScrollBar().size().width(), 0)

        size -= QtCore.QSize(utils.dpiScale(2), 0)

        # Calculate the number of columns
        iconWidth = (self.initialIconSize * self.zoomAmount).width() + self.spacing()
        calcColumns = int(size.width() / iconWidth)  # calculate number of columns and round it down
        columns = calcColumns + self.columnOffset

        # setColumn() was run so set the columns by changing the columnOffset
        if self.columnQueue != 0:
            diff = self.columnQueue - calcColumns
            columns = self.columnQueue
            self.columnOffset = diff
            self.columnQueue = 0

        columns = max(columns, 1)  # atleast 1 column

        # Set columnOffset maximum and minimum

        # Calculate the new ratio to resize the icons to
        ratio = float(iconWidth * columns) / float(size.width())
        self.setZoomAmount(1/ratio)
        self.stateChanged.emit()

    def setIconMinMax(self, size):
        minSize = size[0]
        maxSize = size[1]
        self.defaultMinIconSize = minSize
        self.defaultMaxIconSize = maxSize
        currentSize = self.iconSize()
        width = currentSize.width()
        height = currentSize.height()
        if width > maxSize or height > maxSize:
            size = QtCore.QSize(maxSize, maxSize)
            self.setIconSize(size)
        elif width < minSize or height > minSize:
            size = QtCore.QSize(minSize, minSize)
            self.setIconSize(size)

    def refresh(self):
        """ Refresh so the icons show properly

        :return:
        :rtype:
        """
        QtCore.QCoreApplication.processEvents()
        size = self.size() - QtCore.QSize(self.verticalScrollBar().size().width(), 0)
        self.resizeEvent(QtGui.QResizeEvent(size, size))
        self.model().layoutChanged.emit()
        if not self.updatesEnabled():
            self.setUpdatesEnabled(True)

    def setModel(self, model):
        """ Set the Model

        :param model:
        :type model:
        :return:
        :rtype:
        """
        model.setUniformItemSizes(self._uniformIcons)
        model.refreshRequested.connect(self.loadVisibleIcons)
        ret = super(ThumbnailWidget, self).setModel(model)
        if self.selectionModel():
            self.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        return ret

    def invisibleRootItem(self):
        if self.model():
            return self.model().invisibleRootItem()

    def onSelectionChanged(self):
        index = self.currentIndex()
        if self.model() is not None:
            item = self.model().itemFromIndex(index)
            self.model().onSelectionChanged(index, item)
            self.requestSelectionChanged.emit(index, item)

    def paginationLoadNextItems(self):
        """ Simple method to call the models loadData method when the vertical slider hits the max value, useful to load
        the next page of data on the model.

        :return:
        :rtype:
        """

        if not self.pagination:
            return

        model = self.model()
        if model is None:
            return

        vbar = self.verticalScrollBar()
        sliderMax = vbar.maximum()
        sliderPos = vbar.sliderPosition()

        if sliderPos == sliderMax:
            indexes = self.selectionModel().selection().indexes()
            model.loadData()

            # Reselect selection
            self.setAutoScroll(False)
            [self.selectionModel().setCurrentIndex(index, QtCore.QItemSelectionModel.SelectCurrent) for index in indexes]
            self.setAutoScroll(True)


