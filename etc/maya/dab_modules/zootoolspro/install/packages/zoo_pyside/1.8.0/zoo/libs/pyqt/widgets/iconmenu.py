from Qt import QtCore

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets.extendedbutton import ExtendedButton
from zoo.preferences.core import preference

THEME_PREFS = preference.interface("core_interface")


class IconMenuButton(ExtendedButton):
    """
    IconMenuButton is a button that only takes an icon. Clicking it will pop up a context menu.
    Left click, middle click and right click can be customized and added with addAction

    .. code-block:: python

        from zoo.libs import iconlib
        logoButton = IconMenuButton(iconlib.icon("magic", size=32))
        logoButton.setIconSize(QtCore.QSize(24, 24))

        # Add to menu. The menu is automatically created if there is none and placed into
        # self.leftMenu, self.middleMenu or self.rightMenu
        logoButton.addAction("Create 3D Characters")
        logoButton.addSeparator()
        logoButton.addAction("Toggle Toolbars", connect=self.toggleContents)

        # Middle Click and right click menu
        logoButton.addAction("Middle Click Menu", mouseMenu=QtCore.Qt.MidButton)
        logoButton.addAction("Right Click Menu", mouseMenu=QtCore.Qt.RightButton)

        # to query the menu state, the method actionConnect() can be used to create the menu, if so then use
        stateAsAString = logoButton.currentMenuItemStr  # the current menu item name "First Menu Item"
        # or
        stateAsAnInt = logoButton.currentMenuIndexInt  # the current menu as an int ie 0

    Use the function iconMenuButtonCombo() for more convenient usage and documentation

    .. code-block:: python

        from zoo.libs.pyqt.widgets import iconmenu
        iMBtn = iconmenu.iconMenuButtonCombo(modes, defaultMenuItem)

    See the function and documentation for iconMenuButtonCombo() for more information
    """

    def __init__(self, icon=None, iconHover=None, parent=None, doubleClickEnabled=False, color=(255, 255, 255),
                 menuName="", switchIconOnClick=False):
        """See main description

        :param icon: the default icon name
        :type icon: QtGui.QIcon
        :param iconHover: the hover icon name
        :type iconHover: str
        :param parent: the parent widget
        :type parent: qObject
        :param doubleClickEnabled: does the button have a double click state?
        :type doubleClickEnabled: bool
        :param color: The color of the main icon on the button
        :type color: tuple
        :param menuName: the current state of the menu as a string ie. "Arnold" if it were the renderer set
        :type menuName: str
        """
        super(IconMenuButton, self).__init__(icon=icon, iconHover=iconHover, parent=parent,
                                             doubleClickEnabled=doubleClickEnabled)
        self.initUi()
        self.iconColor = color
        self._currentText = menuName
        self.actionTriggered.connect(self.menuItemClicked)
        self.switchIcon = switchIconOnClick

    def initUi(self):
        for m in self.clickMenu.values():
            if m is not None:
                m.setToolTipsVisible(True)
        self.setMenuAlign(QtCore.Qt.AlignRight)

    # TODO: most of these methods can be moved to extended button and add support for right and middle click menus
    def currentText(self):
        """Returns the current selected menu name (current menu name related to the main icon)

        :rtype: basestring
        """
        return self._currentText


    def text(self):
        """ Same as currentText() to avoid confusion

        :return:
        :rtype:
        """
        return self._currentText

    def currentAction(self, mouseMenu=QtCore.Qt.LeftButton):
        """

        :param mouseMenu:
        :type mouseMenu:
        :return:
        :rtype: QtWidgets.QAction
        """
        for a in self.actions(mouseMenu):
            if a.text() == self._currentText:
                return a

    def currentMenuIndex(self, mouseMenu=QtCore.Qt.LeftButton):
        """Returns the current selected menu index (current menu number related to the main icon)

        :return self.currentMenuIndexInt: The current index menu item (of the current icon)
        :rtype self.currentMenuIndexInt: int
        """
        return self.index(self.currentText(), mouseMenu)

    def menuItemClicked(self, action, mouseMenu):
        """ Switch the icon when clicking a menu item

        :param action:
        :type action:
        :param mouseMenu:
        :type mouseMenu:
        :return:
        :rtype:
        """
        self.setMenuName(action.text())

    def setMenuName(self, name, mouseMenu=QtCore.Qt.LeftButton):
        """ Sets the main icon and menu states by the menuItem name

        Menu items must already be created.

        :param name: the name of the menu item to set
        :type name: str
        :param mouseMenu:
        :type mouseMenu:
        """
        for i, a in enumerate(self.actions(mouseMenu)):
            if a.text() == name:
                self._currentText = a.text()
                if self.switchIcon:
                    self.setIconByName(a.iconText(), colors=self.iconColor)
                break

    def actionConnectList(self, modeList, mouseMenu=QtCore.Qt.LeftButton):
        """Creates the entire menu with icons from the modeList:

            modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]

        Automatically creates the actions and menu states so they can be queried later
        Also changes the main icon auto with the menu actions
        Creates/recreates/resets self.menuItemStrList and self.menuIconList lists

        :param modeList: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        """
        for i, action in enumerate(modeList):
            icon = action[0]
            name = action[1]
            self.addAction(name, mouseMenu=mouseMenu, icon=icon)

        firstName = modeList[0][1]  # Assumes first one is the default
        self.setMenuName(firstName)


