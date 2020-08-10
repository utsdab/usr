from zoovendor.six.moves import cPickle
import pprint

from Qt import QtCore, QtWidgets, QtGui

from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants, utils
from zoo.libs.pyqt.widgets import expandedtooltip
from zoo.libs.pyqt.widgets import stackwidget
from zoo.libs.pyqt.widgets import frame, elements
from zoo.libs.utils import zlogging
from zoo.preferences.core import preference

logger = zlogging.getLogger(__name__)

WIDGET_COL = 0
ITEMWIDGETINFO_COL = 1
DATA_COL = 2

THEME_PREFS = preference.interface("core_interface")


class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, name, flags, after=None):
        super(TreeWidgetItem, self).__init__(parent, after)
        self.setText(WIDGET_COL, name)

        self.setFlags(flags)


class ItemInfo(object):
    """ The description of a TreeWidgetItem so it can be pickled into into a mimedata and dragged into another tree

    """
    data = None
    text = ""
    children = None
    toolTip = ""
    itemHash = 0
    itemType = ""

    @classmethod
    def fromItems(cls, items):
        """
        - If a child is selected after parent, the child is not included in the reconstruction
        - If a child is selected first, then the parent after, the child excluded in the reconstruction

        :param items:
        :return:
        """

        infos = []

        for item in items:
            infos.append(cls.fromItem(item))
            item.setToolTip(0, str(hash(item)))

        # Child first then parent selection
        checkChildren = []
        for info in infos:
            checkChildren.append(info)

            for c in checkChildren:
                cls.removeFromDescendents(info, c)

        # for every info in infos remove the previous info from the children
        return infos

    def __str__(self):
        newDict = dict(self.__dict__)
        newDict['data'] = cPickle.loads(str(self.data))
        return pprint.pformat(newDict)

    @classmethod
    def fromItem(cls, item):
        """ Constructs a tree from item

        :param item:
        :return:
        """

        info = cls()
        info.data = item.data(ITEMWIDGETINFO_COL, QtCore.Qt.EditRole)
        info.text = item.data(WIDGET_COL, QtCore.Qt.EditRole)
        info.toolTip = item.toolTip(WIDGET_COL)
        info.itemType = item.data(DATA_COL, QtCore.Qt.EditRole)
        info.itemHash = hash(item)
        info.children = info.children or []

        children = [item.child(i) for i in range(item.childCount())]

        for child in children:
            childItemInfo = cls.fromItem(child)
            info.children.append(childItemInfo)

        return info

    @classmethod
    def removeFromDescendents(cls, itemInfo, removeInfo):
        """ Remove removeInfo from itemInfos descendents

        :param itemInfo:
        :param removeInfo:
        :return:
        """

        for c in list(itemInfo.children):
            if c.itemHash == removeInfo.itemHash:
                itemInfo.children.remove(c)

            cls.removeFromDescendents(c, removeInfo)

    @classmethod
    def removeRedundant(cls, infos):
        """ Remove redundant children from list of infos.

        When dragging we don't want the children to be in the list, only the upper most parent.
        This is to stop it from creating the child already when the parent creates the children when reconstructing
        the TreeWidgetItem sub tree.

        :param infos:
        :return:
        """
        ret = list(infos)
        for i in infos:
            for j in infos:
                if i == j:
                    continue

                if cls.inDescendents(i, j):
                    ret.remove(j)

        return ret

    @classmethod
    def inDescendents(cls, sourceInfo, targetInfo):
        """ If target is in source's descendants

        :param sourceInfo:
        :type sourceInfo: ItemInfo
        :return:
        """

        for c in sourceInfo.children:
            if c.itemHash == targetInfo.itemHash:
                return targetInfo

            return cls.inDescendents(c, targetInfo)

        return None

    def descendents(self):
        """ Descendants of info

        :param item:
        :type item: ItemInfo
        :return:
        """
        desc = []
        for c in self.children:
            desc.append(c)
            desc += self.descendents(c)

        return desc


