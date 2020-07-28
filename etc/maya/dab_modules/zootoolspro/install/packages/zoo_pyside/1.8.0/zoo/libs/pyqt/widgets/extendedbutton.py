from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from zoo.libs import iconlib
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.extended import searchablemenu, menu
from zoo.libs.pyqt.widgets import expandedtooltip, dpiscaling
from zoo.libs.pyqt.extended.searchablemenu import action as taggedAction
from zoo.libs.utils import zlogging
from zoovendor.six import string_types


logger = zlogging.getLogger(__name__)


class ButtonIcons(QtWidgets.QAbstractButton):
    """Set up the icons that change on mouse over, press and release. Inherit from this class to have icons

    .. code-block:: python

        class ExtendedButton(QtWidgets.QPushButton, ButtonIcons):
        class ExtendedButton(QtWidgets.QToolButton, ButtonIcons):

    Must be placed after the button.

    """
    highlightOffset = 40
    iconNames = None
    iconColors = (128, 128, 128)
    iconScaling = []

    buttonIcon = None
    buttonIconPressed = None
    buttonIconHover = None

    def setHighlight(self, highlight):
        self.highlightOffset = highlight

    def setIconByName(self, iconNames, colors=None, size=None, colorOffset=None, tint=None,
                      tintComposition=QtGui.QPainter.CompositionMode_Plus, iconScaling=None, grayscale=False):
        """Set up both icons in a simple function

        :param iconNames: name of the icon
        :type iconNames: basestring or list
        :param colors: the icon regular color
        :type colors: tuple or list or None
        :param size: Size is dpiScaled automatically here, but can be passed in
        :type size: int
        :param colorOffset: the amount of tint white highlight that's added when mouse over hover 0-255
        :type colorOffset: int
        :param iconScaling: the icon's scale
        :type iconScaling: list of int or int
        """
        if size is not None:
            self.setIconSize(QtCore.QSize(size, size))

        if colorOffset is not None:
            self.highlightOffset = colorOffset

        if iconScaling is not None:
            self.iconScaling = iconScaling

        self.tint = (255, 0, 0, 100)
        colors = colors or self.iconColors
        self.grayscale = grayscale
        self.tintComposition = tintComposition

        self.iconNames = iconNames
        self.setIconColor(colors, update=False)
        self.updateIcons()

    def setIconColor(self, colors, update=True):
        self.iconColors = colors
        if update and self.buttonIcon is not None and self.iconNames is not None:
            self.updateIcons()

    def updateIcons(self):
        if self.iconNames is None or self.iconNames == []:
            # Icon name is none? should mean the button is not ready yet
            return

        hoverCol = (255, 255, 255, self.highlightOffset)

        self.buttonIcon = iconlib.iconColorizedLayered(self.iconNames,
                                                       size=self.iconSize().width(),
                                                       iconScaling=self.iconScaling,
                                                       tintComposition=self.tintComposition,
                                                       colors=self.iconColors, grayscale=self.grayscale)
        self.buttonIconHover = iconlib.iconColorizedLayered(self.iconNames,
                                                            size=self.iconSize().width(),
                                                            colors=self.iconColors,
                                                            tintComposition=self.tintComposition,
                                                            iconScaling=self.iconScaling,
                                                            tintColor=hoverCol, grayscale=self.grayscale)

        self.setIcon(self.buttonIcon)

    def setIconSize(self, size):
        """ Set icon size

        :param size:
        :return:
        """
        if self.iconNames is None:
            return

        super(ButtonIcons, self).setIconSize(utils.sizeByDpi(size))
        self.updateIcons()

    def setIconIdle(self, icon):
        """Set the button Icon when idle or default.

        :param icon:
        :return:
        """
        self.buttonIcon = icon
        self.setIcon(icon)

    def setIconHover(self, iconHover):
        """Set the button icon for when mouse hovers over

        :param iconHover:
        :return:
        """
        self.buttonIconHover = iconHover

    def enterEvent(self, event):
        """Button Hover on mouse enter

        :param event:
        :return:
        """
        if self.buttonIconHover is not None:
            self.setIcon(self.buttonIconHover)

    def leaveEvent(self, event):
        """Button Hover on mouse leave

        :param event:
        :return:
        """
        if self.buttonIcon is not None:
            self.setIcon(self.buttonIcon)


