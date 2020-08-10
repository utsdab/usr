from Qt import QtWidgets, QtCore, QtGui

from zoo.apps.toolsetsui.widgets import toolsetwidgetitem

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import groupedtreewidget
from zoo.libs.utils import zlogging
from zoovendor.six.moves import cPickle
from zoovendor.six import string_types



logger = zlogging.getLogger(__name__)


class ToolsetTreeWidget(groupedtreewidget.GroupedTreeWidget):
    ActiveItem_Active = 0
    ActiveItem_InActive = 1
    ActiveItem_Hidden = 2

    toolsetHidden = QtCore.Signal(string_types)

    def __init__(self, parent=None, registry=None):
        """

        :param parent:
        :type parent: zoo.apps.toolsetsui.widgets.toolsetframe.ToolsetFrame
        :param registry:
        :type registry:
        """

        self.toolsetFrame = parent
        super(ToolsetTreeWidget, self).__init__(parent=parent, customTreeWidgetItem=toolsetwidgetitem.ToolsetWidgetItem)

        self.toolsetRegistry = registry
        self.lastHidden = []
        self.properties = {}
        self.toolsetIdsDragging = None
        self._toolsetUi = None
        self.setMouseTracking(True)
        self.toolsetItems = []

    def initUi(self):

        self.header().hide()

        super(ToolsetTreeWidget, self).initUi()
        self._toolsetUi = self.window().property("tool")

        self.setIndentation(0)
        self.initDragDrop()
        self.setMinimumHeight(0)

        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored))
        self.toolsetHidden.connect(self.toolsetHiddenEvent)

    @property
    def toolsetUi(self):
        """

        :return:
        :rtype: zoo.apps.toolsetsui.toolsetui.ToolsetsUI
        """
        return self._toolsetUi

    def connections(self):
        super(ToolsetTreeWidget, self).connections()

        self.itemsDragged.connect(self.itemsDraggedEvent)
        self.itemsDropped.connect(self.itemsDroppedEvent)
        self.itemsDragCancelled.connect(self.itemsDragCancelledEvent)
        self.toolsetUi.windowResizedFinished.connect(lambda: self.updateTree(True))

    def itemsDraggedEvent(self, items):
        """ On drag event

        :param items: a tree item
        :type items: list of toolsetwidgetitem.ToolsetWidgetItem
        """
        for it in items:
            # Emit a signal when the tree item is dragged
            it.widget.toolsetDragged.emit()

    def itemsDragCancelledEvent(self, items, target):
        """Emit a signal when the tree item is dragged but then cancelled and not dropped

        :param items: a tree item
        :type items: list of toolsetwidgetitem.ToolsetWidgetItem
        """
        for it in items:
            it.widget.toolsetDragCancelled.emit()
            it.savePropertiesToData()

        from zoo.apps.toolsetsui import toolsetui
        if target is None or not utils.hasAncestorType(target, toolsetui.ToolsetsUI):
            mousePos = QtGui.QCursor.pos()
            self.spawnToolset(mousePos)

    def itemsDroppedEvent(self, items):
        """Emit a signal when the tree item is dropped

        :param items: a tree item
        :type items: list of toolsetwidgetitem.ToolsetWidgetItem
        """
        for it in items:
            if isinstance(it, toolsetwidgetitem.ToolsetWidgetItem):
                it.updatePropertiesFromData()
                it.widget.toolsetDropped.emit()
            else:
                logger.warning("WARNING: ToolsetWidgetItem expected. \"{}\" found. Properties may not be sent".format(str(type(it))))

        self.toolsetFrame.updateColors()

    def toolsetHiddenEvent(self, toolsetId):
        """ Save a list of last hidden toolsets

        :param toolsetId:
        :return:
        """
        if toolsetId not in self.lastHidden:
            self.lastHidden.append(toolsetId)

    def addToolItem(self, item):
        """ Add by ToolsetWidgetItem

        :param item:
        :type item: toolsetwidgetitem.ToolsetWidgetItem
        :return:
        """

        if self.itemExists(item):
            return

        self.addTopLevelItem(item)

        item.setFlags(self.itemWidgetFlags)

    def addToolset(self, toolsetId, activate=True):
        """ Add toolset by toolsetId

        :param toolsetId: toolsetId string usually found in ToolsetWidgetItem.id
        :type toolsetId: basestring
        :param activate:
        :param color:
        :return:
        """

        index = self.invisibleRootItem().childCount()
        return self.insertToolset(index, toolsetId, activate=activate)

    def insertToolset(self, index, toolsetId, treeParent=None, activate=True):
        """ Insert toolset by type

        :param index:
        :param toolsetId:
        :param activate:
        :param treeParent:
        :return:
        """

        color = self.toolsetRegistry.toolsetColor(toolsetId)
        root = (treeParent or self.invisibleRootItem())
        treeWidgetItem = toolsetwidgetitem.ToolsetWidgetItem(toolsetId=toolsetId, color=color,
                                                             toolsetRegistry=self.toolsetRegistry,
                                                             treeWidget=self, parent=treeParent)

        childCount = root.childCount()

        if index > childCount:
            index = root.childCount()

        root.insertChild(index, treeWidgetItem)

        treeWidgetItem.setFlags(self.itemWidgetFlags)
        treeWidgetItem.applyWidget(activate=activate)
        return treeWidgetItem

    def invisibleRootItem(self):
        return super(ToolsetTreeWidget, self).invisibleRootItem()

    def reconstructItems(self, item, widgetInfo):
        """ Usually only used when dragged into a separate tree

        :param item:
        :type item: toolsetwidgetitem.ToolsetWidgetItem
        :param widgetInfo:
        :return:
        """

        parent = item.parent()

        if parent is None:
            parent = self.invisibleRootItem()  # type: toolsetwidgetitem.ToolsetWidgetItem
            index = parent.indexOfChild(item)
            tooltip = item.toolTip(0)
            parent.removeChild(item)

            prop = toolsetwidgetitem.itemData[widgetInfo.data] # todo: itemdata needs to be in a function
            toolsetId = prop["toolsetId"]

            # Check if toolset exists
            useExisting = True  # True: move to new dragged location? or False: leave the toolset where it is in the tree?

            draggedItem = None
            # Avoid duplicates by using existing one
            if useExisting:
                draggedItem = self.toolset(toolsetId)
                if draggedItem is not None:
                    parent.insertChild(index, draggedItem)
                    self.toolsetFrame.toggleToolset(toolsetId, activate=True, keepOpen=True)
            if draggedItem is None:  # Use the currently existing ToolsetWidgetItem, if none is found add a new toolset
                draggedItem = self.insertToolset(index, toolsetId)

            draggedItem.setText(groupedtreewidget.WIDGET_COL, widgetInfo.text)
            draggedItem.setData(groupedtreewidget.ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, widgetInfo.data)
            draggedItem.setData(groupedtreewidget.DATA_COL, QtCore.Qt.EditRole, widgetInfo.itemType)
            draggedItem.setToolTip(0, tooltip)  # does this need to be done?

        for i, c in enumerate(widgetInfo.children):
            draggedItem = self.insertToolset(i, c.data, item)
            self.reconstructItems(draggedItem, c)
        return draggedItem

    def toolsetIds(self):
        """ Returns list of toolset IDs in tree

        :return:
        """
        return [it.value().id() for it in self.iterator()]

    def toolset(self, toolsetId):
        """ Returns item based on toolset ID, returns None if nothing found.

        :param toolsetId:
        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """

        for it in self.iterator():
            if it.value().id() == toolsetId:
                return it.value()
        return None

    def toolsets(self):
        """ Returns list of ToolsetWidgetItems in tree

        :return:
        :rtype: list of toolsetwidgetitem.ToolsetWidgetItem
        """
        return [it.value() for it in self.iterator()]

    def itemHidden(self, item):
        """ If item is hidden

        :param item:
        :return:
        """
        for it in self.iterator():
            treeItem = it.value()
            if type(item) == type(treeItem):
                return item.hidden

        return None

    def itemExists(self, item):
        """ Checks to see if item of the same type exists in the tree yet

        :param item:
        :return:
        """
        for it in self.iterator():
            treeItem = it.value()
            if type(item) == type(treeItem):
                return True

        return False

    def startDrag(self, supportedActions, widget=None):
        """ Override the default start drag which is run in the mousePressEvent

        Here we get a pixmap of the itemWidget and use that as the drag

        :param widget:
        :param supportedActions:
        :return:
        """
        itemPos = self.mapFromGlobal(QtGui.QCursor.pos())

        item = self.itemAt(itemPos)  # type: toolsetwidgetitem.ToolsetWidgetItem
        # Mouse over titleFrame only

        # todo: sometimes item can be none?

        self.setDragWidget(item.widget.titleFrame, hotspotAlign=QtCore.Qt.AlignVCenter)
        self.toolsetIdsDragging = item.widgetData()['toolsetId']

        super(ToolsetTreeWidget, self).startDrag(supportedActions, item.widget.titleFrame)

    def mimeData(self, items):
        """ Save properties

        :param items:
        :type items: list of toolsetwidgetitem.ToolsetWidgetItem
        :return:
        :rtype:
        """

        # Save the properties before dragging
        for it in items:
            it.savePropertiesToData()

        return super(ToolsetTreeWidget, self).mimeData(items)

    def dropEvent(self, event):
        """ Drop event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        treeSource = event.source()  # type: ToolsetTreeWidget

        # Remove callbacks on source tree right before it gets dropped
        for item in treeSource.selectedItems():  # type: toolsetwidgetitem.ToolsetWidgetItem
            item.widget.stopCallbacks()

        ret = super(ToolsetTreeWidget, self).dropEvent(event)

        QtCore.QTimer.singleShot(0, lambda x=treeSource: self.dropFinish(x))

        return ret

    @staticmethod
    def dropFinish(treeSource):
        """ Runs this code after dropEvent on a timer to do any finishing up of ui refreshing and updating

        :param treeSource:
        :type treeSource: ToolsetTreeWidget
        :return:
        :rtype:
        """
        treeSource.toolsetFrame.window().resizeWindow()
        treeSource.toolsetFrame.updateColors()

    def dropMimeData(self, parent, index, mimedata, action):
        ret = super(ToolsetTreeWidget, self).dropMimeData(parent, index, mimedata, action)
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i)

        return ret

    def updateWidget(self, item):
        """

        :param item:
        :type item: toolsetwidgetitem.ToolsetWidgetItem
        :return:
        :rtype:
        """

        item.applyWidget(recreateWidget=True)

    def calculateContentHeight(self):
        """ Calculate the height for the contents to stretch into

        :return:
        """
        rowSum = 0
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if isinstance(item, toolsetwidgetitem.ToolsetWidgetItem) and item.hidden is False:
                rowSum += item.widget.sizeHint().height()

        return rowSum

    def spawnToolset(self, pos):
        """ Spawn a new toolset at the given position

        :param pos:
        :type pos:
        :return:
        :rtype:
        """

        toolsetId = self.toolsetIdsDragging
        from zoo.apps.toolpalette import run as _paletterun
        _zooPalette = _paletterun.show()
        plugin = _zooPalette.executePluginById("zoo.toolsets", toolsetIds=[toolsetId], position=(pos.x(), pos.y()))
        sourceItem = self.toolsetFrame.toggleToolset(toolsetId)  # toolset not working?
        self.toolsetFrame.updateColors()
        self.toolsetIdsDragging = None
        # The last added toolset ui should be the last toolset ui
        toolsetUi = plugin.latestTool()  # type: ToolsetUi
        targetItem = toolsetUi.toolsetFrame.toolset(toolsetId)
        targetItem.setPropertiesData(sourceItem.widgetData())

    def activateItem(self, item, activate=True, closeOthers=False):
        """ Activate Item

        :param activate:
        :type activate:
        :param closeOthers:
        :type closeOthers:
        :param item:
        :type item:  toolsetwidgetitem.ToolsetWidgetItem
        :return:
        """
        wgt = item.widget  # type: ToolsetWidget
        wgt.setActive(active=activate, emit=False)

        if closeOthers:
            treeItemIterator = QtWidgets.QTreeWidgetItemIterator(self)
            for it in treeItemIterator:
                treeItem = it.value()  # type: ToolsetWidgetItem
                if treeItem is not item:
                    treeItem.collapse()

        QtCore.QTimer.singleShot(0, lambda: self.updateTreeWidget())

    def updateTreeWidget(self, disableScrollBars=False):
        """ Add resize requested to updateTreeWidget

        :return:
        """
        vPolicy = None
        if disableScrollBars:
            vPolicy = self.verticalScrollBarPolicy()
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        super(ToolsetTreeWidget, self).updateTreeWidget()
        self.toolsetFrame.resizeRequested.emit()

        if vPolicy is not None:
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def updateTree(self, delayed=False):
        """ Update the tree

        Same as updateTreeWidget but if it needs some extra refreshes use this one.

        :param delayed: If delayed is true, it will do it after the timer of 0 seconds. Can help with some refresh issues
        :return:
        """

        if delayed:
            QtCore.QTimer.singleShot(0, self.updateTree)
            return
        self.setUpdatesEnabled(False)
        self.updateTreeWidget()
        self.toolsetFrame.window().resizeWindow()
        self.updateTreeWidget()  # needs to be done a second time for some reason
        self.setUpdatesEnabled(True)


    def activeItems(self):
        """ Returns active items as list of tuples.

        Example::

            First element tuple WidgetItem
            Second element Active or not

            [(ToolsetWidgetItem, True),
             (ToolsetWidgetItem, False),
             (ToolsetWidgetItem, True)
            ]

        :return:
        :rtype: list of tuple
        """
        ret = []
        for it in self.iterator():
            treeItem = it.value()

            if not treeItem.widget.isVisible():
                state = self.ActiveItem_Hidden
            elif treeItem.widget.collapsed == 0:  # Not collapsed
                state = self.ActiveItem_Active
            else:
                state = self.ActiveItem_InActive

            if treeItem is None:
                continue

            ret.append((treeItem, state))

        return ret

    def closeEvent(self, event):
        self.removeEventFilter(self)
        super(ToolsetTreeWidget, self).closeEvent(event)