class GroupedTreeWidget(QtWidgets.QTreeWidget):
    ITEMTYPE_WIDGET = "WIDGET"
    ITEMTYPE_GROUP = "GROUP"

    ITEMWIDGETINFO_COL = 1
    DATA_COL = 2

    INSERT_AFTERSELECTION = 0
    INSERT_END = 1
    INSERT_ATINDEX = 2

    defaultGroupName = "Group"
    itemsDropped = QtCore.Signal(object)
    itemsDragged = QtCore.Signal(object)
    itemsDragCancelled = QtCore.Signal(object, object)

    CustomTreeWidgetItem = QtWidgets.QTreeWidgetItem  # TreeWidgetItem class to use, change this to set custom

    def __init__(self, parent=None, locked=False, allowSubGroups=True, customTreeWidgetItem=QtWidgets.QTreeWidgetItem):
        """ A tree widget that has grouping capabilities

        :param parent:
        :param locked:
        :param allowSubGroups:
        """
        super(GroupedTreeWidget, self).__init__(parent)

        self.setRootIsDecorated(False)

        # Drag drop
        self.droppedItems = None
        self.dropCancelled = False
        self.draggedItems = None
        self.dropTarget = None

        # Grouping flags
        self.allowSubGroups = allowSubGroups
        self.headerItem = None  # type: QtWidgets.QTreeWidgetItem
        self.CustomTreeWidgetItem = customTreeWidgetItem

        self.groupFlags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        self.groupUnlockedFlags = QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        self.itemWidgetFlags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled
        self.itemWidgetUnlockedFlags = QtCore.Qt.ItemIsDragEnabled

        self.locked = locked
        self.setLocked(locked)

        self.initUi()
        self.connections()
        self.dragWidget = None
        self.dragWidgetAlign = None

    def initUi(self):
        """ Init Ui Setup

        :return:
        """
        # Header setup
        self.headerItem = QtWidgets.QTreeWidgetItem(["Widget"])
        self.setHeaderItem(self.headerItem)
        self.header().hide()

        self.initDragDrop()

        self.resizeColumnToContents(1)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setIndentation(utils.dpiScale(10))
        self.setFocusPolicy(QtCore.Qt.NoFocus)

    def dragging(self):
        return self.draggedItems is not None

    def setLocked(self, locked):
        """ Sets the lock for drag and drop.

        :param locked:
        :type locked: bool
        """
        self.locked = locked

        if locked:
            self.groupFlags = self.groupFlags & ~self.groupUnlockedFlags
            self.itemWidgetFlags = self.itemWidgetFlags & ~self.itemWidgetUnlockedFlags
        else:
            self.groupFlags = self.groupFlags | self.groupUnlockedFlags
            self.itemWidgetFlags = self.itemWidgetFlags | self.itemWidgetUnlockedFlags
        self.applyFlags()

    def connections(self):
        self.itemSelectionChanged.connect(self.treeSelectionChanged)

    def treeSelectionChanged(self):
        pass

    def initDragDrop(self):
        """ Set up Drag drop Settings for this widget
        """

        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)

    def setDragWidget(self, widget, hotspotAlign=QtCore.Qt.AlignVCenter):
        """ The widget that will be shown in the drag

        :return:
        """
        self.dragWidget = widget
        self.dragWidgetAlign = hotspotAlign

    def startDrag(self, supportedActions, widget=None):
        """ Override this to set the widget thats gets shown when dragged

        Example:

            .. code-block:: python

                def startDrag(self, supportedActions):
                    itemPos = self.mapFromGlobal(QtGui.QCursor.pos())
                    item = self.itemAt(itemPos)
                    self.setDragWidget(self.itemWidget(item, groupedtreewidget.WIDGET_COL).titleFrame, hotspotAlign=QtCore.Qt.AlignVCenter)

                    super(ToolsetTreeWidget, self).startDrag(supportedActions)


        :param supportedActions:
        :param widget: Widget to use to drag. If widget is none, then just use the whole ItemWidget. Usually set by the overriding class
        :return:
        """

        # If widget is not under the mouse, we dont want to start the drag
        if widget is not None and not widget.underMouse():
            return

        # todo: this might cause problems in linux or osx! Need to test
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            # Ignore alt drag, as alt drag copies items. Not sure if theres another workaround to disable alt-drag
            return

        # If no widget then ignore
        if self.dragWidget is None:
            super(GroupedTreeWidget, self).startDrag(supportedActions)
        else:
            hotSpot = self.dragWidget.mapFromGlobal(QtGui.QCursor.pos())
            if self.dragWidgetAlign & QtCore.Qt.AlignTop == QtCore.Qt.AlignTop:
                hotSpot.setY(0)
            elif self.dragWidgetAlign & QtCore.Qt.AlignVCenter == QtCore.Qt.AlignVCenter:
                hotSpot.setY(self.dragWidget.height() / 2)

            elif self.dragWidgetAlign & QtCore.Qt.AlignBottom == QtCore.Qt.AlignBottom:
                hotSpot.setY(self.dragWidget.height())

            if self.dragWidgetAlign & QtCore.Qt.AlignLeft == QtCore.Qt.AlignLeft:
                hotSpot.setX(0)
            elif self.dragWidgetAlign & QtCore.Qt.AlignCenter == QtCore.Qt.AlignCenter:
                hotSpot.setX(self.dragWidget.width() / 2)
            elif self.dragWidgetAlign & QtCore.Qt.AlignRight == QtCore.Qt.AlignRight:
                hotSpot.setX(self.dragWidget.width())

            # Todo: have to make sure selected indexes are draggable. Where is "getSelectedDraggableIndexes()"?
            mimeData = self.model().mimeData(self.selectedIndexes())

            pixmap = QtGui.QPixmap(self.dragWidget.size())
            self.dragWidget.render(pixmap)

            tintColor = QtGui.QColor(*THEME_PREFS.TREEITEM_DRAG_TINT)
            painter = QtGui.QPainter(pixmap)
            painter.setCompositionMode(painter.CompositionMode_SoftLight)
            painter.fillRect(pixmap.rect(), tintColor)
            painter.end()

            #
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            drag.setHotSpot(hotSpot)

            self.dropCancelled = True
            drag.targetChanged.connect(self.dragTargetChanged)
            #
            dropAction = drag.exec_(supportedActions, QtCore.Qt.DropAction.MoveAction)

            # Remove selected items from old tree but only do it if its the same tree type
            if dropAction == QtCore.Qt.DropAction.MoveAction and drag.target() is not None and \
                type(utils.getWidgetTree(drag.target())) == type(self):
                for s in self.selectedItems():
                    parent = s.parent() or self.invisibleRootItem()
                    parent.removeChild(s)

            self.dragWidget = None
            self.dragWidgetAlign = None
            self.dropCancelledCheck(self.dropTarget)

    def dragTargetChanged(self, widget):
        """ Drag target changed

        :param widget:
        :type widget:
        :return:
        :rtype:
        """
        # Workaround for qt not giving us the widget.
        if widget is None:
            # We want it to still set the target even if dropAction is set to IgnoreAction
            # Note! This will cause issues with screen recording software when its recording but should work for most people
            widget = QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos())
        self.dropTarget = widget

    def dropCancelledCheck(self, target):
        """ Check to see if the drop was cancelled

        :param target: The target widget that has been dropped into
        :type target: QtWidgets.QWidget
        :return:
        :rtype:
        """
        if self.dropCancelled and self.draggedItems:  # if the drop is cancelled and not dropped
            self.itemsDragCancelled.emit(self.draggedItems, target)
            self.dropCancelled = False
            self.draggedItems = None
            self.dropTarget = None

    def dropEvent(self, event):
        """ Drop event

        Handle all the QT weirdness of drag dropping to separate trees here.

        :param event:
        :type event: QtGui.QDropEvent
        :return:
        """
        event.source().dropCancelled = False  # drop successful so set to false
        self.draggedItems = None
        ret = super(GroupedTreeWidget, self).dropEvent(event)

        mData = event.mimeData().data("dragData")
        data = cPickle.loads(str(mData))

        # If dropped onto same tree
        if event.source() is self:
            for winfo in data['itemInfos']:
                item = self.itemFromHash(winfo.itemHash)

                # Hacky way of searching for the destination QTreeItemWidget since the other columns dont get copied
                # over if moved to a different tree
                # We use tooltip instead since only that single column data gets copied.
                item.setToolTip(WIDGET_COL, winfo.toolTip)  # Revert tooltip back from item id hash
                item.setText(WIDGET_COL, winfo.text)
                items = [item] + self.descendants(item)

                self.updateItemWidgets(items)
        else:  # Dropped into a different tree
            # Remove redundant itemInfos
            itemInfos = ItemInfo.removeRedundant(data['itemInfos'])  # type: list

            for winfo in itemInfos:
                item = self.itemFromHash(winfo.itemHash)
                # Replaces item with itemType we want

                # Reconstruct the items and its children since QT doesnt do it for us for some reason
                item = self.reconstructItems(item, winfo)
                item.setToolTip(WIDGET_COL, winfo.toolTip)  # Revert tooltip back from item id hash
                item.setText(WIDGET_COL, winfo.text)
                items = [item] + self.descendants(item)
                self.updateItemWidgets(items)

            # Find the extraneous items bug that QT does when moving to separate tree
            remove = []
            parent = None
            for childIndex in self.droppedItems['remove']:
                parent = self.droppedItems['parent'] or self.invisibleRootItem()
                item = parent.child(childIndex)

                # If there are any children with hashes remaining, delete them since it is just extra junk items
                # from the drag drop
                if item is not None and str(item.toolTip(WIDGET_COL)) in self.hashesFromItemInfo(data['itemInfos'], str=True):
                    remove.append(childIndex)

            for r in remove:
                parent.takeChild(r)

        self.itemsDropped.emit(items)
        self.updateTreeWidget()
        return ret

    def removeItems(self, items):
        """ Remove items from tree

        :param items:
        :type items: list
        :return:
        :rtype:
        """
        root = self.invisibleRootItem()
        for item in items:
            (item.parent() or root).removeChild(item)

    def mimeData(self, items):
        """ The data that will be dragged between tree nodes

        :param items: List of selected TreeWidgetItems
        :type items: list of QtWidgets.TreeWidgetItem
        :return:
        """

        data = {"treeHash": hash(self),
                "itemInfos": []}

        data['itemInfos'] += ItemInfo.fromItems(items)
        ret = super(GroupedTreeWidget, self).mimeData(items)
        ret.setData("dragData", cPickle.dumps(data))

        self.itemsDragged.emit(items)
        self.draggedItems = items

        return ret

    def dropMimeData(self, parent, index, mimedata, action):
        """ Drop Mime Data

        This is usually run first before dropEvent

        :param parent:
        :param index:
        :param mimedata:
        :param action:
        :return:
        """
        dragData = mimedata.data("dragData")
        data = cPickle.loads(str(dragData))

        ret = super(GroupedTreeWidget, self).dropMimeData(parent, index, mimedata, action)

        # If its a different tree, get the items that were dropped into the new tree
        if data['treeHash'] != hash(self):
            self.droppedItems = {"parent": parent, "remove": []}
            parent = parent or self.invisibleRootItem() # done after because we want droppedItems['parent'] to be none if nothing is found
            for i, item in enumerate((parent.child(c) for c in range(parent.childCount()))):

                if item is not None and str(item.toolTip(0)) in self.hashesFromItemInfo(data['itemInfos'], str=True):  # has a hash

                    self.droppedItems['remove'].append(i)

        return ret

    def reconstructItems(self, item, widgetInfo):
        """ Reconstruct items from widgetInfo.

        Includes the children

        :param item:
        :param widgetInfo:
        :type widgetInfo: ItemInfo

        :return:
        """
        item.setText(WIDGET_COL, widgetInfo.text)
        item.setData(ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, widgetInfo.data)
        item.setData(DATA_COL, QtCore.Qt.EditRole, widgetInfo.itemType)

        newItem = None
        for c in widgetInfo.children:
            newItem = self.CustomTreeWidgetItem(parent=item)
            self.reconstructItems(newItem, c)
            item.addChild(newItem)

        return newItem

    def updateItemWidgets(self, items):
        """ Update TreeWidgetItems to their respective itemWidgets children.

        Usually used when drag and dropped, since drag drop deletes their itemWidget.

        :param items:
        :type items: list of QtWidgets.QTreeWidgetItem
        :return:
        """
        for it in items:
            if self.itemWidget(it, WIDGET_COL) is None:
                itemType = self.itemType(it)

                if itemType == self.ITEMTYPE_WIDGET:
                    self.updateWidget(it)
                elif itemType == self.ITEMTYPE_GROUP:
                    self.updateGroupWidget(it)

    def updateAllWidgets(self):
        """ Update all the TreeWidgetItems to their respective itemWidgets in the tree.

        Usually used when drag and dropped, since drag drop deletes their itemWidget.

        :return:
        """
        for it in self.iterator():
            if self.itemWidget(it.value(), WIDGET_COL) is None:
                if self.itemType(it) is self.ITEMTYPE_WIDGET:
                    self.updateWidget(it)
                else:
                    self.updateGroupWidget(it)

    def dragEnterEvent(self, event):
        """ Only accept if it is the same GroupedTreeWidget type.

        Override if you need it to accept drag events even if the tree class is different

        :param event:
        :return:
        """
        if event.source().__class__ is self.__class__:
            event.accept()
        else:
            event.ignore()

    def updateWidget(self, item):
        """ Update the TreeWidgetItem to its itemWidget.

        Should be overridden by its sub-class

        Usually used when drag and dropped, since drag drop deletes their itemWidget. This is to reconstruct the
        itemWidget.


        Example:
        .. code-block:: python
            model = self.itemWidgetInfo(item)
            self.setItemWidget(item, 0, QtWidgets.QLabel(item.text(1), parent=self))
            or
            self.setItemWidget(item, WIDGET_COL, componentwidget.ComponentWidget(componentModel=model, parent=self))

        :param item:
        :type item: QtWidgets.QTreeWidgetItem
        :return:
        """
        logger.error("GroupedTreeWidget.updateWidget() must be overridden! The itemWidget must be recreated and set"
                     "after the drag-drop.")
        logger.error("eg.self.setItemWidget(item, 0, QtWidgets.QLabel(item.text(1), parent=self))")

    def updateGroupWidget(self, item):
        """ Update the TreeWidgetItem to use a GroupWidget.

        This should be overridden if you have your own GroupWidget

        :param item: TreeWidgetItem to attach a GroupWidget to
        :type item: QtWidgets.QTreeWidgetItem
        :return:
        """
        data = self.itemWidgetInfo(item)
        widget = GroupWidget(data['text'], parent=self)
        widget.setTreeItem(item)
        if not data['collapsed']:
            widget.collapse()
        else:
            widget.expand()

        if data['titleFrameHidden']:
            widget.titleFrame.hide()

        self.setItemWidget(item, WIDGET_COL, widget)
        return widget

    def hashesFromItemInfo(self, itemInfos, str=False):
        """ Get all the itemHashes from itemInfos and their children

        :param itemInfos: list of
        :param str:
        :return:
        """
        hashes = []
        for itemInfo in itemInfos:
            hashes += self._hashesRecursive(itemInfo, string=str)

        # Remove duplicates
        return list(set(hashes))

    def _hashesRecursive(self, itemInfo, string=False):
        """ The recursive function to get all the hashes from the itemInfo and its children

        :param itemInfo:
        :type itemInfo: ItemInfo
        :return:
        """

        hashes = [str(itemInfo.itemHash)] if string else [itemInfo.itemHash]

        for c in itemInfo.children:
            hashes += self._hashesRecursive(c)

        return hashes

    def itemFromHash(self, hash, rootItem=None):
        """ Get the hash which is saved in the items tooltip

        :param hash:
        :param rootItem:
        :type rootItem:
        :return:
        """
        # Since QTreeWidgetItemIterator deletes the object somehow, we have to iterate
        # through the children manually
        rootItem = rootItem or self.invisibleRootItem()

        # generator for performance
        children = (rootItem.child(c) for c in range(rootItem.childCount()))

        retItem = None
        for item in children:
            if item.toolTip(0) == str(hash):
                return item

            childItem = self.itemFromHash(hash, item)

            if childItem is not None:
                return childItem

        return retItem

    def descendants(self, item):
        """ Descendants of QTreeWidgetItem

        :param item:
        :type item: QtWidgets.QTreeWidgetItem
        :return:
        """
        descendants = []
        for i in range(item.childCount()):
            descendants.append(item.child(i))
            descendants += self.descendants(item.child(i))

        return descendants

    def setCurrentItems(self, items):
        """ Selects the items in the TreeWidget

        :param items:
        """
        prevMode = self.selectionMode()
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        for item in items:
            self.setCurrentItem(item)
        self.setSelectionMode(prevMode)

    def insertNewItem(self, name, widget=None, index=0, treeParent=None, itemType=ITEMTYPE_WIDGET, widgetInfo=None,
                      icon=None):
        """ Inserts a new item at a location, and sets the widget as the itemWidget

        ItemType can be Widget or Group. Groups wont have user customized widgets, but can have children.
        ITEMTYPE_WIDGETS wont have children.

        May merge with self.addNewItem()

        :param name: Name of the new Item, generally put into the text field of the TreeWidgetItem. This is the text \
                     that is used for the search bar if it is active.

        :param widget: Expects ItemWidget or any subclass of QtWidgets.QWidget.
        :param index: Index to insert into
        :param treeParent: The parent that it will insert into. If treeParent is None, it will assume the parent to be Root
        :type treeParent: TreeWidgetItem or None
        :param itemType: The type of widget being set for the new Item.
        :param icon: Icon to set for the TreeWidgetItem
        :return: The new item created
        :rtype: TreeWidgetItem
        """
        if itemType == self.ITEMTYPE_WIDGET:
            flags = self.itemWidgetFlags
        else:
            flags = self.groupFlags

        newTreeItem = TreeWidgetItem(None, name=name, flags=flags)
        newTreeItem.setData(DATA_COL, QtCore.Qt.EditRole, itemType)  # Data set to column 2, which is not visible
        if icon is not None:
            newTreeItem.setIcon(WIDGET_COL, icon)

        (treeParent or self.invisibleRootItem()).insertChild(index, newTreeItem)
        if widget is not None:
            widget.setParent(self)
            self.setItemWidget(newTreeItem, WIDGET_COL, widget)
            if hasattr(widget, "toggleExpandRequested"):
                widget.toggleExpandRequested.connect(self.updateTreeWidget)
                widget.toggleExpandRequested.connect(newTreeItem.setExpanded)
            self.updateTreeWidget()

        newTreeItem.setData(ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, widgetInfo)

        return newTreeItem

    def addNewItem(self, name, widget=None, itemType=ITEMTYPE_WIDGET, widgetInfo=None, icon=None):
        """Add a new item type. Should be a group or an itemWidget. If you'd like to add a TreeWidgetItem instead, use
        addNewTreeWidgetItem()

        ItemType can be Widget or Group. Groups wont have user customized widgets, but can have children.
        ITEMTYPE_WIDGETS wont have children.

        May merge with self.insertNewItem()

        :param widgetInfo:
        :param name: Name of the new Item, generally put into the text field of the TreeWidgetItem. This is the text \
                     that is used for the search bar if it is active.
        :param widget: Expects ItemWidget or any subclass of QtWidgets.QWidget.
        :param itemType: The type of widget being set for the new Item.
        :param icon: Icon to set for the TreeWidgetItem
        :return: The new item created
        :rtype: TreeWidgetItem
        """

        if itemType == self.ITEMTYPE_WIDGET:
            flags = self.itemWidgetFlags
        else:
            flags = self.groupFlags

        if not isinstance(widgetInfo, int):
            # logger.error("widgetInfo must be a hash")
            pass

        item = self.currentItem()
        treeParent = None
        # If tree parent is left to none it will be added later on to end of the tree by self.addTopLevelItem()
        if item is not None:
            treeParent = self

        newTreeItem = TreeWidgetItem(treeParent, name=name, flags=flags, after=item)
        newTreeItem.setData(DATA_COL, QtCore.Qt.EditRole, itemType)  # Data set to column 2, which is not visible

        if icon is not None:
            newTreeItem.setIcon(WIDGET_COL, icon)

        # This will add it in if it wasn't added earlier, if it has then it will just pass through
        self.addTopLevelItem(newTreeItem)

        if widget:

            widget.setParent(self)
            if self.updatesEnabled():
                self.updateTreeWidget()

            self.setItemWidget(newTreeItem, WIDGET_COL, widget)  # items parent must be set otherwise it will crash
            # temp hack to support rowheight refresh, need to replace
            if hasattr(widget, "toggleExpandRequested"):
                widget.toggleExpandRequested.connect(self.updateTreeWidget)
                widget.toggleExpandRequested.connect(newTreeItem.setExpanded)
        self.setCurrentItem(newTreeItem)

        newTreeItem.setData(ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, widgetInfo)

        return newTreeItem

    def itemWidgetInfo(self, item):
        """ Retrieve the information to build the widget from the item.

        The info to build the itemWidget from the data that is stored in the data column
        eg. The ComponentModel for a ComponentWidget, or simply Text for QLabel

        It would return the ComponentModel or the Text.

        :param item:
        :return:
        """
        return item.data(ITEMWIDGETINFO_COL, QtCore.Qt.EditRole)

    def itemWidgets(self, itemType=None, treeItem=None):
        """ Gets all widgets in the tree.

        includeNones is for when QTreeWidgetItems don't have a itemWidget attached, but
        for any reason or another we still want to know

        :return: List of itemWidgets
        """
        if treeItem is not None:
            iteratorItem = treeItem
        else:
            iteratorItem = self
        treeItemIterator = QtWidgets.QTreeWidgetItemIterator(iteratorItem)
        widgets = []
        for it in treeItemIterator:
            treeItem = it.value()
            if treeItem is not None:
                itemWidget = self.itemWidget(treeItem)
                if itemWidget is None:
                    continue

                # Add by type, but if itemType is none, let them all through
                if (itemType is not None and self.itemType(treeItem) == itemType) or \
                        itemType is None:
                    widgets.append(itemWidget)

        return widgets

    def treeWidgetItemByHash(self, treeItemHash):
        """ Return TreeWidgetItem by hash.
        If this is slow maybe we should put all the treeWidgetItems in a hash map as well.

        :param treeItemHash:
        :return:
        :rtype: TreeWidgetItem or None
        """
        if treeItemHash is None:
            return

        treeItemIterator = QtWidgets.QTreeWidgetItemIterator(self)

        for it in treeItemIterator:
            treeItem = it.value()
            if hash(treeItem) == treeItemHash:
                return treeItem

    def itemWidget(self, treeItem, col=None):
        """ Short hand to get the item widget from the default column (as defined by WIDGET_COL)

        :param treeItem:
        :param col:
        :return:
        """
        col = col or WIDGET_COL

        return super(GroupedTreeWidget, self).itemWidget(treeItem, col)

    def updateTreeWidget(self):
        """ Updates the tree widget so the row heights of the TreeWidgetItems matches what the ComponentWidgets ask for
        in terms of the sizeHint() asks for
        """
        # Super hacky way to update the TreeWidget, add an empty object and then remove it
        self.insertTopLevelItem(0, QtWidgets.QTreeWidgetItem())
        self.takeTopLevelItem(0)

    def itemType(self, treeItem):
        """ Get the item type ("COMPONENT" or "GROUP")

        :param treeItem: The TreeWidgetItem to get the type of
        :type treeItem: TreeWidgetItem
        :return:
        """
        return treeItem.data(DATA_COL, QtCore.Qt.EditRole)

    def getItemName(self, treeItem):
        itemType = self.itemType(treeItem)
        wgt = self.itemWidget(treeItem)

        if itemType == self.ITEMTYPE_WIDGET:
            # If its an ItemWidget class
            if isinstance(wgt, ItemWidgetLabel):
                return wgt.text()

            # Try .name, if all else fails use the text in the widget column
            try:
                return wgt.name
            except AttributeError:
                # If no name is found, just use the treeItem text (the text hidden behind the widget)
                return treeItem.text(WIDGET_COL)
        elif itemType == self.ITEMTYPE_GROUP:
            return treeItem.text(WIDGET_COL)

    def filter(self, text):
        """ Hide anything that that doesnt have text. Used for searches.

        :param text:
        """

        treeItemIterator = QtWidgets.QTreeWidgetItemIterator(self)

        for it in treeItemIterator:
            treeItem = it.value()
            name = self.getItemName(treeItem)

            found = (text in name.lower())
            self.setItemHidden(treeItem, not found)

    def addGroup(self, name="", expanded=True, groupSelected=True, groupWgt=None):
        """ Adds a group to the ComponentTreeWidget. If no name is given, it will generate a unique one
        in the form of "Group 1", "Group 2", "Group 3" etc

        :param groupSelected:
        :param expanded:
        :param name:
        :param groupWgt: Use this as the widget, if its none we'll just use the text background as the display
        :return:
        :todo: This area still needs a bit of work. Update with addNewItem code
        """

        if self.locked:
            logger.warning("Locked. Adding of groups disabled")
            return

        # Place group after last selected item
        if len(self.selectedItems()) > 0:
            index = self.indexFromItem(self.selectedItems()[-1]).row() + 1
        else:
            # Otherwise just place it on the top
            index = self.topLevelItemCount()

        name = name or self.getUniqueGroupName()
        group = self.addNewItem(name, groupWgt, widgetInfo=groupWgt, itemType=self.ITEMTYPE_GROUP)
        self.insertTopLevelItem(index, group)

        if groupSelected:
            for s in self.selectedItems():
                # If its a group move on to the next one
                if self.itemType(s) == self.ITEMTYPE_GROUP:
                    continue

                self.addToGroup(s, group)

        group.setExpanded(expanded)
        self.updateTreeWidget()

        groupWgt.setTreeItem(group)
        groupWgt.expand()

        return group

    def insertGroup(self, name="", index=0, treeParent=None, expanded=True, groupWgt=None, icon=None):
        """ Inserts a group into index, underneath treeParent.

        :param name:
        :param index:
        :param treeParent:
        :param expanded:
        :param groupWgt:
        :type groupWgt: zoo.apps.hiveartistui.views.componentwidget.ComponentGroupWidget
        :param icon:
        :return:
        """
        if self.locked:
            logger.warning("Locked. Adding of groups disabled")
            return

        name = name or self.getUniqueGroupName()
        group = self.insertNewItem(name, widget=groupWgt, index=index, treeParent=treeParent,
                                   itemType=self.ITEMTYPE_GROUP, icon=icon, widgetInfo=groupWgt)

        groupWgt.setTreeItem(group)
        groupWgt.expand()

    def addToGroup(self, item, group):
        newWgt = self.itemWidget(item, WIDGET_COL).copy()

        if item.parent() is None:
            # If it is a top level item
            index = self.indexFromItem(item).row()
            self.takeTopLevelItem(index)
        else:
            # If its under a group
            index = item.parent().indexOfChild(item)
            item.parent().takeChild(index)

        # add to the last
        group.addChild(item)
        newWgt.setParent(self)  # parent must be put here otherwise it will crash
        self.setItemWidget(item, 0, newWgt)

        if self.updatesEnabled():
            self.updateTreeWidget()

    def getUniqueGroupName(self):
        """Returns a unique group name: "Group 1", "Group 2", "Group 3" etc.

        :return:
        :rtype: str
        """
        num = len(self.findItems(self.defaultGroupName + " *", QtCore.Qt.MatchFlag.MatchWildcard |
                                 QtCore.Qt.MatchFlag.MatchRecursive, 0))
        return self.defaultGroupName + " " + str(num + 1)

    def applyFlags(self):
        """ Apply flags as set by self.groupFlags and self.itemWidgetFlags.

        ITEMTYPE_WIDGET gets applied a different set of drag drop flags to
        ITEMWIDGET_GROUP
        """
        treeItemIterator = QtWidgets.QTreeWidgetItemIterator(self)
        for it in treeItemIterator:
            treeItem = it.value()
            if self.itemType(treeItem) == self.ITEMTYPE_WIDGET:
                treeItem.setFlags(self.itemWidgetFlags)
            elif self.itemType(treeItem) == self.ITEMTYPE_GROUP:
                treeItem.setFlags(self.groupFlags)

    def iterator(self):
        """ Iterator to iterate through the treeItems

        .. code-block:: python

            for it in treeItemIterator:
                treeItem = it.value()

        :return:
        :rtype:
        """
        return QtWidgets.QTreeWidgetItemIterator(self)