class ExtendedButton(QtWidgets.QPushButton, ButtonIcons):
    """
    Push Button that allows you to have the left click, middle click, and right click.

    Each click allows for a menu

    .. code-block:: python

        # You can use it in a similar fashion to QPushbutton
        ExtendedButton(icon=iconlib.iconColorized("magic", size=32, color=(128,128,128)),
                       iconHover=iconlib.iconColorized("magic", size=32, color=(255,255,255)))

        # Set the hover through the constructor like above or simply set the iconName and offset

    """

    leftClicked = QtCore.Signal()
    middleClicked = QtCore.Signal()
    rightClicked = QtCore.Signal()

    leftDoubleClicked = QtCore.Signal()
    middleDoubleClicked = QtCore.Signal()
    rightDoubleClicked = QtCore.Signal()
    clicked = leftClicked

    menuAboutToShow = QtCore.Signal()
    middleMenuAboutToShow = QtCore.Signal()
    rightMenuAboutToShow = QtCore.Signal()

    menuChanged = QtCore.Signal()
    middleMenuChanged = QtCore.Signal()
    rightMenuChanged = QtCore.Signal()

    SINGLE_CLICK = 1
    DOUBLE_CLICK = 2

    highlightOffset = 40
    actionTriggered = QtCore.Signal(object, object)

    def __init__(self, icon=None, iconHover=None,
                 text=None, parent=None,
                 doubleClickEnabled=False):
        """

        :param icon:
        :param iconHover: Note this already gets set in setIconByName(), only use this if you want to have something different
        :param text:
        :param parent:
        :param doubleClickEnabled:
        """

        self.buttonIcon = icon
        self.buttonIconHover = iconHover
        # 2020 temp fix
        if not self.buttonIcon:
            self.buttonIcon = QtGui.QIcon()

        super(ExtendedButton, self).__init__(icon=self.buttonIcon, text=text, parent=parent)

        # To check of the menu is active
        self.menuActive = {QtCore.Qt.LeftButton: True,
                           QtCore.Qt.MidButton: True,
                           QtCore.Qt.RightButton: True}

        # Store menus into a dictionary
        self.clickMenu = {QtCore.Qt.LeftButton: None,
                          QtCore.Qt.MidButton: None,
                          QtCore.Qt.RightButton: None}  # type: dict[searchablemenu.SearchableMenu]

        # Is menu searchable?
        self.menuSearchable = {QtCore.Qt.LeftButton: False,
                               QtCore.Qt.MidButton: False,
                               QtCore.Qt.RightButton: False}

        self.menuPadding = 5

        self.menuAlign = QtCore.Qt.AlignLeft

        self.leftClicked.connect(partial(self.contextMenu, QtCore.Qt.LeftButton))
        self.middleClicked.connect(partial(self.contextMenu, QtCore.Qt.MidButton))
        self.rightClicked.connect(partial(self.contextMenu, QtCore.Qt.RightButton))

        self.doubleClickInterval = uiconstants.DOUBLE_CLICK_INTERVAL  # 500
        self.doubleClickEnabled = doubleClickEnabled
        self.lastClick = None
        self.iconColor = None

    def actions(self, mouseMenu=QtCore.Qt.LeftButton):
        """ Get the actions of a mouse menu

        :param mouseMenu:
        :type mouseMenu:
        :return:
        :rtype: list of QtWidgets.QAction
        """

        return self.clickMenu[mouseMenu].actions()[2:]  # Ignore search widget and separator

    def setDoubleClickInterval(self, interval=150):
        """
        Sets the interval of the double click, defaults to 150

        :param interval:
        :return:
        """
        self.doubleClickInterval = interval

    def setDoubleClickEnabled(self, enabled):
        """
        Enables double click signals for this widget

        :param enabled:
        :return:
        """
        self.doubleClickEnabled = enabled

    def setWindowTitle(self, windowTitle, mouseMenu=QtCore.Qt.LeftButton):
        """Set the window title of the menu, if it gets teared off

        :param windowTitle:
        :param mouseMenu:
        :return:
        """
        menu = self.menu(mouseMenu, searchable=self.isSearchable(mouseMenu))
        menu.setWindowTitle(windowTitle)

    def setTearOffEnabled(self, mouseMenu=QtCore.Qt.LeftButton, tearoff=True):
        """Set the tear off enabled

        :param mouseMenu:
        :param tearoff:
        :param windowTitle:
        :return:
        """
        menu = self.menu(mouseMenu, searchable=self.isSearchable(mouseMenu))
        menu.setTearOffEnabled(tearoff)

    def setMenu(self, menu, mouseButton=QtCore.Qt.LeftButton):
        """ Sets the menu based on mouse button

        :param menu:
        :type menu: QtWidgets.QMenu
        :param mouseButton:
        :return:
        """
        self.clickMenu[mouseButton] = menu

    def _aboutToShow(self, mouseButton):
        if mouseButton == QtCore.Qt.LeftButton:
            self.menuAboutToShow.emit()
        elif mouseButton == QtCore.Qt.MiddleButton:
            self.middleMenuAboutToShow.emit()
        elif mouseButton == QtCore.Qt.RightButton:
            self.rightMenuAboutToShow.emit()

    def _menuChanged(self, mouseButton, object):
        if mouseButton == QtCore.Qt.LeftButton:
            self.menuChanged.emit()
        elif mouseButton == QtCore.Qt.MiddleButton:
            self.middleMenuChanged.emit()
        elif mouseButton == QtCore.Qt.RightButton:
            self.rightMenuChanged.emit()

    def setFixedHeight(self, height):
        """ DpiScaling version of set fixed height

        :param height:
        :return:
        """
        return super(ExtendedButton, self).setFixedHeight(utils.dpiScale(height))

    def setFixedWidth(self, width):
        """ DpiScaling version of set fixed width

        :param width:
        :return:
        """
        return super(ExtendedButton, self).setFixedWidth(utils.dpiScale(width))

    def setFixedSize(self, size):
        """ Set the fixed size

        :param size: New fixed size of the widget
        :type size: QtCore.QSize

        :return:
        """
        super(ExtendedButton, self).setFixedSize(utils.sizeByDpi(size))

    def setSearchable(self, mouseMenu=QtCore.Qt.LeftButton, searchable=True):
        self.menuSearchable[mouseMenu] = searchable

        if self.clickMenu[mouseMenu] is not None:
            self.clickMenu[mouseMenu].setSearchVisibility(searchable)

    def isSearchable(self, mouseMenu=QtCore.Qt.LeftButton):
        """ Checks if the button menu is searchable or not.

        :param mouseMenu:
        :return:
        """
        if self.clickMenu[mouseMenu] is not None:
            return self.clickMenu[mouseMenu].searchVisible()

        return self.menuSearchable[mouseMenu]

    def setMenuAlign(self, align=QtCore.Qt.AlignLeft):
        self.menuAlign = align

    def clearMenu(self, mouseMenu=QtCore.Qt.LeftButton):
        """Clears specified menu

        :param mouseMenu: QtCore.Qt.LeftButton, QtCore.Qt.MidButton, QtCore.Qt.RightButton
        :return:
        """

        if self.clickMenu[mouseMenu] is not None:
            self.clickMenu[mouseMenu].clear()

    def mousePressEvent(self, event):
        """ Mouse set down button visuals

        :param event:
        :return:
        """
        if event.button() == QtCore.Qt.MidButton:
            self.setDown(True)
        elif event.button() == QtCore.Qt.RightButton:
            self.setDown(True)

        self.lastClick = self.SINGLE_CLICK

    def mouseReleaseEvent(self, event):
        """Mouse release event plays the menus

        :param event:
        :return:
        """
        button = event.button()
        self.setDown(False)

        # Single Clicks Only
        if not self.doubleClickEnabled:
            self.mouseSingleClickAction(button)
            return

        # Double clicks
        if self.lastClick == self.SINGLE_CLICK:
            QtCore.QTimer.singleShot(self.doubleClickInterval,
                                     lambda: self.mouseSingleClickAction(button))
        else:
            self.mouseDoubleClickAction(event.button())

    def mouseSingleClickAction(self, button):
        """The actual single click action

        :param button:
        :return:
        """
        if self.lastClick == self.SINGLE_CLICK or self.doubleClickEnabled is False:
            if button == QtCore.Qt.LeftButton:
                self.leftClicked.emit()
            elif button == QtCore.Qt.MidButton:
                self.middleClicked.emit()
            elif button == QtCore.Qt.RightButton:
                self.rightClicked.emit()

    def mouseDoubleClickAction(self, button):
        """The actual double click Action

        :param button:
        :return:
        """
        if button == QtCore.Qt.LeftButton:
            self.leftDoubleClicked.emit()
        elif button == QtCore.Qt.MidButton:
            self.middleDoubleClicked.emit()
        elif button == QtCore.Qt.RightButton:
            self.rightDoubleClicked.emit()

    def mouseDoubleClickEvent(self, event):
        """
        Detects Double click event.

        :param event:
        :return:
        """
        self.lastClick = self.DOUBLE_CLICK

    def contextMenu(self, mouseButton):
        """Run context menu depending on mouse button

        :param mouseButton:
        :return:
        """

        menu = self.clickMenu[mouseButton]

        # Show menu
        if menu is not None and self.menuActive[mouseButton]:
            self._aboutToShow(mouseButton)
            pos = self.menuPos(widget=menu, align=self.menuAlign)
            menu.exec_(pos)
            menu.searchEdit.setFocus()

    def menuPos(self, align=QtCore.Qt.AlignLeft, widget=None):
        """Get menu position based on the current widget position and perimeter

        :param align: Align the menu left or right
        :type align: QtCore.Qt.AlignLeft or QtCore.Qt.AlignRight
        :param widget: The widget to calculate the width based off. Normally it is the menu
        :type widget: QtWidgets.QWidget
        :return:
        """
        pos = 0

        if align == QtCore.Qt.AlignLeft:
            point = self.rect().bottomLeft() - QtCore.QPoint(0, -self.menuPadding)
            pos = self.mapToGlobal(point)
        elif align == QtCore.Qt.AlignRight:
            point = self.rect().bottomRight() - QtCore.QPoint(widget.sizeHint().width(), -self.menuPadding)
            pos = self.mapToGlobal(point)

        return pos

    def menu(self, mouseMenu=QtCore.Qt.LeftButton, searchable=False, autoCreate=True):
        """Get menu depending on the mouse button pressed

        :param mouseMenu:
        :return: The requested menu
        :rtype: ExtendedButtonMenu
        """

        if self.clickMenu[mouseMenu] is None and autoCreate:
            self.clickMenu[mouseMenu] = ExtendedButtonMenu(objectName="extendedButton", title="Extended Button")
            self.clickMenu[mouseMenu].triggered.connect(lambda action: self.actionTriggered.emit(action, mouseMenu))
            self.clickMenu[mouseMenu].triggered.connect(partial(self._menuChanged, mouseMenu))
            if not searchable:
                self.clickMenu[mouseMenu].setSearchVisible(False)

        return self.clickMenu[mouseMenu]

    def index(self, name, mouseMenu=QtCore.Qt.LeftButton):
        """ Gets the index of the menu item or action name

        :param name:
        :type name:
        :param mouseMenu:
        :type mouseMenu:
        :return:
        :rtype:
        """
        return self.menu(mouseMenu).index(name)

    def addAction(self, name, mouseMenu=QtCore.Qt.LeftButton,
                  connect=None, checkable=False,
                  checked=True, action=None, icon=None, data=None, iconText=None, iconColor=None, iconSize=16):
        """Add a new menu item through an action

        :param mouseMenu: Expects QtCore.Qt.LeftButton, QtCore.Qt.MidButton, or QtCore.Qt.RightButton
        :param name: The text for the new menu item
        :param connect: The function to connect when the menu item is pressed
        :param checkable: If the menu item is checkable
        :param icon:
        :type icon: QtGui.QIcon or basestring

        :return:
        :rtype: taggedAction.TaggedAction

        """

        # temporarily disabled isSearchable due to c++ error
        menu = self.menu(mouseMenu, searchable=False)  # self.isSearchable(mouseMenu))

        if action is not None:
            menu.addAction(action)
            return

        newAction = taggedAction.TaggedAction(name, parent=menu)
        newAction.setCheckable(checkable)
        newAction.setChecked(checked)
        newAction.tags = set(self.stringToTags(name))
        newAction.setData(data)
        menu.addAction(newAction)

        if icon is not None:
            if isinstance(icon, QtGui.QIcon):
                newAction.setIcon(icon)
                newAction.setIconText(iconText or "")
            elif isinstance(icon, string_types):
                newAction.setIconText(icon or iconText or None)

                newAction.setIcon(iconlib.iconColorizedLayered(icon, colors=[iconColor], size=utils.dpiScale(iconSize)))

        if connect is not None:
            if checkable:
                newAction.triggered.connect(partial(connect, newAction))
            else:
                newAction.triggered.connect(connect)

        return newAction

    def addSeparator(self, mouseMenu=QtCore.Qt.LeftButton):
        """ Add a separator in the menu

        :param mouseMenu:
        :return:
        """
        menu = self.menu(mouseMenu)
        menu.addSeparator()

    def stringToTags(self, string):
        """Break down string to tags so it is easily searchable

        :param string:
        :return:
        """
        ret = []
        ret += string.split(" ")
        ret += [s.lower() for s in string.split(" ")]

        return ret

    def setStyleSheet(self, *args, **kwargs):
        return super(ExtendedButton, self).setStyleSheet(*args, **kwargs)