def iconMenuButtonCombo(menuItems, defaultMenuItem, color=THEME_PREFS.ICON_PRIMARY_COLOR, parent=None,
                        width=uic.BTN_W_ICN_MED, height=24, toolTip="", switchIconOnClick=True,
                        setDefaultIconByName=""):
    """ Creates an IconMenuButton in a combo box style, like a combo box with an icon instead,
    works with left click and a regular menu

    The following creates a menu with icons, the defaultMenuItem is the item set by default and should match the menu:

        modes = [("arnoldIcon", "Arnold"),
                ("redshiftIcon", "Redshift"),
                ("rendermanIcon", "Renderman")]
        defaultMenuItem = "Redshift"

    To create an icon menu button:

        from zoo.libs.pyqt.widgets import iconmenu
        iMBtn = iconmenu.iconMenuButtonCombo(modes, defaultMenuItem)

    Menu changes are emitted with itemChanged:

        iMBtn.itemChanged.connect(runFunctionMethod)

    To query the current menu selection use:

        menuSelection = iMBtn.currentMenuItem()  # is the current menu item name ie "Arnold"
        # or
        menuSelectionNumber = iMBtn.logoButton.currentMenuIndex()  # is the current menu as an int ie 0

    To set the icon and related menu states, set with it's Menu item name (not icon name):

        iMBtn.setMenuName("Arnold")

    setMenuName() will not trigger a menu change (itemChanged)

    :param menuItems: A list of tuples, tuples are (iconName, menuItemName)
    :type menuItems: list(tuples)
    :param defaultMenuItem: the name of the icon to set as the default state
    :type defaultMenuItem: str
    :param color: Color of the main icon in 255 rgb color (255, 0, 0). Defaults to the theme prefs primary icon color
    :type color: tuple
    :param parent: the parent widget
    :type parent: QWidget
    :param width: the size of the icon
    :type width: int
    :param toolTip: the toolTip on mouse hover
    :type toolTip: str
    :return iconCBtn: the iconCBtn widget
    :rtype iconCBtn: IconMenuButton
    """
    iconCBtn = IconMenuButton(parent=parent, color=color, switchIconOnClick=switchIconOnClick)
    iconCBtn.actionConnectList(menuItems)  # adds the actions and menu items
    iconCBtn.setFixedSize(QtCore.QSize(width, height))
    iconCBtn.setToolTip(toolTip)
    if setDefaultIconByName:  # can set any icon, useful if switchIconOnClick = False, icon doesn't change
        iconCBtn.setIconByName(setDefaultIconByName)
    else:
        iconCBtn.setMenuName(defaultMenuItem)  # sets the default icon and menu states by the menu item name
    utils.setStylesheetObjectName(iconCBtn, "DefaultButton")
    return iconCBtn