class ItemWidgetTitleFrame(stackwidget.StackTitleFrame):

    def initUi(self):
        self.layout().addWidget(self.titleFrame)

        self.titleFrame.setContentsMargins(*utils.marginsDpiScale(1, 1, 4, 0))
        self.titleFrame.mousePressEvent = self.mousePressEvent

        # the horizontal layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.titleFrame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        # the icon and title and spacer
        self.expandToggleButton.setParent(self.titleFrame)
        if self.collapsed:
            self.expandToggleButton.setIcon(self._collapsedIcon)
        else:
            self.expandToggleButton.setIcon(self._expandIcon)

        self.folderIcon.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        spacerItem = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # add to horizontal layout
        self.horizontalLayout.addWidget(self.expandToggleButton)
        self.horizontalLayout.addWidget(self.folderIcon)
        self.horizontalLayout.addItem(spacerItem)
        self.titleFrame.setFixedHeight(self.titleFrame.sizeHint().height())

        self.setMinimumSize(self.titleFrame.sizeHint().width(), self.titleFrame.sizeHint().height() + 3)

        self.horizontalLayout.addWidget(self.groupTextEdit)
        self.horizontalLayout.addLayout(self.extrasLayout)
        self.horizontalLayout.addWidget(self.deleteBtn)

        self.horizontalLayout.setStretchFactor(self.groupTextEdit, 4)


