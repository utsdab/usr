import os, sys
from functools import partial

from Qt import QtWidgets, QtCore
from zoo.libs.pyqt.extended.imageview import items
from zoo.libs.pyqt.extended.imageview.model import ItemModel
from zoo.libs.pyqt.extended.imageview.thumbnail import minibrowser
from zoo.libs.utils import env
from zoo.libs.utils import path


class ExampleCustomWidget(minibrowser.MiniBrowser):
    def __init__(self, *args, **kwargs):
        super(ExampleCustomWidget, self).__init__(*args, **kwargs)

    def closeEvent(self, event):
        if self.model() is not None:
            self.model().clear()
            self.model().parentClosed.emit(True)
        super(ExampleCustomWidget, self).closeEvent(event)

    def contextMenu(self, items, menu):
        """ Example on how to add the context menu

        :param items:
        :type items: list(Treeitem)
        :param menu:
        :type menu: QMenu
        :return:
        :rtype:
        """
        for i in range(10):
            menu.addAction(str(i))


class ExampleItem(items.BaseItem):
    def __init__(self, *args, **kwargs):
        super(ExampleItem, self).__init__(*args, **kwargs)
        self._description = "\n".join(("name: {}".format(self.name)))


class ExampleThumbnailViewerModel(ItemModel):
    """Overridden base model to handle custom loading of the data eg. files
    """
    # called by the view to signal the thread
    parentClosed = QtCore.Signal(bool)

    def __init__(self, view, directory=""):
        super(ExampleThumbnailViewerModel, self).__init__(parent=view)
        self.view = view
        self.directory = directory
        self.currentFilesList = []
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
        super(ExampleThumbnailViewerModel, self).clear()

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
        tItem = items.TreeItem(item=item)
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


def _bind(parent=None):
    wid = ExampleCustomWidget(parent=parent)
    rootDirectory = r"D:\reference\Firefall"
    model = ExampleThumbnailViewerModel(wid, rootDirectory)
    wid.setModel(model)
    model.listFiles()
    model.loadData()
    wid.show()
    return wid


def main():
    if not env.isInMaya():
        app = QtWidgets.QApplication(sys.argv)
        _bind()
        sys.exit(app.exec_())
    else:
        return _bind(parent=None)  # mayaui.getMayaWindow())


if __name__ == "__main__":
    main()
