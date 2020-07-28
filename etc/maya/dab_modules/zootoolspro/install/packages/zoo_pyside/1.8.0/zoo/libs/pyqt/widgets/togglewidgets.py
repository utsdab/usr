from Qt import QtWidgets, QtCore

from zoo.libs.pyqt.widgets import extendedbutton
from zoo.libs.utils import colour

""" Image versions of radio buttons and checkbox so we can customize colour and icon
"""

class CheckableIcons(extendedbutton.ButtonIcons):
    """RadioButton and CheckBox inherits from this this class to set up the icons that
    change on mouse over, press and release. Also the icons change when the button is checked or unchecked.

    .. code-block:: python

        class ImageRadioButton(QtWidgets.QRadioButton, Checkable):
            def __init__():
                self.initCheckables(uncheckedIconName="circle",
                        checkedIconName="circleFilled",
                        pressedIconName="circleFilled")

    Must use initCheckables() when inherited in a subclass

    """
    def __init__(self):
        super(CheckableIcons, self).__init__()

    def toggleClicked(self):

        if self.isChecked():
            self.setIconByName(self._iconChecked, colorOffset=40)
        else:
            self.setIconByName(self._iconUnchecked, colorOffset=40)

    def initCheckables(self, uncheckedIconName, checkedIconName, pressedIconName):

        className = self.__class__.__name__

        style = """
        {0}::indicator {{background-color:transparent; width:0}}
        """.format(className)
        self.setStyleSheet(style)

        self._iconUnchecked = uncheckedIconName
        self._iconChecked = checkedIconName
        self._iconPressed = pressedIconName

        self.toggled.connect(self.toggleClicked)
        self.pressed.connect(self.buttonPressed)
        self.released.connect(self.buttonReleased)

        self.toggleClicked()

    def buttonPressed(self):
        pressedCol = colour.offsetColor(self.iconColors, -30)
        self.originalColor = self.iconColors
        self.setIconByName(self._iconPressed, colors=pressedCol)

    def buttonReleased(self):
        self.setIconColor(self.originalColor, update=True)

    def paintEvent(self, e):
        super(CheckableIcons, self).paintEvent(e)


class RadioButton(QtWidgets.QRadioButton, CheckableIcons):

    def __init__(self, text,
                 checkedIcon="circleFilled",
                 uncheckedIcon="circle",
                 pressedIcon="circleFilled",
                 color=(128, 128, 128),
                 toolTip="",
                 highlight=40, parent=None):
        super(RadioButton, self).__init__(parent=parent, text=text)

        self.highlightOffset = highlight
        self.setIconColor(color)
        self.setToolTip(toolTip)

        # Initialise the icons
        self.initCheckables(uncheckedIconName=uncheckedIcon,
                            checkedIconName=checkedIcon,
                            pressedIconName=pressedIcon)
        self.setIconSize(QtCore.QSize(14, 14))


class CheckBox(QtWidgets.QCheckBox, CheckableIcons):
    def __init__(self, text,
                 checkedIcon="roundedSquareFilledBox",
                 uncheckedIcon="roundedsquare",
                 pressedIcon="roundedSquareFilledBox",
                 color=(128, 128, 128),
                 checked=False,
                 toolTip="",
                 highlight=40, parent=None):
        super(CheckBox, self).__init__(parent=parent, text=text)

        self.highlightOffset = highlight
        self.setIconColor(color)
        self.setChecked(checked)
        self.setToolTip(toolTip)

        # Initialise the icons
        self.initCheckables(uncheckedIconName=uncheckedIcon,
                            checkedIconName=checkedIcon,
                            pressedIconName=pressedIcon)
        self.setIconSize(QtCore.QSize(14, 14))