class GroupWidget(QtWidgets.QWidget):
    """
    The Widget used for groups in TreeWidget
    """
    _deleteIcon = iconlib.icon("xMark")
    _itemIcon = iconlib.icon("openFolder01")
    _collapsedIcon = iconlib.icon("sortClosed")
    _expandIcon = iconlib.icon("sortDown")

    def __init__(self, title="", parent=None, treeItem=None, hideTitleFrame=False):
        super(GroupWidget, self).__init__(parent=parent)

        self.color = uiconstants.DARKBGCOLOR
        self.horizontalLayout = elements.hBoxLayout(self)
        self.mainLayout = elements.hBoxLayout(self)
        self.expandToggleButton = QtWidgets.QToolButton(parent=self)
        self.folderIcon = QtWidgets.QToolButton(parent=self)
        self.titleFrame = frame.QFrame(parent=self)
        self.collapsed = False

        self.groupTextEdit = stackwidget.LineClickEdit(title, single=False)
        self.titleExtrasLayout = QtWidgets.QHBoxLayout()
        self.deleteBtn = QtWidgets.QToolButton(parent=self)
        self.treeItem = treeItem

        if hideTitleFrame:
            self.titleFrame.hide()

        self.initUi()
        self.connections()

    def initUi(self):
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.folderIcon.setIcon(self._itemIcon)
        self.deleteBtn.setIcon(self._deleteIcon)

        self.buildTitleFrame()

    def setTreeItem(self, treeItem):
        self.treeItem = treeItem
        self.updateTreeItemData()

    def connections(self):
        self.expandToggleButton.clicked.connect(self.expandToggle)
        self.groupTextEdit.textChanged.connect(self.updateTreeItemData)

    def updateTreeItemData(self):
        data = {"text": self.groupTextEdit.text(),
                "collapsed": self.collapsed,
                "titleFrameHidden": self.titleFrame.isHidden()
                }
        self.treeItem.setData(ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, data)

    def text(self):
        """
        Returns the text of the text edit
        :return:
        """
        return self.groupTextEdit.text()

    def buildTitleFrame(self):
        """Builds the title part of the layout with a QFrame widget
        """

        self.layout().addWidget(self.titleFrame)

        self.titleFrame.setContentsMargins(1, 1, 4, 0)
        self.titleFrame.mousePressEvent = self.mousePressEvent

        # the horizontal layout
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.titleFrame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        # the icon and title and spacer
        self.expandToggleButton.setParent(self.titleFrame)
        if self.collapsed:
            self.expandToggleButton.setIcon(self._collapsedIcon)
        else:
            self.expandToggleButton.setIcon(self._expandIcon)

        self.folderIcon.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        spacerItem = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # add to horizontal layout
        self.horizontalLayout.addWidget(self.expandToggleButton)
        self.horizontalLayout.addWidget(self.folderIcon)
        self.horizontalLayout.addItem(spacerItem)
        self.titleFrame.setFixedHeight(30)

        self.setMinimumSize(self.titleFrame.sizeHint().width(), self.titleFrame.sizeHint().height() + 3)

        self.horizontalLayout.addWidget(self.groupTextEdit)
        self.horizontalLayout.addLayout(self.titleExtrasLayout)
        self.horizontalLayout.addWidget(self.deleteBtn)

        self.horizontalLayout.setStretchFactor(self.groupTextEdit, 4)

    def expandToggle(self):
        if self.collapsed:
            self.expand()

        else:
            self.collapse()

    def onCollapsed(self):
        """
        Collapse and hide the item contents
        :return:
        """
        self.updateTreeItemData()
        self.expandToggleButton.setIcon(self._collapsedIcon)
        self.treeItem.setExpanded(False)

    def onExpand(self):
        self.updateTreeItemData()
        self.expandToggleButton.setIcon(self._expandIcon)
        self.treeItem.setExpanded(True)

    def expand(self):
        """ Extra Code for convenience """
        self.onExpand()
        self.collapsed = False

    def collapse(self):
        """ Extra Code for convenience """
        self.onCollapsed()
        self.collapsed = True

    def mousePressEvent(self, event):
        event.ignore()

    def passThroughMouseEvent(self, event):
        event.ignore()


class ItemWidgetLabel(QtWidgets.QLabel):
    """

    """
    triggered = QtCore.Signal()

    def __init__(self, name, parent=None):
        super(ItemWidgetLabel, self).__init__(name, parent=parent)

        self.emitTarget = None
        self.initUi()

    def initUi(self):
        pass

    def connectEvent(self, func):
        self.emitTarget = func
        self.triggered.connect(func)

    def copy(self):
        CurrentType = type(self)
        ret = CurrentType(self.text())
        ret.name = self.name
        # ret.setIcon(self.icon())
        ret.setStyleSheet(self.styleSheet())
        expandedtooltip.copyExpandedTooltips(self, ret)

        return ret

    def mouseDoubleClickEvent(self, event):
        self.triggered.emit()
        # self.emitTarget()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def text(self):
        return super(ItemWidgetLabel, self).text()
