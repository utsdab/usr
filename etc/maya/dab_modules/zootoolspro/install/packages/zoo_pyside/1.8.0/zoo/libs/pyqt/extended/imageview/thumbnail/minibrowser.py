from collections import OrderedDict
from functools import partial

from Qt import QtCore, QtWidgets, QtGui
from zoo.libs.maya.qt import mayaui

from zoo.libs.pyqt import utils, uiconstants as uic
from zoo.libs.pyqt.extended.imageview.thumbnail.thumbnailwidget import ThumbnailWidget
from zoo.libs.pyqt.extended.searchablemenu import TaggedAction
from zoo.libs.pyqt.extended.snapshotui import SnapshotUi
from zoo.libs.pyqt.widgets import searchwidget, layouts, buttons, typehinting
from zoo.libs.pyqt.widgets.extendedbutton import ExtendedButton
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs import iconlib
from zoo.libs.pyqt.extended.imageview.thumbnail.infoembedwindow import InfoEmbedWindow
from zoo.libs.pyqt.widgets.layouts import hBoxLayout, vBoxLayout
from zoo.libs.zooscene import zooscenefiles
from zoo.preferences.core import preference
import maya.api.OpenMaya as om2
import os

THEME_PREFS = preference.interface("core_interface")


class MiniBrowser(QtWidgets.QWidget):
    itemSelectionChanged = QtCore.Signal(object, object)  # Item selection changed of model
    infoToggled = QtCore.Signal(bool)  # When info embed window is toggled
    screenshotSaved = QtCore.Signal(object)
    savedHeight = None  # type: int
    infoEmbedWindow = None  # type: InfoEmbedWindow
    dotsMenu = None  # type: DotsMenu
    thumbWidget = None  # type:
    infoButton = None  # type: ExtendedButton
    searchWidget = None  # type: ThumbnailSearchWidget
    uniformIcons = True
    SNAPTYPE_NEW = 0
    SNAPTYPE_EDIT = 1

    def __init__(self, parent=None, listDelegate=None, thumbnailWidget=ThumbnailWidget, toolsetWidget=None,
                 columns=None, iconSize=None,
                 fixedWidth=None, fixedHeight=None, infoEmbedShift=200, uniformIcons=False,
                 itemName="", applyText="Apply", applyIcon="checkOnly", createText="New",
                 newActive=True,
                 snapshotActive=False, clipboardActive=False, snapshotNewActive=False, createThumbnailActive=False):
        """ The main widget for viewing thumbnails

        :param parent: the parent widget
        :type parent: QtWidgets.QWidget
        :param toolsetWidget: Optional Toolset Ui
        :type toolsetWidget: toolsetwidget.ToolsetWidgetMaya
        :param infoEmbedShift: How many pixels to shift when info embed window activated
        :type infoEmbedShift: int
        :param listDelegate:
        :type listDelegate:
        :param thumbnailWidget:
        :type thumbnailWidget:
        :param columns: The number of square image columns, will vary for non-square images, overrides iconSize
        :type columns: int
        :param iconSize: Set the icon size in pixels, will be overridden by columns
        :type iconSize: QtCore.QSize
        :param fixedWidth: The fixed width of the widget in pixels, dpi handled
        :type fixedWidth: int
        :param fixedHeight: the fixed height of the widget in pixels, dpi handled
        :type fixedHeight: int
        :param uniformIcons: Will keep the icons square, images will be clipped if True, non square if False
        :type uniformIcons: bool
        """
        super(MiniBrowser, self).__init__(parent=parent)
        self.toolsetWidget = toolsetWidget
        self.infoEmbedShift = utils.dpiScale(infoEmbedShift)
        self.listDelegate = listDelegate
        self.thumbnailClass = thumbnailWidget  # type: type(ThumbnailWidget)
        self.uniformIcons = uniformIcons
        self.itemName = itemName
        self.applyText = applyText
        self.applyIcon = applyIcon
        self.createText = createText
        self.snapshotType = self.SNAPTYPE_EDIT
        self.snapshotWgt = SnapshotUi(mayaui.getMayaWindow(), onSave=self.screenshotSaved.emit, imageType="png")
        self.initUi()
        self.connections()
        self.autoResizeItems = True

        if iconSize is not None:
            self.setIconSize(iconSize)
        if columns:
            self.setColumns(columns)
        if fixedHeight:
            self.setFixedHeight(utils.dpiScale(fixedHeight), save=True)
        if fixedWidth:
            self.setFixedWidth(utils.dpiScale(fixedWidth))

        self.dotsMenu.setSnapshotActive(snapshotActive)
        self.dotsMenu.setFromClipboardActive(clipboardActive)
        self.dotsMenu.setFromSnapShotActive(snapshotNewActive)
        self.dotsMenu.setCreateThumbnailActive(createThumbnailActive)
        self.dotsMenu.setCreateActive(newActive)

    def initUi(self):
        """ Initialize UI

        :return:
        :rtype:
        """
        layout = vBoxLayout()
        self.setLayout(layout)
        self.thumbWidget = self.thumbnailClass(parent=self, delegate=self.listDelegate, uniformIcons=self.uniformIcons)
        self.infoEmbedWindow = InfoEmbedWindow(parent=self,
                                               margins=(0, 0, 0, uic.SMLPAD), resizeTarget=self.thumbWidget)

        layout.addLayout(self.topBar())
        layout.addWidget(self.infoEmbedWindow)
        layout.addWidget(self.thumbWidget, 1)

        layout.setContentsMargins(0, 0, 0, 0)
        self.thumbWidget.setSpacing(utils.dpiScale(0))

    def connections(self):
        """ Connections

        :return:
        :rtype:
        """
        self.dotsMenu.snapshotAction.connect(self.setPathThumbnail)
        self.snapshotWgt.saved.connect(self.snapshotSaved)

    def topBar(self):
        """ Top Bar

        :return:
        :rtype:
        """
        topLayout = hBoxLayout(margins=(0, 0, 0, uic.SPACING), spacing=uic.SREG)

        self.searchWidget = ThumbnailSearchWidget(self, themePref=THEME_PREFS)
        toolTip = "Thumbnail information and add meta data"
        self.infoButton = buttons.styledButton(icon="information", style=uic.BTN_TRANSPARENT_BG, toolTip=toolTip)
        self.searchWidget.searchChanged.connect(lambda text, tag: self.onSearchChanged(text, tag))
        self.infoButton.leftClicked.connect(self.toggleInfoVisibility)
        self.dotsMenu = DotsMenu(self, uniformIcons=self.uniformIcons, itemName=self.itemName, applyText=self.applyText,
                                 applyIcon=self.applyIcon, createText=self.createText)
        self.dotsMenu.uniformIconAction.connect(self.updateUniformIcons)
        topLayout.addWidget(self.searchWidget)
        topLayout.addWidget(self.infoButton)
        topLayout.addWidget(self.dotsMenu)
        return topLayout

    def updateUniformIcons(self, taggedAction):
        """ Update the uniform icons

        :param taggedAction:
        :type taggedAction: TaggedAction
        :return:
        :rtype:
        """
        self.uniformIcons = taggedAction.isChecked()

    def setSnapshotType(self, snapType):
        """

        :param snapType:
        :type snapType: MiniBrowser.SNAPTYPE_NEW or MiniBrowser.SNAPTYPE_EDIT
        :return:
        :rtype:
        """

        self.snapshotType = snapType
        self.setPathThumbnail()
        if snapType == MiniBrowser.SNAPTYPE_NEW:
            self.snapshotWgt.setWindowTitle("Create New Item")
        else:
            self.snapshotWgt.setWindowTitle("Edit Thumbnail")

    def snapshotSaved(self):
        """ Refresh thumbs on snapshot saved

        :return:
        :rtype:
        """
        # delete any jpgs since we're going to use pngs from now on

        depPath = self.itemDependencyPath()
        if depPath is not None:
            oldThumb = os.path.join(depPath, "thumbnail.jpg")
            if os.path.exists(oldThumb):
                os.remove(oldThumb)
            # todo: should just refresh one thumbnail for speed
        self.refreshThumbs()

    def setScreenshotPath(self, path):
        """ Path to save the screenshot to

        :param path:
        :type path:
        :return:
        :rtype:
        """
        self.snapshotWgt.setSavePath(path)

    def setPathThumbnail(self):
        """ Save the thumbnail path to get ready to save

        :return:
        :rtype:
        """
        extensions = ("png", "jpg", "jpeg")

        if self.snapshotType == MiniBrowser.SNAPTYPE_EDIT:
            # If the zoo file is a image file, replace that instead of creating a thumbnail
            dirPath = self.itemDependencyPath(create=True)
            if self.itemFileExt().lower() in extensions:
                screenshotPath = self.itemFilePath()
                self.snapshotWgt.imageType = self.itemFileExt().lower()
            else:
                screenshotPath = os.path.join(dirPath, "thumbnail.png")
                self.snapshotWgt.imageType = "png"

        else:
            dirPath = self.directory()
            newName = self.newImageName() + ".png"
            screenshotPath = os.path.join(dirPath, newName)
            self.snapshotWgt.imageType = "png"

        self.setScreenshotPath(screenshotPath)

    def onSearchChanged(self, text, tag):
        """ Set the filter on search changed

        :param text:
        :type text:
        :param tag:
        :type tag:
        :return:
        :rtype:
        """
        self.filter(text, tag)

    def newImageName(self):
        """ Generate a new name

        :return:
        :rtype:
        """
        itemTexts = list(self.model().itemTexts())
        check = 1000
        for i in range(1, check):
            testName = "newimage{}".format(str(i).zfill(2))
            if testName not in itemTexts:
                return testName

    def setFixedHeight(self, h, save=False):
        """ Sets the fixed height of the widget

        :param h:
        :type h:
        :param save: save this height as a default when switching between infoembedwindows
        :type save:
        :return:
        :rtype:
        """

        super(MiniBrowser, self).setFixedHeight(h)
        if save:
            self.savedHeight = h

    def selectedMetadata(self):
        """ Gets the metadata of the currently selected item

        :return:
        :rtype: dict
        """
        return dict(self.infoEmbedWindow.metadata)

    def itemFilePath(self):
        """ Gets the current filepath from the currently selected items metadata

        :return:
        :rtype:
        """
        if self.infoEmbedWindow.metadata is None:
            return None

        return self.infoEmbedWindow.metadata['zooFilePath']

    def itemDependencyPath(self, create=False):
        """ Get dependency folder

        :return:
        :rtype:
        """
        try:
            ret = self.infoEmbedWindow.metadata['zooFilePath']
        except TypeError:
            return None
        return zooscenefiles.getDependencyFolder(ret, create=create)[0]

    def directory(self):
        """ Get the directory

        :return:
        :rtype:
        """
        return self.model().directory

    def itemFileName(self):
        """ Gets the current file name from the currently selected item's metadata

        :return:
        :rtype:
        """
        return self.infoEmbedWindow.metadata['name']

    def itemFileExt(self):
        """

        :return:
        :rtype: basestring
        """
        return self.infoEmbedWindow.metadata['extension']

    def setModel(self, model):
        """

        :param model:
        :type model: zoo.libs.pyqt.extended.imageview.models.filemodel.FileViewModel
        :return:
        :rtype:
        """
        self.thumbWidget.setModel(model)
        self.infoEmbedWindow.setModel(model)
        model.itemSelectionChanged.connect(self.itemSelectionChanged.emit)
        model.itemSelectionChanged.connect(self.itemSelected)

    def itemSelected(self, image, item):
        """ Item selected

        :param image:
        :type image:
        :param item:
        :type item:
        :return:
        :rtype:
        """
        self.setPathThumbnail()
        self.dotsMenu.setSnapshotEnabled(True)

    def model(self):
        return self.thumbWidget.model()

    def refreshThumbs(self, scrollToItemName=-1):
        """ Refreshes the GUI

        :return:
        :rtype:
        """
        self.setUpdatesEnabled(False)
        self.searchWidget.setSearchText("")
        state = self.thumbWidget.state()

        self.model().setUniformItemSizes(self.uniformIcons)

        self.model().refreshList()  # Does the refresh
        self.refreshListView()
        scrollTo = False

        # Select the newest saved
        if self.snapshotWgt.lastSavedLocation is not None:
            snappedName = os.path.basename(os.path.splitext(self.snapshotWgt.lastSavedLocation)[0])
            index = self.model().indexFromText(snappedName)
            if index:
                state['selected'] = index.row()
                scrollTo = True

        if scrollToItemName != -1:  # todo: merge this with above
            state['selected'] = self.model().indexFromText(scrollToItemName).row()

            scrollTo = True

        self.thumbWidget.setState(state, scrollTo=scrollTo)

        self.setUpdatesEnabled(True)
        self.thumbWidget.refresh()

    def toggleInfoVisibility(self):
        """ Toggles the vis of the Information tags section

        :return:
        :rtype:
        """
        currentImage = self.model().currentImage
        if not currentImage:  # no image has been selected
            om2.MGlobal.displayWarning("Please select an asset thumbnail image.")
            return
        vis = not self.infoEmbedWindow.isVisible()
        self.infoEmbedWindow.setEmbedVisible(vis)

        if vis:
            self.savedHeight = self.minimumHeight()
            # Use height of this widget or the embed window plus a little extra
            self.setFixedHeight(max(self.infoEmbedWindow.height() + self.infoEmbedShift,
                                    self.minimumHeight()))
        else:
            self.setFixedHeight(self.savedHeight)

        self.infoToggled.emit(not vis)

        if self.toolsetWidget:
            self.updateToolset(delayed=True)

    def refreshListView(self):
        """ Refresh List View
        Make sure the icons resize correctly

        :return:
        :rtype:
        """
        self.thumbWidget.refresh()

    def invisibleRootItem(self):
        """ Get the invisible root item of the thumbwidget

        :return:
        :rtype:
        """

        return self.thumbWidget.invisibleRootItem()

    def iconSize(self):
        return self.thumbWidget.iconSize()

    def setIconSize(self, size):
        self.thumbWidget.setIconSize(size)

    def filter(self, text, tag=None):
        self.thumbWidget.filter(text, tag)

    def setColumns(self, col):
        """ Reset columns to default

        :param col:
        :type col:
        :return:
        :rtype:
        """
        self.thumbWidget.setColumns(col)

    def setIconMinMax(self, size):
        """ Sets the min and max icon size

        :param size: min and max of the the icon size
        :type size: tuple(int, int)
        """
        self.thumbWidget.setIconMinMax(size)

    def updateToolset(self, delayed=False):
        """ Update the toolset widget if it exists

        :param delayed:
        :type delayed:
        :return:
        :rtype:
        """
        if delayed:
            QtCore.QTimer.singleShot(0, self.updateToolset)
            return
        self.toolsetWidget.treeWidget.setUpdatesEnabled(False)
        self.toolsetWidget.treeWidget.updateTreeWidget()
        self.toolsetWidget.treeWidget.toolsetFrame.window().resizeWindow()
        self.toolsetWidget.treeWidget.updateTreeWidget()  # needs to be done a second time for some reason
        self.toolsetWidget.treeWidget.setUpdatesEnabled(True)

    def newItemFromClipboard(self):
        """ Create new item from clipboard

        :return:
        :rtype:
        """
        clipboard = QtWidgets.QApplication.clipboard()
        mimeData = clipboard.mimeData()

        if mimeData.hasImage():
            px = QtGui.QPixmap(mimeData.imageData())
            name = self.newImageName()
            path = os.path.join(self.directory(), name + ".png")
            px.save(path)
            self.refreshThumbs(scrollToItemName=name)


