from Qt import QtWidgets, QtCore, QtGui

from zoo.apps.toolsetsui import registry
from zoo.apps.toolsetsui.widgets import toolsettoolbar, toolsettree
from zoo.apps.toolsetsui.widgets import toolsetwidgetitem
from zoo.apps.toolsetsui.widgets.menubutton import ToolsetMenuButton
from zoo.libs.pyqt import utils as qtutils, utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import iconmenu


class ToolsetFrame(QtWidgets.QFrame):
    """ ToolsetFrame which has the main body of the toolset ui.

    Includes the toolbar
    (:class:`zoo.apps.toolsetsui.widgets.toolsettoolbar.ToolsetToolBar`)

    which is moved to the frameless window header area later
    (:class:`zoo.apps.toolsetsui.widgets.frameless.FramelessTitleBar`),


    """
    resizeRequested = QtCore.Signal()
    toolsetToggled = QtCore.Signal()

    def __init__(self, parent, toolsetRegistry, iconColour=(255, 255, 255), hueShift=-30, showMenuBtn=True,
                 initialGroup=None, iconSize=20, iconPadding=2, startHidden=False):
        """ Initialise ToolsetFrame which has the main body of the toolset ui. Includes
        the toolbar which is moved to the frameless window header area later, and the
        toolset menus.

        Usage. Place frame in intended area for toolbar, and move the tree into the desired layout location

        :param toolsetUi:
        :type toolsetUi: zoo.apps.toolsetsui.toolsetui.ToolsetsUI
        :param toolsetRegistry:
        :type toolsetRegistry: registry.ToolsetRegistry

        :param iconColour:
        :param hueShift:
        """
        super(ToolsetFrame, self).__init__(parent=parent)
        if startHidden:
            self.hide()
        self.toolsetRegistry = toolsetRegistry
        self.mainLayout = elements.vBoxLayout(self)
        self.topbarLayout = elements.hBoxLayout()
        self.toolbar = toolsettoolbar.ToolsetToolBar(toolbarFrame=self, parent=self, toolsetRegistry=self.toolsetRegistry,
                                                     iconSize=iconSize, iconPadding=iconPadding)
        self.tree = toolsettree.ToolsetTreeWidget(self, self.toolsetRegistry)
        self.currentGroup = None  # type: str  # groupType as string
        self.menuBtn = ToolsetMenuButton(self, size=16, toolsetRegistry=self.toolsetRegistry)
        self.menuBtn.setVisible(showMenuBtn)

        self.iconColor = iconColour
        self.hueShift = hueShift

        self.toolsetUi = self.window()

        # Set to first
        self.setGroup(initialGroup or self.toolsetRegistry.groupTypes()[0])

        self.initUi()
        self.initMenuBtn()

    def initMenuBtn(self):
        self.menuBtn.setMenuAlign(QtCore.Qt.AlignRight)

    def initUi(self):
        """ Initialise UI

        :return:
        """
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setIconSize(18)
        self.toolbar.setIconPadding(1)
        self.toolbar.flowLayout.setSpacingY(utils.dpiScale(3))
        self.topbarLayout.addWidget(self.toolbar)
        self.topbarLayout.setContentsMargins(0, 0, 0, 0)

        self.topbarLayout.addSpacing(qtutils.dpiScale(5))

        self.menuBtn.setMenuAlign(QtCore.Qt.AlignRight)
        self.mainLayout.addLayout(self.topbarLayout)
        self.mainLayout.addWidget(self.tree)

    def toolset(self, name):
        """ Retrieves toolset object in the toolsetTree by its name if it exists

        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """

        return self.tree.toolset(name)

    def calcSizeHint(self):
        """ Calculate height based on the contents of the tree
        :rtype self.mainLayout:
        :return:
        """
        size = self.sizeHint()
        width = size.width()
        height = self.tree.calculateContentHeight()
        return QtCore.QSize(width, height)

    def lastHidden(self):
        return self.tree.lastHidden

    def setGroup(self, groupType):
        """ Update the icons in the toolbar based on groupType.
        Toolset groups are found in toolsetgroups.py

        :param groupType: If group type is none, just get currently selected in ui
        :return:
        """

        if self.currentGroup == groupType:
            # If its already the same group then just return
            return

        self.toolbar.clear()
        toolsets = self.toolsetRegistry.toolsets(groupType)
        color = self.toolsetRegistry.groupColor(groupType)
        self.currentGroup = groupType

        self.iconColor = color

        # Add new button
        for t in toolsets:
            self.addToolset(t)

        QtCore.QTimer.singleShot(0, self.forceRefresh)

    def forceRefresh(self):
        """ Force window refresh

        :return:
        :rtype:
        """
        QtWidgets.QApplication.processEvents()  # To make sure the toolbar dimensions is updated first
        self.toolbar.updateWidgetsOverflow()
        self.setUpdatesEnabled(False)
        # Hacky way of forcing a refresh since window().updateGeometry() isn't enough
        size = self.window().size()
        self.window().setUpdatesEnabled(False)
        self.window().resize(size.width()+1, size.height())
        self.window().resize(size.width(), size.height())
        self.window().setUpdatesEnabled(True)
        self.setUpdatesEnabled(True)
        self.updateColors()

    def addToolset(self, toolset):
        """ Add toolset to toolbar

        :param toolset:
        :type toolset: class def or subclass of toolsetwidgetitem.ToolsetWidgetItem
        :return:
        """

        newButton = self.toolbar.addToolset(toolset, toggleConnect=self.toggleToolset)
        newButton.rightClicked.disconnect()
        newButton.rightClicked.connect(lambda: self.toolsetRightClickMenu(newButton.property("toolsetId"), newButton))

    def toolsetRightClickMenu(self, toolsetId, button):
        """ The toolset right click menu

        :param toolsetId:
        :type toolsetId:
        :param button:
        :type button: iconmenu.IconMenuButton
        :return:
        :rtype:
        """

        item = self.toolset(toolsetId)

        # Create an a toolset if no toolset is found. This might be slow on first right click
        if item is None:
            item = self.toggleToolset(toolsetId, hidden=True)

        widget = item.widget
        actions = widget.actions()
        button.clearMenu(QtCore.Qt.RightButton)
        # todo: Maybe this should be done once and not every time theres a right click
        for a in actions:
            button.addAction(a['label'],
                             mouseMenu=QtCore.Qt.RightButton,
                             connect=lambda x=a: widget.executeActions(x),
                             icon=a.get('icon'))

        button.contextMenu(QtCore.Qt.RightButton)

    def toggleToolset(self, toolsetId, activate=True, hidden=False, keepOpen=False):
        """ Add toolset by toolsetId (their ID) or toggle

        This should be moved to toolsetframe

        :param keepOpen: Keep the toolset open
        :type keepOpen: bool
        :param toolsetId: The toolset to add
        :type toolsetId: basestring
        :param activate: Toggle Toolset activated true or flase
        :type activate: bool
        :param hidden: Show the toolset widget hidden
        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """

        item = self.tree.toolset(toolsetId)  # type: ToolsetWidgetItem

        if item:
            if not keepOpen or item.hidden:  # todo: there should be a better way to do this, or maybe rename function
                item.toggleHidden(activate=activate)
        else:
            item = self.tree.addToolset(toolsetId, activate=activate)
            groupType = self.toolsetRegistry.groupFromToolset(toolsetId)
            self.setGroup(groupType)

        # Hide it if we need to
        if hidden:
            item.setHidden(True)

        self.resizeRequested.emit()
        self.toolsetToggled.emit()
        self.updateColors()

        return item

    def setIconColour(self, iconColour):
        """ Set Icon colour

        :param iconColour:
        :type iconColour:
        :return:
        :rtype:
        """
        self.iconColor = iconColour

    def setGroupFromToolset(self, toolsetId):
        """ Sets the group based on toolset ID given

        :param toolsetId:
        :type toolsetId:
        :return:
        :rtype:
        """
        groupType = self.toolsetRegistry.groupFromToolset(toolsetId)
        self.setGroup(groupType)

        utils.singleShotTimer(0, self.groupUpdateUi)

    def groupUpdateUi(self):
        """ Update ui for set group

        :return:
        :rtype:
        """
        self.updateColors()
        self.update()
        utils.processUIEvents()

    def updateColors(self):
        """ Update colors of the toolbar buttons and toolset icon popup

        :return:
        """

        # Get flow toolbar buttons
        widgets = [r.widget() for r in self.toolbar.flowLayout.itemList] + \
                  utils.layoutWidgets(self.toolbar.overflowLayout)

        activeItems = self.tree.activeItems()

        actives = []
        for a in activeItems:
            item = a[0]
            state = a[1]
            if a[1] != toolsettree.ToolsetTreeWidget.ActiveItem_Hidden:
                actives.append(item.widget.id)

        self.menuBtn.toolsetPopup.updateColors(actives)

        # Change colours based on if active
        for w in widgets:
            if w.property('toolsetId') in actives:
                w.setIconColor(tuple(w.property('color')))
            else:
                col = w.property('colorDisabled') or (128, 128, 128)
                w.setIconColor(tuple(col))

    def window(self):
        """ Return the frameless window

        :return:
        :rtype:
        """
        from zoo.libs.pyqt.widgets.frameless import FramelessWindow
        for w in utils.iterParents(self):
            if isinstance(w, FramelessWindow):
                return w















