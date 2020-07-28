from Qt import QtWidgets, QtCore
from zoo.libs.pyqt import utils


class Menu(QtWidgets.QMenu):
    mouseButtonClicked = QtCore.Signal(object, object)  # emits (mouseButton, QAction)

    def mouseReleaseEvent(self, event):
        """ Emit signal for other mouse events like middle and right click for Menu Items

        :param event:
        :type event: QtGui.QMouseEvent
        :return:
        """
        self.mouseButtonClicked.emit(event.button(), self.actionAt(event.pos()))

        return super(Menu, self).mouseReleaseEvent(event)


# EXTENDED WIDGET MENU CODE


class MenuCreateClickMethods(object):
    def __init__(self):
        """This class can be added to any widget to help add left/right/middle click menus to any widget
        The widget must be extended to support the menus

        To add a menu to a supported extended widget:

            myQMenu =  QtWidgets.QMenu(parent)  # create a menu, need to set it up with menu etc
            zooQtWidget.setMenu(myQMenu, mouseButton=QtCore.Qt.RightButton)  # add menu to the UI with a mouse click

        Or if you are using ExtendedMenu in zoocore_pro, you can easily automatically build the menu items/icons

            myExtMenu =  extendedmenu.ExtendedMenu()  # create an empty zoocore_pro menu (an extended QMenu)
            theMenuModeList = [("menuIcon1", "Menu Item Name 1"),
                                (" menuIcon1  ", " Menu Item Name 2")]  # create the menu names and icons
            zooQtWidget.setMenu(myExtMenu, modeList=theMenuModeList, mouseButton=QtCore.Qt.RightButton)  # add menu

        ExtendedMenu in zoocore_pro can connect when a menu is changed with

            theMenu.menuChanged.connect(runTheMenuFunction)

        Then write a method or function that finds the menu and runs the appropriate code
        (must be a zoocore_pro ExtendedMenu)

            def runTheMenuFunction(self):
                if theMenu.currentMenuItem() == theMenuModeList[0][1]:  # menu item name 1
                    runSomeFunction("firstMenuItemClicked")
                elif theMenu.currentMenuItem() == theMenuModeList[1][1]:  # menu item name 1
                    runSomeFunction("secondMenuItemClicked")

        """
        super(MenuCreateClickMethods, self).__init__()

    def setupMenuClass(self, menuVOffset=20):
        """ The __init__ of this class is not run with multi-inheritance, not sure why, so this is the __init__ code

        :param menuVOffset:  The vertical offset (down) menu drawn from widget top corner.  DPI is handled
        :type menuVOffset: int
        """
        self.menuVOffset = menuVOffset  # offset neg vertical of the menu when drawn, dpi is handled
        # To check of the menu is active
        self.menuActive = {QtCore.Qt.LeftButton: False,
                           QtCore.Qt.MidButton: False,
                           QtCore.Qt.RightButton: False}

        # Store menus into a dictionary
        self.clickMenu = {QtCore.Qt.LeftButton: None,
                          QtCore.Qt.MidButton: None,
                          QtCore.Qt.RightButton: None}

        # Is menu searchable? Not implimented
        self.menuSearchable = {QtCore.Qt.LeftButton: False,
                               QtCore.Qt.MidButton: False,
                               QtCore.Qt.RightButton: False}

    def setMenu(self, menu, modeList=None, mouseButton=QtCore.Qt.RightButton):
        """Add the left/middle/right click menu by passing in a QMenu and assign it to the appropriate mouse click key

        If a modeList is passed in then auto create/reset the menu to the modeList:

            [("icon1", "menuName1"), ("icon2", "menuName2")]

        If no modelist the menu won't change

        :param menu: the Qt menu to show on middle click
        :type menu: QtWidgets.QMenu
        :param modeList: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        self.clickMenu[mouseButton] = menu
        self.menuActive[mouseButton] = True
        # setup the connection
        if modeList:
            self.addActionList(modeList, mouseButton=mouseButton)

    def contextMenu(self, mouseButton):
        """Draw the menu depending on mouse click

        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        menu = self.getMenu(mouseButton=mouseButton)
        # Show menu
        if menu is not None and self.menuActive[mouseButton]:
            self.setFocus()
            parentPosition = self.mapToGlobal(QtCore.QPoint(0, 0))
            # TODO: Should auto find the height of the QLineEdit
            pos = parentPosition + QtCore.QPoint(0, utils.dpiScale(self.menuVOffset))
            menu.exec_(pos)

    def getMenu(self, mouseButton=QtCore.Qt.RightButton):
        """Get menu depending on the mouse button pressed

        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        :return: The requested menu
        :rtype: QtWidgets.QMenu
        """
        return self.clickMenu[mouseButton]

    def addActionList(self, modes, mouseButton=QtCore.Qt.RightButton):
        """resets the appropriate menu with the incoming modes,
        Note: Use this method only if the menu is an ExtendedMenu from zoocore_pro

        modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]

        resets the lists and menus:

            self.menuIconList: ["icon1", "icon2", "icon3"]
            self.menuIconList: ["menuName1", "menuName2", "menuName3"]

        :param modes: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modes: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        menu = self.getMenu(mouseButton=mouseButton)
        if menu is not None:
            menu.actionConnectList(modes)  # this only exists in ExtendedMenu which is not in zoocore