class ThumbnailSearchWidget(QtWidgets.QWidget):
    searchChanged = QtCore.Signal(object, object)

    def __init__(self, parent=None, themePref=None):
        """ Search Widget for the thumbnail view

        :param parent:
        :type parent:
        :param themePref:
        :type themePref:
        """

        self.themePref = themePref
        super(ThumbnailSearchWidget, self).__init__(parent)

        self.mainLayout = layouts.hBoxLayout()
        toolTip = "Search filter by meta data"
        self.filterMenu = IconMenuButton(parent=self,
                                         color=self.themePref.ICON_PRIMARY_COLOR,
                                         switchIconOnClick=True)
        self.filterMenu.setToolTip(toolTip)  # IconMenuButton must set after
        self.filterMenu.addAction("Name And Tags", icon="filter", data=["filename", "tags"])
        self.filterMenu.addAction("File Name", icon="file", data="filename")
        self.filterMenu.addAction("Description", icon="infoTags", data="description")
        self.filterMenu.addAction("Tags", icon="tag", data="tags")
        self.filterMenu.addAction("Creators", icon="creator", data="creators")
        self.filterMenu.addAction("Websites", icon="web", data="websites")
        self.filterMenu.addAction("All", icon="selectAll",
                                  data=["filename", "tags", "description", "creators", "websites"])

        self.filterMenu.setMenuName("Name And Tags")  # sets the default icon and menu states
        self.filterMenu.setMenuAlign(QtCore.Qt.AlignLeft)

        self.searchEdit = searchwidget.SearchLineEdit(parent=self)
        self.setFixedHeight(utils.dpiScale(22))
        self.searchEdit.setPlaceholderText("Search...")
        self.setLayout(self.mainLayout)

        self.mainLayout.addWidget(self.filterMenu)
        self.mainLayout.addWidget(self.searchEdit)

        self.searchEdit.setBackgroundColor(self.themePref.TEXT_BOX_BG_COLOR)

        self.searchEdit.textChanged.connect(self.onSearchChanged)
        self.filterMenu.actionTriggered.connect(self.onActionTriggered)

    def onSearchChanged(self, text):
        """ On Search Changed

        :param text:
        :type text:
        :return:
        :rtype:
        """
        self.searchChanged.emit(text, self.filterMenuData())

    def filterMenuData(self):
        return self.filterMenu.currentAction().data()

    def onActionTriggered(self, action, mouseMenu):
        self.searchChanged.emit(self.searchEdit.text(), action.data())

    def setSearchText(self, text):
        """ Set the text of the search edit

        :param text:
        :type text:
        :return:
        :rtype:
        """
        self.searchEdit.setText(text)

    def state(self):
        """ Get the state of the widget

        :return:
        :rtype:
        """
        return {"filter": self.filterMenu.currentText(),
                "search": self.searchEdit.text()}

    def setState(self, state):
        """ Set the state of the widget

        :param state:
        :type state:
        :return:
        :rtype:
        """
        # Block signals so we can do it all at once after
        self.blockSignals(True)
        self.filterMenu.setMenuName(state['filter'])
        self.searchEdit.setText(state['search'])
        self.blockSignals(False)
        utils.singleShotTimer(0, partial(self.onSearchChanged, state['search']))


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    applyAction = QtCore.Signal()
    createAction = QtCore.Signal()
    renameAction = QtCore.Signal()
    deleteAction = QtCore.Signal()
    browseAction = QtCore.Signal()
    setDirectoryAction = QtCore.Signal()
    refreshAction = QtCore.Signal()
    uniformIconAction = QtCore.Signal(object)
    snapshotAction = QtCore.Signal()
    snapshotNewAction = QtCore.Signal()
    createThumbnailAction = QtCore.Signal()
    newFromClipboard = QtCore.Signal()

    APPLY_ACTION = 0
    CREATE_ACTION = 1
    RENAME_ACTION = 2
    DELETE_ACTION = 3
    BROWSE_ACTION = 4
    SETDIRECTORY_ACTION = 5
    REFRESH_ACTION = 6
    UNIFORMICON_ACTION = 7
    SNAPSHOT_ACTION = 8
    SNAPSHOTNEW_ACTION = 9
    CREATE_THUMBNAIL_ACTION = 10
    NEWFROMCLIPBOARD_ACTION = 11

    def __init__(self, parent=None, uniformIcons=True, itemName="", applyText="Apply", applyIcon="checkOnly",
                 createText="New", newActive=True, renameActive=True, deleteActive=True, snapshotActive=False,
                 createThumbnailActive=False, itemFromSnapshotActive=False, newClipboardActive=False):
        """This class is the dots menu button and right click menu

        TODO:  Should add right clicks to buttons in an easier way

        :param parent: The Qt Widget parent
        :type parent: MiniBrowser
        """
        self.dotsMenuName = itemName
        self._uniformIcons = uniformIcons
        self.menuActions = None

        self.applyText = applyText
        self.applyIcon = applyIcon
        self.createText = createText
        self.menuActions = OrderedDict()  # type: dict[str, TaggedAction]
        super(DotsMenu, self).__init__(parent=parent)

        self.setCreateActive(newActive)
        self.setRenameActive(renameActive)
        self.setDeleteActive(deleteActive)
        self.setSnapshotActive(snapshotActive)
        self.setFromClipboardActive(newClipboardActive)
        self.setFromSnapShotActive(newClipboardActive)
        self.setCreateThumbnailActive(createThumbnailActive)

    def initUi(self):
        super(DotsMenu, self).initUi()

        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)
        self.setToolTip("File menu. Manage {}".format(self.dotsMenuName))

        applyIcon = iconlib.iconColorized(self.applyIcon, utils.dpiScale(16))
        saveIcon = iconlib.iconColorized("save", utils.dpiScale(16))
        renameIcon = iconlib.iconColorized("editText", utils.dpiScale(16))
        deleteIcon = iconlib.iconColorized("trash", utils.dpiScale(16))
        browseIcon = iconlib.iconColorized("globe", utils.dpiScale(16))
        refreshIcon = iconlib.iconColorized("refresh", utils.dpiScale(16))
        setPrefsIcon = iconlib.iconColorized("addDir", utils.dpiScale(16))
        snapshotIcon = iconlib.iconColorized("cameraSolid", utils.dpiScale(16))

        # New Actions to add
        newActions = \
            [("DoubleClick", ("{} (Double Click)".format(self.applyText), self.applyAction.emit, applyIcon, False)),
             ("---", None),
             (DotsMenu.CREATE_ACTION,
              ("{} {}".format(self.createText, self.dotsMenuName), self.createAction.emit, saveIcon, False)),
             (DotsMenu.RENAME_ACTION,
              ("Rename {}".format(self.dotsMenuName), self.renameAction.emit, renameIcon, False)),
             (DotsMenu.DELETE_ACTION,
              ("Delete {}".format(self.dotsMenuName), self.deleteAction.emit, deleteIcon, False)),
             ("---", None),
             (DotsMenu.SETDIRECTORY_ACTION,
              ("Set {} Dir".format(self.dotsMenuName), self.setDirectoryAction.emit, setPrefsIcon, False)),
             (DotsMenu.BROWSE_ACTION, ("Browse Files", self.browseAction.emit, browseIcon, False)),
             (DotsMenu.REFRESH_ACTION, ("Refresh Thumbnails", self.refreshAction.emit, refreshIcon, False)),
             ("---", None),
             (DotsMenu.UNIFORMICON_ACTION, ("Square Icons", self.uniformActionClicked, None, True)),
             (DotsMenu.SNAPSHOTNEW_ACTION, ("Snapshot New", self.newItemSnapshotMenuClicked, snapshotIcon, False)),
             (DotsMenu.SNAPSHOT_ACTION,
              ("Replace Image (Please select an item)", self.snapshotMenuClicked, snapshotIcon, False)),
             (DotsMenu.NEWFROMCLIPBOARD_ACTION,
              ("New from Clipboard", self.parent().newItemFromClipboard, snapshotIcon, False)),
             (DotsMenu.CREATE_THUMBNAIL_ACTION, ("New Thumbnail", self.createThumbnailAction.emit, applyIcon, False))]

        # Add actions
        for key, value in newActions:
            if value is None and key == "---":  # add separators
                self.addSeparator()
            else:  # otherwise add the actions
                text, connect, icon, checkable = value
                self.menuActions[key] = self.addAction(text, connect=connect, icon=icon, checkable=checkable)

        # Extra settings for the actions
        self.menuActions[DotsMenu.SNAPSHOT_ACTION].setEnabled(False)
        self.menuActions[DotsMenu.UNIFORMICON_ACTION].setChecked(self._uniformIcons)
        self.setMenuAlign(QtCore.Qt.AlignRight)

    def parent(self):
        """

        :return:
        :rtype: MiniBrowser
        """
        return super(DotsMenu, self).parent()

    def uniformActionClicked(self, action):
        """ Uniform action clicked

        :param action:
        :type action: TaggedAction
        :return:
        :rtype:
        """
        self._uniformIcons = action.isChecked()
        self.uniformIconAction.emit(action)

    def snapshotMenuClicked(self):
        """ On snapshot clicked

        :return:
        :rtype:
        """
        self.snapshotAction.emit()
        self.parent().setSnapshotType(MiniBrowser.SNAPTYPE_EDIT)
        self.parent().snapshotWgt.show()

    def newItemSnapshotMenuClicked(self):
        self.snapshotNewAction.emit()
        self.parent().setSnapshotType(MiniBrowser.SNAPTYPE_NEW)
        self.parent().snapshotWgt.show()

    def setActionActive(self, actionId, active):
        self.menuActions[actionId].setVisible(active)

    def setCreateActive(self, active):
        """ Show/Hide new menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.CREATE_ACTION, active)

    def setRenameActive(self, active):
        """ Show/Hide rename menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.RENAME_ACTION, active)

    def setDeleteActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.DELETE_ACTION, active)

    def setSnapshotActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.SNAPSHOT_ACTION, active)

    def setSnapshotEnabled(self, enabled):
        """ Set enabled

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        snapshotAction = self.menuActions[DotsMenu.SNAPSHOT_ACTION]
        snapshotAction.setEnabled(enabled)
        if snapshotAction.isEnabled():
            snapshotAction.setText("Snapshot Replace")
        else:
            snapshotAction.setText("Snapshot Replace (Please select an item)")

    def setFromClipboardActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.NEWFROMCLIPBOARD_ACTION, active)

    def setFromSnapShotActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.SNAPSHOTNEW_ACTION, active)

    def setCreateThumbnailActive(self, active):
        self.setActionActive(DotsMenu.CREATE_THUMBNAIL_ACTION, active)
