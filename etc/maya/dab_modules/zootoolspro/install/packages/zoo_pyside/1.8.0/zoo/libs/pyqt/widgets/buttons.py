from Qt import QtWidgets, QtCore
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import roundbutton, label, layouts
from zoo.libs.pyqt.widgets.extendedbutton import ExtendedPushButton, ExtendedButton, ShadowedButton
from zoo.libs import iconlib
from zoo.preferences.core import preference

THEMEPREF = preference.interface("core_interface")


class OkCancelButtons(QtWidgets.QWidget):
    OkBtnPressed = QtCore.Signal()
    CancelBtnPressed = QtCore.Signal()

    def __init__(self, okText="OK", cancelTxt="Cancel", parent=None):
        """Creates OK Cancel Buttons bottom of window, can change the names

        :param okText: the text on the ok (first) button
        :type okText: str
        :param cancelTxt: the text on the cancel (second) button
        :type cancelTxt: str
        :param parent: the widget parent
        :type parent: class
        """
        super(OkCancelButtons, self).__init__(parent=parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.okBtn = QtWidgets.QPushButton(okText, parent=self)
        self.cancelBtn = QtWidgets.QPushButton(cancelTxt, parent=self)
        self.layout.addWidget(self.okBtn)
        self.layout.addWidget(self.cancelBtn)
        self.connections()

    def connections(self):
        self.okBtn.clicked.connect(self.OkBtnPressed.emit)
        self.cancelBtn.clicked.connect(self.CancelBtnPressed.emit)


def buttonRound(**kwargs):
    """Create a rounded button usually just an icon only button with icon in a round circle

    This function is usually called via buttonStyled()
    Uses stylesheet colors, and icon color via the stylesheet from buttonStyled()

    :Note: WIP, Will fill out more options with time

    :param kwargs: See the doc string from the function buttonStyle
    :type kwargs: dict
    :return qtBtn: returns a qt button widget
    :rtype qtBtn: object
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    toolTip = kwargs.get("toolTip", "")
    icon = kwargs.get("icon", (255, 255, 255))  # returns the name of the icon as a string only
    iconSize = kwargs.get("iconSize")
    iconColor = kwargs.get("iconColor")
    iconHoverColor = kwargs.get("iconHoverColor")  # TODO: add this functionality later
    btnWidth = kwargs.get("btnWidth", 24)
    btnHeight = kwargs.get("btnHeight", 24)

    iconObject = iconlib.iconColorized(icon, size=iconSize, color=iconColor)

    btn = roundbutton.RoundButton(parent=parent, text=text, icon=iconObject, toolTip=toolTip)
    btn.setFixedSize(QtCore.QSize(btnWidth, btnHeight))
    return btn


def styledButton(text=None, icon=None, parent=None, toolTip="", textCaps=False, iconColor=None, iconHoverColor=None,
                 minWidth=None, maxWidth=None, iconSize=16, overlayIconName=None, overlayIconColor=None, minHeight=None,
                 maxHeight=None, style=uic.BTN_DEFAULT, btnWidth=None, btnHeight=None):
    """ Create a button with text or an icon in various styles and options.

    Style - 0 - uic.BTN_DEFAULT - Default zoo extended button with optional text or an icon.
    Style - 1 - uic.BTN_TRANSPARENT_BG - Default zoo extended button w transparent bg.
    Style - 2 - uic.BTN_ICON_SHADOW - Main zoo IconPushButton button (icon in a colored box) with shadow underline
    Style - 3 - uic.BTN_DEFAULT_QT - Default style uses vanilla QPushButton and not zoo's extended button
    Style - 4 - uic.BTN_ROUNDED - # Rounded button stylesheeted bg color and stylesheeted icon color
    Style - 5 - uic.BTN_LABEL_SML - A regular Qt label with a small button beside

    :param text: The button text
    :type icon: str
    :param icon: The icon image name, icon is automatically sized.
    :type icon: str
    :param parent: The parent widget.
    :type parent: object
    :param toolTip: The tooltip as seen with mouse over extra information.
    :type toolTip: str
    :param style: The style of the button, 0 default, 1 no bg. See pyside.uiconstants BTN_DEFAULT, BTN_TRANSPARENT_BG.
    :type style: int
    :param textCaps: Bool to make the button text all caps.
    :type textCaps: bool
    :param iconColor: The color of the icon in 255 color eg (255, 134, 23)
    :type iconColor: tuple
    :param minWidth: minimum width of the button in pixels, DPI handled.
    :type minWidth: int
    :param maxWidth: maximum width of the button in pixels, DPI handled.
    :type maxWidth: int
    :param iconSize: The size of the icon in pixels, always square, DPI handled.
    :type iconSize: int
    :param overlayIconName: The name of the icon image that will be overlayed on top of the original icon.
    :param overlayIconName: tuple
    :param overlayIconColor: The color of the overlay image icon (255, 134, 23) :note: Not implemented yet.
    :type overlayIconColor: tuple
    :param minHeight: minimum height of the button in pixels, DPI handled.  Overrides min and max settings
    :type minHeight: int
    :param maxHeight: maximum height of the button in pixels, DPI handled.
    :type maxHeight: int
    :param btnWidth: the fixed width of the button is there is one, DPI handled.  Overrides min and max settings
    :type btnWidth: int
    :param btnHeight: the fixed height of the button is there is one, DPI handled.
    :type btnHeight: int
    :return qtBtn: returns a qt button widget.
    :rtype qtBtn: object
    """
    if btnWidth:
        minWidth = btnWidth
        maxWidth = btnWidth
    if btnHeight:
        minHeight = btnHeight
        maxHeight = btnHeight
    if not iconColor:
        iconColor = THEMEPREF.BUTTON_ICON_COLOR
    if not iconHoverColor:
        # todo: this is done automatically in extendedbuttons, this shouldn't be done here
        hoverOffset = 25
        iconHoverColor = iconColor
        iconHoverColor = tuple([min(255, c+hoverOffset) for c in iconHoverColor])
    if style == uic.BTN_DEFAULT or style == uic.BTN_TRANSPARENT_BG:
        return buttonExtended(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                              iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth,
                              maxWidth=maxWidth, iconSize=iconSize, overlayIconName=overlayIconName,
                              overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight,
                              style=style)
    elif style == uic.BTN_ICON_SHADOW:
        return iconShadowButton(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                                iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth,
                                maxWidth=maxWidth, iconSize=iconSize, overlayIconName=overlayIconName,
                                overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight)
    elif style == uic.BTN_DEFAULT_QT:
        return regularButton(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                             iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth, maxWidth=maxWidth,
                             iconSize=iconSize, overlayIconName=overlayIconName, overlayIconColor=overlayIconColor,
                             minHeight=minHeight, maxHeight=maxHeight)
    elif style == uic.BTN_ROUNDED:
        return buttonRound(text=text, icon=icon, parent=parent, toolTip=toolTip, iconColor=iconColor,
                           iconHoverColor=iconHoverColor, iconSize=iconSize, overlayIconName=overlayIconName,
                           overlayIconColor=overlayIconColor, btnWidth=btnWidth, btnHeight=btnHeight)
    elif style == uic.BTN_LABEL_SML:
        return LabelSmlButton(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                              iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=uic.BTN_W_ICN_MED,
                              maxWidth=uic.BTN_W_ICN_MED, iconSize=iconSize, overlayIconName=overlayIconName,
                              overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight)


def buttonExtended(**kwargs):
    """ Create an extended either transparent bg or regular style. Features all the extended button functionality

    Default Icon colour (None) is light grey and turns white (lighter in color) with mouse over.
    :Note: WIP, Will fill out more options with time

    :param kwargs: See the doc string from the function buttonStyle
    :type kwargs: dict
    :return qtBtn: returns a qt button widget
    :rtype qtBtn: object
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    icon = kwargs.get("icon", THEMEPREF.BUTTON_ICON_COLOR)  # returns the name of the icon as a string only
    toolTip = kwargs.get("toolTip", "")
    iconSize = kwargs.get("iconSize", 16)
    iconColor = kwargs.get("iconColor")
    iconHoverColor = kwargs.get("iconHoverColor")
    overlayIconName = kwargs.get("overlayIconName")
    overlayIconColor = kwargs.get("overlayIconColor")
    minWidth = kwargs.get("minWidth")
    maxWidth = kwargs.get("maxWidth")
    minHeight = kwargs.get("maxHeight")
    maxHeight = kwargs.get("maxHeight")
    style = kwargs.get("style")

    if icon:
        # todo: icon hover already gets done automatically use btn.setIconByName() instead
        iconObject = iconlib.iconColorized(icon,
                                           size=iconSize, color=iconColor,
                                           overlayName=overlayIconName, overlayColor=overlayIconColor)
        iconHoverObject = iconlib.iconColorized(icon,
                                                size=iconSize, color=iconHoverColor,
                                                overlayName=overlayIconName, overlayColor=overlayIconColor)
        if style == uic.BTN_DEFAULT:
            btn = ExtendedPushButton(icon=iconObject, iconHover=iconHoverObject, parent=parent, text=text)
        else:
            btn = ExtendedButton(icon=iconObject, iconHover=iconHoverObject, parent=parent, text=text)
    else:
        if style == uic.BTN_DEFAULT:
            btn = ExtendedPushButton(parent=parent, text=text)  # default style
        else:
            btn = ExtendedButton(parent=parent, text=text)  # transparent style
    btn.setToolTip(toolTip)

    if minWidth is not None:
        btn.setMinimumWidth(utils.dpiScale(minWidth))
    if maxWidth is not None:
        btn.setMaximumWidth(utils.dpiScale(maxWidth))
    if minHeight is not None:
        btn.setMinimumHeight(utils.dpiScale(minHeight))
    if maxHeight is not None:
        btn.setMaximumHeight(utils.dpiScale(maxHeight))
    return btn


def regularButton(**kwargs):
    """ Creates regular pyside button with text or an icon.

    :note: Will fill out more options with time.
    :note: Should probably override ExtendedButton and not QtWidgets.QPushButton for full options.

    :param kwargs: See the doc string from the function buttonStyle
    :type kwargs: dict
    :return qtBtn: returns a qt button widget
    :rtype qtBtn: object
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    icon = kwargs.get("icon", THEMEPREF.BUTTON_ICON_COLOR)
    toolTip = kwargs.get("toolTip", "")
    iconSize = kwargs.get("iconSize")
    iconColor = kwargs.get("iconColor")
    overlayIconName = kwargs.get("overlayIconName")
    overlayIconColor = kwargs.get("overlayIconColor")
    minWidth = kwargs.get("minWidth")
    maxWidth = kwargs.get("maxWidth")
    minHeight = kwargs.get("maxHeight")
    maxHeight = kwargs.get("maxHeight")

    btn = QtWidgets.QPushButton(text, parent=parent)
    if icon:
        btn.setIcon(iconlib.iconColorized(icon, size=utils.dpiScale(iconSize), color=iconColor,
                                          overlayName=overlayIconName, overlayColor=overlayIconColor))

    btn.setToolTip(toolTip)
    if minWidth is not None:
        btn.setMinimumWidth(utils.dpiScale(minWidth))
    if maxWidth is not None:
        btn.setMaximumWidth(utils.dpiScale(maxWidth))
    if minHeight is not None:
        btn.setMinimumHeight(utils.dpiScale(minHeight))
    if maxHeight is not None:
        btn.setMaximumHeight(utils.dpiScale(maxHeight))
    return btn


def iconShadowButton(**kwargs):
    """ Create a button (ShadowedButton) with the icon in a coloured box and a button shadow at the bottom of the button.

    This function is usually called via buttonStyled()
    Uses stylesheet colors, and icon color via the stylesheet from buttonStyled()

    :Note: WIP, Will fill out more options with time

    :param kwargs: See the doc string from the function buttonStyle
    :type kwargs: dict
    :return qtBtn: returns a qt button widget
    :rtype qtBtn: object
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    textCaps = kwargs.get("textCaps")
    icon = kwargs.get("icon", THEMEPREF.BUTTON_ICON_COLOR)  # returns the name of the icon as a string only
    toolTip = kwargs.get("toolTip", "")
    iconSize = kwargs.get("iconSize")
    iconColor = kwargs.get("iconColor")
    iconHoverColor = kwargs.get("iconHoverColor")  # TODO: add this functionality later
    minWidth = kwargs.get("minWidth")
    maxWidth = kwargs.get("maxWidth")
    minHeight = kwargs.get("minHeight")  # TODO: add this functionality later
    maxHeight = kwargs.get("maxHeight")
    btn = ShadowedButton(text=text, parent=parent, forceUpper=textCaps, toolTip=toolTip)
    btn.setIconByName(icon, colors=iconColor, size=iconSize)
    if maxHeight:
        btn.setFixedHeight(maxHeight)
    if maxWidth:
        btn.setMaximumWidth(maxWidth)
    if minWidth:
        btn.setMinimumWidth(minWidth)
    return btn


class LabelSmlButton(QtWidgets.QWidget):
    clicked = QtCore.Signal()

    def __init__(self, text="", icon=None, parent=None, toolTip="", textCaps=False, iconColor=None, iconHoverColor=None,
                 minWidth=None, maxWidth=None, iconSize=16, overlayIconName=None, overlayIconColor=None, minHeight=None,
                 maxHeight=None, style=uic.BTN_DEFAULT, btnWidth=None, btnHeight=None):
        """Creates a Qt label and a small button with icon, can be called as though it's a button with StyledButton()

        See StyledButton() for kwarg documentation
        """
        super(LabelSmlButton, self).__init__(parent=parent)
        self.text = text
        if text:
            self.label = label.Label(text, self, toolTip=toolTip, upper=textCaps)
        self.btn = buttonExtended(text="", icon=icon, parent=self, toolTip=toolTip, textCaps=textCaps,
                                  iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth,
                                  maxWidth=maxWidth, iconSize=iconSize, overlayIconName=overlayIconName,
                                  overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight,
                                  style=style)
        btnLayout = layouts.hBoxLayout(parent=self)
        if text:
            btnLayout.addWidget(self.label, 5)
        btnLayout.addWidget(self.btn, 1)
        self.connections()

    def _onClicked(self):
        """If the button is clicked emit"""
        self.clicked.emit()

    def setDisabled(self, state):
        """Disable the text (make it grey)"""
        self.btn.setDisabled(state)
        if self.text:
            self.label.setDisabled(state)

    def connections(self):
        self.btn.clicked.connect(self._onClicked)