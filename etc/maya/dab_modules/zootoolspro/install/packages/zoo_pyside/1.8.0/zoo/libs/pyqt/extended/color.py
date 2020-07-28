from functools import partial

import math

from Qt import QtGui, QtWidgets, QtCore
from zoo.libs.pyqt import uiconstants, utils
from zoo.libs.pyqt.widgets import layouts
from zoo.libs.utils import colour

class ColorButtonPressedEvent(object):
    color = (-1,-1,-1)
    index = -1
    srgb = (-1,-1,-1)

    def __init__(self, index, color, srgb):
        """ Color button pressed event for ColorPaletteColorList

        :param index:
        :type index:
        :param color:
        :type color:
        :param srgb:
        :type srgb:
        """
        self.color = color
        self.index = index
        self.srgb = srgb

    def __str__(self):
        return str(self.__dict__)


class ColorPaletteColorList(QtWidgets.QWidget):
    colorPressed = QtCore.Signal(ColorButtonPressedEvent)

    def __init__(self, colorList, parent=None, rows=2, totalHeight=70, borderRadius=0, spacing=0, toolTip=""):
        """Draws a color palette from a color list.  The list is in SRGB not linear color.
        The columns are automatically set from the row count and list length.

        .. code-block:: python

            # build widget
            self.colorPaletteHOffset = elements.ColorPaletteColorList(parent=parent)

            # setup connections
            for i, btn in enumerate(self.colorPaletteHOffset.colorBtnList):
                color = self.colorPaletteHOffset.colorListLinear[i]
                btn.clicked.connect(partial(self.colorSelected, color=color))

        See it's use in the Color Controls Toolset where palettes can be passed in and updated

        :param colorList: list of colors as SRGB float (0.5, 0.5, 0.5) is 50% grey
        :type colorList: list(tuple(float))
        :param parent: the widget parent
        :type parent: QtWidget
        :param rows: The amount of rows to draw
        :type rows: int
        :param totalHeight: The total height of the palette, button height is auto calculated from this number
        :type totalHeight: int
        """
        # TODO allow the row column counts to change so single palettes can be swithed.
        super(ColorPaletteColorList, self).__init__(parent=parent)
        self.colorListSrgb = colorList
        self.colorListLinear = list()  # Will be in Maya linear color, can be accessed through the GUI
        self.colorBtnList = list()  # buttons to connect in the GUI
        self.setToolTip(toolTip)
        gridLayout = layouts.GridLayout(parent=self, spacing=utils.dpiScale(spacing))
        btnHeight = utils.dpiScale(int(totalHeight / rows))
        columns = math.ceil(float(len(colorList)) / rows)  # ( number of colors / rows ), then round up.
        colCount = 0
        rowCount = 0
        for i, color in enumerate(colorList):
            # create button and set color
            btn = QtWidgets.QPushButton("", parent=self)
            btn.setMinimumWidth(utils.dpiScale(5))

            srgbInt = tuple(colour.rgbFloatToInt(color))  # Qt stylesheet needs int 255 color
            self.colorListLinear.append(colour.convertColorSrgbToLinear(color))
            btn.setStyleSheet("background-color: rgb{}; border-radius: {}px;".format(str(srgbInt), utils.dpiScale(borderRadius)))
            btn.setProperty("color", color)
            btn.setProperty("index", i)
            btn.setProperty("srgb", srgbInt)

            self.colorBtnList.append(btn)
            # set btn height
            btn.setMaximumHeight(btnHeight)
            btn.setMinimumHeight(btnHeight)
            # add to grid layout
            if colCount >= columns:  # if columns are full then increment row and reset column
                rowCount += 1
                colCount = 0
            gridLayout.addWidget(btn, rowCount, colCount)
            colCount += 1

            # btn
            btn.clicked.connect(lambda i=i, color=color, srgb=srgbInt: self.colorPressed.emit(ColorButtonPressedEvent(i, color, srgb)))


    def updatePaletteColors(self, newColorList):
        """Updates the palettes colors with the `startHsvColor` and `hueRange`

        :param newColorList: list of colors (in what colour space?)
        :type newColorList: list(tuple(float))
        """
        for i, oldCol in enumerate(self.colorListSrgb):  # loop through the original list in case of length mismatch
            color = newColorList[i]
            if i > len(newColorList):  # bail if new color doesn't exist, list not long enough
                break
            # set btn color
            rgbInt = colour.rgbFloatToInt(color)
            self.colorBtnList[i].setStyleSheet("background-color: rgb{}; "
                                               "border-radius: 0px;".format(str(tuple(rgbInt))))
            # replace color in list
            self.colorListSrgb[i] = color
            self.colorListLinear[i] = colour.convertColorSrgbToLinear(color)

    def rebuildPalette(self, rows=2, columns=10, totalHeight=70, startHsvColor=(0.0, 0.8, 0.8),
                       hueRange=280.0):
        """Currently not working???

        :param rows:
        :type rows:
        :param columns:
        :type columns:
        :param totalHeight:
        :type totalHeight:
        :param startHsvColor:
        :type startHsvColor:
        :param hueRange:
        :type hueRange:
        :return:
        :rtype:
        """
        # TODO this function is not working
        self.clear()  # delete and remake the grid layout
        QtWidgets.QWidget().setLayout(self.gridLayout)
        self.gridLayout = layouts.GridLayout(parent=self, spacing=0)  # rebuild
        self._buildWidget(rows, columns, totalHeight, hueRange, startHsvColor)
        self.mainWidget.setLayout(self.gridLayout)
        self.update()


