from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants
from zoo.libs.pyqt.extended import searchablemenu
from zoo.libs.pyqt.extended.searchablemenu import action as taggedAction


class ExtendedMenu(searchablemenu.SearchableMenu):
    menuChanged = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        """Extends the searchable menu, adding automatic menu generation and menu state management,
        menu can be queried like a comboBox finding the "last clicked" (current state) menu item

        self.actionConnectList(modeList) creates a menu with icons, the defaultMenuItem should match a menu item name:

            modes = [("arnoldIcon", "Arnold"),
                    ("redshiftIcon", "Redshift"),
                    ("rendermanIcon", "Renderman")]
            defaultMenuItem = "Redshift"

        Menu changes are emitted with itemChanged, to catch the change in a UI use:

            menu.menuChanged.connect(runFunctionMethod)

        or if you need the menu item name sent then (not tested)

            menu.menuChanged.connect(partial(runFunctionMethod, menu.currentMenuItem()))

        To query the current (last) menu selection use:

            menuSelection = menu.currentMenuItem()  # is the current menu item name ie "Arnold"
            # or
            menuSelectionNumber = menu.currentMenuIndex()  # is the current menu as an int ie 0

        To set the menu state (last clicked) manually in code, set with menu item name (not icon name),
        useful for iconMenuButtons:

            menu.setMenuName("Arnold")
        """
        # TODO: menu should have a stylesheet, is inheriting badly (black) in toolsets, maybe default is same as combo
        searchVisible = kwargs.pop("searchVisible") if kwargs.get("searchVisible", None) is not None else True
        super(ExtendedMenu, self).__init__(*args, **kwargs)
        self.menuItemStrList = list()
        self.menuIconList = list()
        self.currentMenuItemStr = ""
        self.currentMenuIndexInt = 0
        self.setSearchVisible(searchVisible)
        self.setStyleSheet("* {menu-scrollable: 1;}")  # scrollable menu behaviour. Doesn't seem to work when put in qss

    def currentMenuItem(self):
        """Returns the current selected menu name (current menu name related to the main icon)

        :return self.currentMenuIndexInt: The current menu name (of the current icon)
        :rtype self.currentMenuIndexInt: str
        """
        return self.currentMenuItemStr

    def currentMenuIndex(self):
        """Returns the current selected menu index (current menu number related to the main icon)

        :return self.currentMenuIndexInt: The current index menu item (of the current icon)
        :rtype self.currentMenuIndexInt: int
        """
        return self.currentMenuIndexInt

    def setCurrentMenuItem(self, currentMenuItem):
        """Sets both menu states by the menu item name, does not trigger a menu action.

        Sets the following variables:

            self.currentMenuItemStr: the current menu name as a string
            self.currentMenuIndexInt: the current menu item as a int

        :param currentMenuItem: The name of a single menu name (one item in the menu)
        :type currentMenuItem: str
        """
        self.currentMenuItemStr = currentMenuItem
        self.currentMenuIndexInt = self.menuItemStrList.index(currentMenuItem)

    def setCurrentMenuIndex(self, currentMenuIndexInt):
        """Sets both menu states by the menu item index, does not trigger a menu action.

        Sets the following variables:

            self.currentMenuItemStr: the current menu name as a string
            self.currentMenuIndexInt: the current menu item as a int

        :param currentMenuIndexInt: The current index menu item (of the current icon)
        :type currentMenuIndexInt: int
        """
        self.currentMenuIndexInt = currentMenuIndexInt
        self.currentMenuItemStr = self.menuItemStrList[currentMenuIndexInt]

    def stringToTags(self, string):
        """Break down string to tags so it is easily searchable

        :param string:
        :return:
        """
        ret = []
        ret += string.split(" ")
        ret += [s.lower() for s in string.split(" ")]

        return ret

    def iconAndMenuNameLists(self, modeList):
        """from the modeList set the self.menuItemStrList and self.menuIconList:

            modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]

        resets the lists:

            self.menuIconList: ["icon1", "icon2", "icon3"]
            self.menuIconList: ["menuName1", "menuName2", "menuName3"]

        :param modeList: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        """
        self.menuItemStrList = list()
        self.menuIconList = list()
        for i, m in enumerate(modeList):
            self.menuItemStrList.append(m[1])
            self.menuIconList.append(m[0])

    def addActionExtended(self, name, connect=None, checkable=False, checked=True, action=None, icon=None):
        """Builds a new single menu item through an action, will add icon, menu item name, connection function etc.

        :param name: The text for the new menu item
        :type name: str
        :param connect: The function to connect when the menu item is pressed
        :type connect: object
        :param checkable: If the menu item is checkable
        :type checkable: bool
        :param checkable: If the menu item is checkable
        :type checkable: bool
        :param action: set the action directly, will ignore other kwargs
        :type action: taggedAction.TaggedAction
        :param icon: set the icon for the menu item by name
        :type icon: str
        :return newAction: The new action if one was created
        :rtype newAction: taggedAction.TaggedAction
        """
        # temporarily disabled isSearchable due to c++ error
        # rememberSearchVisible = self.searchVisible()
        # self.setSearchVisible(False)

        if action is not None:
            self.addAction(action)
            # self.setSearchVisible(rememberSearchVisible)  # return search mode
            return

        newAction = taggedAction.TaggedAction(name, parent=self)
        newAction.setCheckable(checkable)
        newAction.setChecked(checked)
        newAction.tags = set(self.stringToTags(name))
        self.addAction(newAction)

        if icon is not None:
            newAction.setIcon(icon)

        if connect is not None:
            if checkable:
                newAction.triggered.connect(partial(connect, newAction))
            else:
                newAction.triggered.connect(connect)

        # self.setSearchVisible(rememberSearchVisible)  # return search mode
        return newAction

    def actionConnectList(self, modeList, defaultMenuItem=None):
        """Creates the entire menu with optional icons from the modeList:

            modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]
            or
            modeList: [(None, "menuName1"), (None, "menuName2"), (None, "menuName3")]

            Separators should be passed in as (None, "separator")

        Automatically creates the actions and menu states so they can be queried later
        Creates/recreates/resets self.menuItemStrList and self.menuIconList lists

        :param modeList: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        """
        self.clear()
        self.iconAndMenuNameLists(modeList)  # sets up or creates self.menuIconList & self.menuIconList
        for i, menuItemName in enumerate(self.menuItemStrList):
            if menuItemName != "separator":
                self.addActionExtended(menuItemName,
                                       connect=partial(self.actionConnect,
                                                       iconName=self.menuIconList[i],
                                                       currentMenuItem=menuItemName,
                                                       currentMenuIndex=i),
                                       icon=iconlib.iconColorized(self.menuIconList[i]))
            else:
                self.addSeparator()
        if defaultMenuItem is None:
            self.currentMenuItemStr = self.menuItemStrList[0]
            self.currentMenuIndexInt = 0

    def actionConnect(self, iconName, currentMenuItem, currentMenuIndex):
        """Creates a default for a single IconMenuButton menu item ie one menu entry not the whole menu

        Sets the icon to switch when a menu item is clicked, also sets the menuState as an int and str:

            iconName:  the icon that will be changed to when the menu is clicked
            currentMenuItem: usually the current menu name, ie "Arnold" if that renderer is set as the main icon
            currentMenuIndex: the current state of the menu as an int, 0 being the first menu item

        :param currentMenuItem: the current state of the menu, ie "Arnold" renderer, used querying the button state
        :type currentMenuItem: str
        :param currentMenuIndex: the current state of the menu as an int used while querying the button state
        :type currentMenuIndex: int
        :return self.currentMenuItemStr: the current state of the menu, used querying the button state
        :rtype self.currentMenuItemStr: str
        :return self.currentMenuIndexInt: the current state of the menu as an int used while querying the button
        :rtype self.currentMenuIndexInt: int
        """
        self.currentMenuItemStr = currentMenuItem
        self.currentMenuIndexInt = currentMenuIndex
        self.menuChanged.emit()
