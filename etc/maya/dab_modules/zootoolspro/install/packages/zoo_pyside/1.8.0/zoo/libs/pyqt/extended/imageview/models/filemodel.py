import os
import unicodedata
import textwrap
from functools import partial

from Qt import QtCore, QtGui

from zoo.libs import iconlib
from zoo.libs.pyqt.extended.imageview import items, model
from zoo.libs.pyqt.extended.imageview.items import TreeItem
from zoo.libs.utils import path, zlogging
from zoo.preferences.core import preference
from zoo.libs.zooscene import zooscenefiles
from zoo.libs.zooscene.constants import INFO_DESCRIPTION, INFO_WEBSITES
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)

QT_SUPPORTED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "bmp", "pbm", "pgm", "ppm", "xbm", "xpm"]


class FileViewModel(model.ItemModel):
    parentClosed = QtCore.Signal(bool)
    doubleClicked = QtCore.Signal(str)
    itemSelectionChanged = QtCore.Signal(str, object)
    refreshRequested = QtCore.Signal()

    def __init__(self, view, directory=None, extensions=None, chunkCount=20, uniformIcons=False, extVis=False):
        """ Overridden base model to handle loading of the ThumbnailView widget data eg. specific files/images

        This class is the most basic form of the Thumbnail model which is attached to a ThumbnailView

        A directory given and is populated with "png", "jpg", or "jpeg" images.

        Tooltips are also generated from the file names

        This class can be overridden further for custom image loading in subdirectories such as .zooScene files.

        :param view: The viewer to assign this model data?
        :type view: thumbwidget.ThumbListView
        :param directory: The directory full path where the .zooScenes live
        :type directory: str
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        :param extensions: The image file extensions to override, otherwise will be ["png", "jpg", "jpeg"]
        :type extensions: list of basestring
        :param uniformIcons: False keeps the images non-square.  True the icons will be square, clipped on longest axis
        :type uniformIcons: bool
        """
        super(FileViewModel, self).__init__(parent=view)
        self.view = view
        self.extensions = extensions
        self.chunkCount = chunkCount
        self.currentFilesList = []  # the files loaded in the viewer, empty while initializing
        self.infoDictList = None  # usually used for generating tooltips
        self.toolTipList = None  # list of tooltips to match each images
        self.currentImage = None  # the current image name selected (no image highlighted on creation)
        self.fileNameList = None  # each file's name with an extension
        self.fileNameListNoExt = None  # each file's name without an extension, for display
        self._nameExtVis = extVis  # Show name extensions
        self.directory = None
        self.themePref = preference.interface("core_interface")  # the color theme data
        self.threadPool = QtCore.QThreadPool.globalInstance()
        self.lastFilter = ""
        self.uniformIcons = uniformIcons
        self.dynamicLoading = True  # Dynamic icon loading
        self.items = []  # type: list[TreeItem]

        # load the images
        if directory is not None:
            self.setDirectory(directory, True)

    def setDirectory(self, directory, refresh=True):
        """Used to set or change the directory"""
        self.directory = directory
        if refresh:
            self.refreshList()

    def refreshList(self):
        """ Refreshes the icon list if contents have been modified, does not change the root directory
        """
        self.view.setUpdatesEnabled(False)
        self.clear()
        self.refreshModelData()
        self.loadData()
        self.view.setUpdatesEnabled(True)

    def _thumbnails(self, extensions=None):
        """ Get full path name of thumbnails of files

        In this case the thumbnails are the files (images) themselves:

            ["C:/aPath/image01.jpg", "C:/aPath/image02.jpg"]

        Override this if you need to get thumbnails from another location, ie for .zooScene or .hdr files

        :type extensions: list of extensions of files or set to None to use all images
        :return: List of paths to image files
        :rtype: list of basestring
        """
        results = []
        for i in self.fileNameList:
            fullPath = os.path.join(self.directory, i)
            if extensions is None and path.isImage(fullPath):
                results.append(fullPath)
            else:
                # todo: do extensions
                pass

        return results

    def _infoDictionaries(self):
        """Returns a list of info dictionaries for each .zooScene file.

        These dictionaries contain information such as author, tag, descriptions etc

        Overrides base class

        :return infoDictList: A list of info dictionaries for each .zooScene file
        :rtype infoDictList: list(dict)
        """
        return zooscenefiles.infoDictionaries(self.fileNameList, self.directory)

    def _toolTips(self):
        """Generates the _toolTips as a list, is constructed from the self.infoDictList

        Overrides base class
        """
        self.toolTipList = list()
        for i, thumb in enumerate(self.currentFilesList):
            self.toolTipList.append(self._createToolTip(self.infoDictList[i], self.fileNameList[i]))

    def _createToolTip(self, infoDictSingle, fileName):
        """Creates a single tooltip from a single zooScene file

        Overrides base class

        :param zooScenePath: The full path to the zooScene image
        :type zooScenePath: str
        :param infoDictSingle: The information dictionary with tag author and description information
        :type infoDictSingle: str
        :return toolTip: The tooltip description
        :rtype toolTip: str
        """
        if not infoDictSingle:  # dict is none so return file path as tooltip
            return os.path.join(self.directory, fileName)
        # breaks on some unicode so convert to plain text
        filepath = "{} ".format(os.path.join(self.directory, fileName))
        infoDescription = unicodedata.normalize('NFKD', infoDictSingle[INFO_DESCRIPTION]).encode('ascii', 'ignore')
        if infoDescription:  # may not exist
            infoDescription = textwrap.fill(infoDescription, 80)
            info = "{} \n\n".format(infoDescription)
        else:
            info = ""
        infoWebsites = unicodedata.normalize('NFKD', infoDictSingle[INFO_WEBSITES]).encode('ascii', 'ignore')
        if infoWebsites:  # may not exist
            website = "\n\n{} ".format(infoWebsites)
        else:
            website = ""
        toolTip = ("{}{}{} ".format(info, filepath, website))
        return toolTip

    def clear(self):
        """Clears the images and data from the model, usually used while refreshing
        """
        # remove any threads that haven't started yet
        self.threadPool.clear()

        while not self.threadPool.waitForDone():
            continue
        # clear any items, this is necessary to get python to GC alloc memory
        self.items = []
        self.loadedCount = 0
        self.currentFilesList = []
        super(FileViewModel, self).clear()

    def fileList(self):
        """Updates the self.fileNameList

        Can be overridden
        """
        if not self.extensions:
            self.extensions = QT_SUPPORTED_EXTENSIONS
        if not isinstance(self.extensions, list):
            raise ValueError("Extensions must be list, \"{}\" type given \"{}\" ".format(type(self.extensions),
                                                                                         self.extensions))
        self.fileNameList = path.filesByExtension(self.directory, self.extensions)

    def filterList(self, text, tag=None):
        """ Returns a list of ints of rows that gets shown or hidden in the search

        :param text:
        :type text:
        :param tag:
        :type tag: basestring or list
        :return:
        :rtype:
        """
        filterList = list()
        if isinstance(tag, string_types):
            tag = [tag]

        for i in range(len(self.infoDictList)):
            for t in tag:
                if t is None or t == "filename":
                    for j, fileName in enumerate(self.fileNameListNoExt):
                        if text.lower() in fileName.lower():
                            filterList.append(j)
                else:
                    if text.lower() in self.infoDictList[i][t.lower()].lower():
                        filterList.append(i)

        for i in range(len(self.fileNameListNoExt)):
            self.view.thumbWidget.setRowHidden(i, i not in filterList)  # Show row if not in filterList

        self.lastFilter = text

        return filterList


    def refreshModelData(self):
        """Needs to create/recreate the thumbnail lists, tooltips and infoDict data
        """
        self.fileList()  # updates self.fileNameList
        self.fileNameListNoExt = [os.path.splitext(preset)[0] for preset in self.fileNameList]
        self.infoDictList = self._infoDictionaries()
        self.currentFilesList = self._thumbnails()
        self._toolTips()  # generates self.toolTipList
        self.refreshRequested.emit()

    def lazyLoadFilter(self):
        """Breaks up the lists self.currentFilesList, self.fileNameList, self.toolTipList for lazy loading.

        Can be overridden, usually to choose if the display names should have extensions or not
        Default is no extensions on display names

        :return filesToLoad: The file name fullpath list (with extensions)
        :rtype filesToLoad: list of basestring
        :return namesToLoad: The name of the item, will be the label under the image, usually extension removed
        :rtype namesToLoad: list of basestring
        :return tooltipToLoad: The toolTip list to load
        :rtype tooltipToLoad: list of basestring
        """
        if self._nameExtVis:
            fileNameList = self.fileNameList
        else:
            fileNameList = self.fileNameListNoExt

        if len(self.currentFilesList) < self.loadedCount:
            filesToLoad = self.currentFilesList
            namesToLoad = fileNameList
            tooltipToLoad = self.toolTipList
        else:
            filesToLoad = self.currentFilesList[self.loadedCount: self.loadedCount + self.chunkCount]
            namesToLoad = fileNameList[self.loadedCount: self.loadedCount + self.chunkCount]
            tooltipToLoad = self.toolTipList[self.loadedCount: self.loadedCount + self.chunkCount]
        return filesToLoad, namesToLoad, tooltipToLoad

    def setExtensionVisibility(self, show):
        """ Show/Hide extension visibility in the item names
        """
        self._nameExtVis = show

    def loadData(self):
        """ Overridden method that prepares the images for loading and viewing.

        Is filtered first via self.lazyLoadFilter()

        From base class documentation:

            Lazy loading happens either on first class initialization and any time the vertical bar hits the max value,
            we then grab the current the new file chunk by files[self.loadedCount: loadedCount + self.chunkCount] that
            way we are only loading a small amount at a time.
            Since this is an example of how to use the method , you can approach it in any way you wish but for each item you
            add you must initialize a item.BaseItem() or custom subclass and a item.treeItem or subclass which handles the
            qt side of the data per item

        """


        if self.lastFilter != "":  # Don't load any new data if theres a search going on
            return

        filesToLoad, namesToLoad, tooltipToLoad = self.lazyLoadFilter()
        loaded = self.loadedCount
        # Load the files
        for i, f in enumerate(filesToLoad):

            if f is None:
                f = iconlib.iconPath("emptyThumbnail")["sizes"][200]["path"]

            workerThread = items.ThreadedIcon(iconPath=f)
            # create an item for the image type
            it = items.BaseItem(name=namesToLoad[i], iconPath=f, description=tooltipToLoad[i])

            it.metadata = self.infoDictList[loaded + i]
            qitem = self.createItem(item=it)
            workerThread.signals.updated.connect(partial(self.setItemIconFromImage, qitem))
            self.parentClosed.connect(workerThread.finished)

            it.iconThread = workerThread

            if self.dynamicLoading is False:
                self.threadPool.start(workerThread)
            self.loadedCount += 1

        if len(filesToLoad) > 0:
            self.reset()

    def createItem(self, item):
        """Custom wrapper Method to create a ::class`items.TreeItem`, add it to the model items and class appendRow()
        :param item:
        :type item: ::class:`baseItem`
        :return:
        :rtype: ::class:`items.TreeItem`
        """
        tItem = TreeItem(item=item, themePref=self.themePref, squareIcon=self.uniformIcons)
        self.items.append(tItem)
        self.appendRow(tItem)
        return tItem

    def itemTexts(self):
        """ Get all the item texts and put them into a generator

        :return:
        :rtype:
        """
        return (item.itemText() for item in self.items)

    def indexFromText(self, text):
        """ Get Item from text

        :param text:
        :type text:
        :return:
        :rtype:
        """
        for it in self.items:
            if it.itemText() == text:
                return self.indexFromItem(it)

    def setUniformItemSizes(self, enabled):
        """ Set uniform item sizes

        Make the items square if true, if false it will keep the images original aspect ratio for the items

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        self.uniformIcons = enabled
        for it in self.items:
            it.squareIcon = enabled

    def setItemIconFromImage(self, item, image):
        """Custom method that gets called by the thread

        :param item:
        :type item: :class:`TreeItem`
        :param image: The Loaded QImage
        :type image: QtGui.QImage
        """
        item.applyFromImage(image)

    def doubleClickEvent(self, modelIndex, item):
        """Gets called by the listview when an item is doubleclicked
        :param modelIndex:
        :type modelIndex: QtCore.QModelIndex
        :param item:
        :type item: TreeItem
        :return self.currentImage:  The current image with it's name and file extension
        :rtype self.currentImage:  str
        """
        self.currentImage = item._item.name
        self.doubleClicked.emit(self.currentImage)
        return self.currentImage

    def onSelectionChanged(self, modelIndex, item):
        """Gets called by the listview when an item is changed, eg left click or rightclick
        :param modelIndex:
        :type modelIndex: QtCore.QModelIndex
        :param item:
        :type item: TreeItem
        """
        try:  # can error while renaming files and the change no longer exists so ignore if so
            self.currentImage = item._item.name
            self.itemSelectionChanged.emit(self.currentImage, item._item)
            return self.currentImage
        except AttributeError:
            pass

    def closeEvent(self, event):
        """Closes the model

        :param event:
        :type event:
        """
        if self.qModel is not None:
            self.qModel.clear()
            self.qModel.parentClosed.emit(True)
        super(FileViewModel, self).closeEvent(event)