class LabelColorBtn(QtWidgets.QWidget):
    """Creates a label and a color button (with no text) which opens a QT color picker,
    returns both rgb (0-255) and rgbF (0-1.0) values
    """
    colorChanged = QtCore.Signal(object)

    def __init__(self, label="Color:", initialRgbColor=None, initialRgbColorF=None, contentsMargins=(0, 0, 0, 0),
                 parent=None, labelWeight=1, colorWeight=1, colorWidth=None):
        """Initialize variables

        :param label: The name of the label, usually "Color:"
        :type label: str
        :param initialRgbColor: The initial rgb color in 0-255 ranges, overridden if there's a initialRgbColorF value
        :type initialRgbColor: tuple
        :param initialRgbColorF: The initial rgb color in 0-1.0 ranges, if None defaults to initialRgbColor values
        :type initialRgbColorF: tuple
        :param parent: the widget parent
        :type parent: class
        """
        super(LabelColorBtn, self).__init__(parent=parent)
        self.layout = layouts.hBoxLayout(parent=self, margins=utils.marginsDpiScale(*contentsMargins),
                                 spacing=utils.dpiScale(uiconstants.SPACING))
        self.layout.addWidget(QtWidgets.QLabel(label, parent=self), labelWeight)
        self.colorPickerBtn = QtWidgets.QPushButton("", parent=self)
        # use initialRgbColor (255 range) or initialRgbColorF (float range 0-1)
        # if no color given then default to red
        self.storedRgbColor = initialRgbColor or tuple([i * 255 for i in initialRgbColorF]) or tuple([255, 0, 0])
        self.colorPickerBtn.setStyleSheet("background-color: rgb{}".format(str(self.storedRgbColor)))
        if colorWidth:
            self.colorPickerBtn.setFixedWidth(colorWidth)
        self.layout.addWidget(self.colorPickerBtn, colorWeight)
        self.connections()

    def setColorSrgbInt(self, rgbList):
        """Sets the color of the button as per a rgb list in 0-255 range

        :param rgbList: r g b color in 255 range eg [255, 0, 0]
        :type rgbList: list
        """
        # if the user hits cancel the returned color is invalid, so don't update
        self.storedRgbColor = rgbList
        color = QtGui.QColor(self.storedRgbColor[0], self.storedRgbColor[1], self.storedRgbColor[2], 255)
        self.colorPickerBtn.setStyleSheet("background-color: {}".format(color.name()))

    def setColorSrgbFloat(self, rgbList):
        """Sets the color of the button as per a rgb list in 0-1 range, colors are not rounded

        :param rgbList: r g b color in float range eg [1.0, 0.0, 0.0]
        :type rgbList: list
        """
        self.setColorSrgbInt([color * 255 for color in rgbList])

    def pickColor(self):
        """Opens the color picker window
        If ok is pressed then the new color is returned in 0-255 ranges Eg (128, 255, 12)
        If Cancel is pressed the color is invalid and nothing happens
        """
        initialPickColor = QtGui.QColor(self.storedRgbColor[0], self.storedRgbColor[1], self.storedRgbColor[2], 255)
        color = QtWidgets.QColorDialog.getColor(initialPickColor)  # expects 255 range
        if QtGui.QColor.isValid(color):
            rgbList = (color.getRgb())[0:3]
            self.setColorSrgbInt(rgbList)
            self.colorChanged.emit(color)

    def rgbColor(self):
        """returns rgb tuple with 0-255 ranges Eg (128, 255, 12)
        """
        return self.storedRgbColor

    def rgbColorF(self):
        """returns rgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        """
        return tuple(float(i) / 255 for i in self.storedRgbColor)

    def connections(self):
        """Open the color picker when the button is pressed
        """
        self.colorPickerBtn.clicked.connect(self.pickColor)