class ExtendedPushButton(ExtendedButton):

    def __init__(self, *args, **kwargs):
        """ Same as ExtendedButton except with the default style

        :param args:
        :param kwargs:
        """
        super(ExtendedPushButton, self).__init__(*args, **kwargs)
        utils.setStylesheetObjectName(self, "DefaultButton")


class ExtendedButtonMenu(searchablemenu.SearchableMenu):
    def __init__(self, *args, **kwargs):
        super(ExtendedButtonMenu, self).__init__(*args, **kwargs)
        self.ttKeyPressed = False
        self.ttKey = QtCore.Qt.Key_Control

    def keyPressEvent(self, event):
        """ Key press event

        :param event:
        :return:
        """

        # Use expanded tooltips if it has any
        if event.key() == self.ttKey:
            pos = self.mapFromGlobal(QtGui.QCursor.pos())
            action = self.actionAt(pos)
            if expandedtooltip.hasExpandedTooltips(action):
                self._popuptooltip = expandedtooltip.ExpandedTooltipPopup(action, iconSize=utils.dpiScale(40),
                                                                          popupRelease=self.ttKey)
            self.ttKeyPressed = True

        super(ExtendedButtonMenu, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Control:
            self.ttKeyPressed = False

    def index(self, name, excludeSearch=True):
        for i, a in enumerate(self.actions()):
            if a.text() == name:
                ret = i
                if excludeSearch:
                    ret -= 2
                return ret


class ExtendedButtonSimpleMenu(QtWidgets.QPushButton, menu.MenuCreateClickMethods):
    leftClicked = QtCore.Signal()
    middleClicked = QtCore.Signal()
    rightClicked = QtCore.Signal()

    def __init__(self, parent=None, menuVOffset=20):
        """A simple QPushButton with no icons (used by color widgets) that can add right, left middle click menus

        Inherits from QPushButton and MenuCreateClickMethods

        Menus are not added by default they must be set in the ui code. QMenu's can be passed in via setMenu():

            zooQtWidget.setMenu(myQMenu, mouseButton=QtCore.Qt.RightButton)

        Recommended to use zoocore_pro's extendedmenu.ExtendedMenu(). Pass that in instead of a QMenu for extra
        functionality

        See the class docs for elements.MenuCreateClickMethods() for more information

        :param parent: the parent widget
        :type parent: QWidget
        :param menuVOffset: The vertical offset (down) menu drawn from widget top corner.  DPI is handled
        :type menuVOffset: int
        """
        super(ExtendedButtonSimpleMenu, self).__init__(parent=parent)
        self.setupMenuClass(menuVOffset=menuVOffset)
        self.leftClicked.connect(partial(self.contextMenu, QtCore.Qt.LeftButton))
        self.middleClicked.connect(partial(self.contextMenu, QtCore.Qt.MidButton))
        self.rightClicked.connect(partial(self.contextMenu, QtCore.Qt.RightButton))

    def mousePressEvent(self, event):
        """ mouseClick emit, only uses clicks as assigned by the menus

        Checks to see if a menu exists on the current clicked mouse button, if not, use the original Qt behaviour

        :param event: the mouse pressed event from the QLineEdit
        :type event: QEvent
        """
        for mouseButton, menu in iter(self.clickMenu.items()):
            if menu and event.button() == mouseButton:  # if a menu exists and that mouse has been pressed
                if mouseButton == QtCore.Qt.LeftButton:
                    return self.leftClicked.emit()
                if mouseButton == QtCore.Qt.MidButton:
                    return self.middleClicked.emit()
                if mouseButton == QtCore.Qt.RightButton:
                    return self.rightClicked.emit()
        super(ExtendedButtonSimpleMenu, self).mousePressEvent(event)

    def setMenu(self, menu, modeList=None, mouseButton=QtCore.Qt.RightButton):
        """Add the left/middle/right click menu by passing in a QMenu and assign it to the appropriate mouse click key

        Note**: this method is in the elements.MenuCreateClickMethods class, for buttons we need to override here too

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


class ShadowedButton(ExtendedButton, dpiscaling.DPIScaling):
    _menuIndicatorIcon = "menuIndicator"

    def __init__(self, parent=None, text="", shadowHeight=4, forceUpper=False, toolTip=""):
        """ IconPushButton

        A custom button that has a colored frame for the icon and a drop shadow for the overall button

        DPI scale is all handled by this class

        :param parent: Widget Parent
        :type parent: QtWidgets.QWidget
        :param text: Button text
        :type text: basestring
        :param shadowHeight: Height of shadow
        :type shadowHeight: int
        :param forceUpper: Force upper case
        :type forceUpper:
        """
        self.forceUpper = forceUpper
        super(ShadowedButton, self).__init__(parent=parent)
        self.setToolTip(toolTip)
        self.imageWgt = ShadowedButtonImage(parent=self)
        self.textLabel = QtWidgets.QLabel(parent=self)
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.shadow = ShadowedButtonShadow(parent=self)
        self.iconSize = utils.sizeByDpi(QtCore.QSize(16, 16))
        self.setShadowHeight(shadowHeight)
        self.setText(text)
        self.mouseEntered = True
        self.iconPixmap = None  # type: QtGui.QPixmap
        self.iconHoveredPixmap = None  # type: QtGui.QPixmap
        self.iconPressedPixmap = None  # type: QtGui.QPixmap
        self.isMenu = True

        self.initUi()

    def initUi(self):
        """ Initialize Ui

        :return:
        """
        self.setLayout(self.mainLayout)

        self.imageWgt.setFixedWidth(self.sizeHint().height())
        self.imageWgt.setAlignment(QtCore.Qt.AlignCenter)

        self.mainLayout.addWidget(self.imageWgt, 0, 0, 1, 1)
        self.mainLayout.addWidget(self.textLabel, 0, 1, 1, 1)
        self.mainLayout.addWidget(self.shadow, 1, 0, 1, 2)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.textLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.mainLayout.setSpacing(0)

    def setFixedHeight(self, height):
        """ Set Fixed Height

        :param height: Height in pixels of the button
        :type height: int
        :return:
        """
        self.updateImageWidget(height)
        super(ShadowedButton, self).setFixedHeight(utils.dpiScale(height))

    def setFixedSize(self, size):
        """ Set the fixed size

        :param size: New fixed size of the widget
        :type size: QtCore.QSize

        :return:
        """
        self.updateImageWidget(size.height())
        super(ShadowedButton, self).setFixedSize(utils.sizeByDpi(size))

    def updateImageWidget(self, newHeight):
        """ Make sure the image widget is always square

        :param newHeight: The new height of the widget to update to
        :type newHeight: int
        :return:
        """

        self.imageWgt.setFixedSize(utils.sizeByDpi(QtCore.QSize(newHeight, newHeight)))

    def setText(self, text):
        """ Set the text

        :param text: Text to set the button to
        :type text: basestring
        :return:
        """
        if not hasattr(self, "textLabel"):
            # Hasn't been initialized! return
            return

        if self.forceUpper and text is not None:
            text = text.upper()
        self.textLabel.setText(text)

    def setForceUpper(self, force):
        """ Force upper case

        :param force: Force upper case
        :type force: bool
        :return:
        """
        self.forceUpper = force

    def setShadowHeight(self, height):
        """ Set the shadow height in pixels

        :param height: Height in pixels
        :type height: int
        :return:
        """
        self.shadow.setFixedHeight(utils.dpiScale(height))

    def mouseDoubleClickEvent(self, event):
        event.ignore()
        return super(ShadowedButton, self).mouseDoubleClickEvent(event)

    def setIconSize(self, size):
        """ Set the icon size

        :param size:
        :return:
        """
        self.iconSize = utils.sizeByDpi(size)
        self.imageWgt.setFixedSize(self.iconSize)

    def setIconByName(self, iconNames, colors, size=None, hoverColor=None, pressedColor=None, iconScaling=None):
        """ Set Icon Size by name

        todo: needs additional features similar to the ButtonIcons.setIconByName() method

        :param size: Size of the icon in pixels
        :type size: int
        :param iconNames: Names of the icons
        :type iconNames: list or basestring
        :param colors: Colors of the icons
        :type colors: list of tuple
        :return:
        """
        if size is not None:
            self.setIconSize(QtCore.QSize(size, size))

        hoverColor = hoverColor or colors
        pressedColor = pressedColor or colors

        colors = [colors]
        hoverColor = [hoverColor]
        pressedColor = [pressedColor]

        if self.isMenu and isinstance(iconNames, string_types):
            iconNames = [iconNames, self._menuIndicatorIcon]
            colors += colors
            hoverColor += hoverColor
            pressedColor += pressedColor

        newSize = self.iconSize.width()
        self.iconPixmap = iconlib.iconColorizedLayered(iconNames, colors=colors, size=newSize, iconScaling=iconScaling). \
            pixmap(QtCore.QSize(newSize, newSize))

        self.iconHoveredPixmap = iconlib.iconColorizedLayered(iconNames, colors=hoverColor, size=newSize,
                                                              iconScaling=iconScaling). \
            pixmap(QtCore.QSize(newSize, newSize))

        self.iconPressedPixmap = iconlib.iconColorizedLayered(iconNames, colors=pressedColor, size=newSize,
                                                              iconScaling=iconScaling). \
            pixmap(QtCore.QSize(newSize, newSize))

        self.imageWgt.setPixmap(self.iconPixmap)

    def enterEvent(self, event):
        self.mouseEntered = True
        utils.setStylesheetObjectName(self.shadow, "buttonShadowHover")
        utils.setStylesheetObjectName(self.imageWgt, "shadowedImageHover")
        utils.setStylesheetObjectName(self.textLabel, "shadowedLabelHover")
        self.imageWgt.setPixmap(self.iconHoveredPixmap)

    def leaveEvent(self, event):
        self.mouseEntered = False
        utils.setStylesheetObjectName(self.shadow, "")
        utils.setStylesheetObjectName(self.imageWgt, "")
        utils.setStylesheetObjectName(self.textLabel, "")
        self.imageWgt.setPixmap(self.iconPixmap)

    def mousePressEvent(self, event):
        utils.setStylesheetObjectName(self.shadow, "buttonShadowPressed")
        utils.setStylesheetObjectName(self.imageWgt, "shadowedImagePressed")
        utils.setStylesheetObjectName(self.textLabel, "shadowedLabelPressed")
        self.imageWgt.setPixmap(self.iconPressedPixmap)
        return super(ShadowedButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # If mouse still entered while mouse released then set it back to hovered style
        if self.mouseEntered:
            self.enterEvent(event)

        return super(ShadowedButton, self).mouseReleaseEvent(event)


class ShadowedButtonImage(QtWidgets.QLabel):
    """ CSS Purposes """


class ShadowedButtonShadow(QtWidgets.QFrame):
    """ CSS Purposes """
