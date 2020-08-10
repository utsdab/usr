import os
from functools import partial

from Qt import QtGui, QtCore, QtWidgets

from zoo.libs.pyqt.extended.imageview import items

from zoo.libs.pyqt.extended.imageview.items import TreeItem
from zoo.preferences.core import preference
from zoo.libs.utils import path


class ThumbnailDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(ThumbnailDelegate, self).__init__(parent)

    def sizeHint(self, option, index):
        return index.model().itemFromIndex(index).sizeHint()

    def paint(self, painter, options, index):
        index.model().itemFromIndex(index).paint(painter, options, index)


class ExampleItem(items.BaseItem):
    def __init__(self, *args, **kwargs):
        super(ExampleItem, self).__init__(*args, **kwargs)
        self._description = "\n".join(("name: {}".format(self.name)))


class ItemModel(QtGui.QStandardItemModel):
    """Main Data Model for the thumbnail widget, this is the main class to handle data access between the core and the view
    """
    # total number of items to load a time
    chunkCount = 20

    def __init__(self, parent=None):
        super(ItemModel, self).__init__(parent)
        self.rootItem = QtGui.QStandardItem('root')
        # items list , all items to show in the view should be in this one dimensional list
        self.items = []  # type: items.TreeItem
        self.loadedCount = 0

    def canFetchMore(self, index=QtCore.QModelIndex()):
        """ Overridden to handle paginating the data using the len(self.items) > self.loadedCount,

        :param index:
        :type index:
        :rtype: bool
        """
        if len(self.items) > self.loadedCount:
            return True
        return False

    def fetchMore(self, index=QtCore.QModelIndex()):
        """ Fetch more rows

        :param index:
        :type index:
        :return:
        :rtype:
        """

        reminder = len(self.items) - self.loadedCount
        itemsToFetch = min(reminder, self.chunkCount)
        self.beginInsertRows(QtCore.QModelIndex(), self.loadedCount, self.loadedCount + itemsToFetch-1)
        self.loadedCount += itemsToFetch
        self.endInsertRows()

    def reset(self):
        self.beginResetModel()
        self.endResetModel()

    def loadData(self):
        """Intended to be overridden by subclasses, This method should deal with loading a chunk of the items to display.
        Use self.loadedCount and self.chunkCount variable to determine the amount to load

        :Example:

            if len(self.currentFilesList) < self.loadedCount:
                filesToLoad = self.mylist
            else:
                filesToLoad = self.mylist[self.loadedCount: self.loadedCount + self.chunkCount]

        :rtype: None
        """
        raise NotImplementedError()

    def data(self, index, role):
        if not index.isValid():
            return None
        row = int(index.row())
        item = self.items[row]
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return item.text()
        elif role == QtCore.Qt.ToolTipRole:
            return item.toolTip()
        elif role == QtCore.Qt.DecorationRole:
            return item.icon()
        elif role == QtCore.Qt.BackgroundRole:
            color = item.backgroundColor()
            if color:
                return QtGui.QColor(*color)
        elif role == QtCore.Qt.ForegroundRole:
            color = item.foregroundColor()
            if color:
                return QtGui.QColor(*color)
        return super(ItemModel, self).data(index, role)

    def doubleClickEvent(self, modelIndex, item):
        pass


class BrowserViewModel(ItemModel):
    """Overridden base model to handle custom loading of the data eg. files
    """
    # called by the view to signal the thread
    parentClosed = QtCore.Signal(bool)

    def __init__(self, view, directory=""):
        super(BrowserViewModel, self).__init__(parent=view)
        self.view = view
        self.directory = directory
        self.currentFilesList = []
        self.themePref = preference.interface("core_interface")
        self.threadpool = QtCore.QThreadPool.globalInstance()

    def clear(self):
        # remove any threads that haven't started yet
        self.threadpool.clear()

        while not self.threadpool.waitForDone():
            continue
        # clear any items, this is necessary to get python to GC alloc memory
        self.items = []
        self.loadedCount = 0
        self.currentFilesList = []
        super(BrowserViewModel, self).clear()

    def onDirectoryChanged(self, directory):
        # honestly this first stage should be done in the view and on a separate thread
        self.clear()
        self.directory = directory
        self.listFiles()
        self.loadData()

    def listFiles(self):
        """Simple functions which gathers all the images to load upfront, probably could do this on a thread and in
        chunks
        """
        results = []
        for i in os.listdir(self.directory):
            fullPath = os.path.join(self.directory, i)
            if path.isImage(fullPath):
                results.append(fullPath)
        self.currentFilesList = results

    def createItem(self, item):
        """Custom wrapper Method to create a :class:`items.TreeItem`, add it to the model items and class appendRow()

        :param item:
        :type item: :class:`baseItem`
        :return:
        :rtype: :class:`items.TreeItem`
        """
        tItem = TreeItem(item=item, themePref=self.themePref)
        self.items.append(tItem)
        self.appendRow(tItem)
        return tItem

    def loadData(self):
        """Overridden to prep the images from load and viewing in the view, you can do anything in here.
        Lazy loading happens either on first class initialization and any time the vertical bar hits the max value, we than
        grab the current the new file chunk by files[self.loadedCount: loadedCount + self.chunkCount] that way we are
        only loading a small amount at a time.
        Since this is an example of how to use the method , you can approach it in any way you wish but for each item you
        add you must initialize a item.BaseItem() or custom subclass and a item.treeItem or subclass which handles the
        qt side of the data per item

        """
        if len(self.currentFilesList) < self.loadedCount:
            filesToLoad = self.currentFilesList
        else:
            filesToLoad = self.currentFilesList[self.loadedCount: self.loadedCount + self.chunkCount]
        for f in filesToLoad:
            workerThread = items.ThreadedIcon(iconPath=f)
            # create an item for the image type
            it = ExampleItem(name=os.path.basename(f).split(os.extsep)[0], iconPath=f)
            qitem = self.createItem(item=it)
            workerThread.signals.updated.connect(partial(self.setItemIconFromImage, qitem))
            self.parentClosed.connect(workerThread.finished)
            self.threadpool.start(workerThread)

        self.reset()

    def setItemIconFromImage(self, item, image):
        """Custom method that gets called by the thread

        :param item:
        :type item: :class:`TreeItem`
        :param image: The Loaded QImage
        :type image: QtGui.QImage
        :return:
        :rtype:
        """
        item.applyFromImage(image)

    def doubleClickEvent(self, modelIndex, item):
        """Gets called by the listview when an item is doubleclicked

        :param modelIndex:
        :type modelIndex: QtCore.QModelIndex
        :param item:
        :type item: TreeItem
        :return:
        :rtype:
        """
        pass