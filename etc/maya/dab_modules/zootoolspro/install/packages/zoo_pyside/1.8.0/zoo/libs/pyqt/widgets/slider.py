from Qt import QtCore, QtWidgets
from zoo.libs.pyqt import uiconstants, utils
from zoo.libs.pyqt.widgets import stringedit
from zoo.libs.pyqt.widgets.layouts import hBoxLayout


class Slider(QtWidgets.QSlider):
    def __init__(self, defaultValue=0.0, parent=None, toolTip="", sliderAccuracy=200, floatMin=0.0, floatMax=1.0,
                 decimalPlaces=None, orientation=QtCore.Qt.Horizontal):
        """A slider only with kwargs for setting float style sliders

        :param defaultValue: The default value of the slider, as a float between range of floatMin and floatMax
        :type defaultValue: float
        :param parent: The parent Qt Widget
        :type parent: object
        :param toolTip: The tooltip of the slider
        :type toolTip: str
        :param sliderAccuracy: The accuracy of the slider, is an int with the steps of the slider
        :type sliderAccuracy: int
        :param floatMin: The minimum value of the slider as a float, this is overridden and is not an int as per qt
        :type floatMin: float
        :param floatMax: The maximum value of the slider as a float, this is overridden and is not an int as per qt
        :type floatMax: float
        :param decimalPlaces: The number of decimal places to limit the value return, if None no decimal place limit
        :type decimalPlaces: int
        :param orientation: The orientation of the slider QtCore.Qt.Horizontal or QtCore.Qt.Vertical
        :type orientation:
        """
        self.floatMin = floatMin  # maybe should use self.minimum()
        self.floatMax = floatMax  # maybe should use self.maximum()

        self.decimalPlaces = decimalPlaces
        self.sliderAccuracy = sliderAccuracy
        super(Slider, self).__init__(orientation=orientation, parent=parent)
        super(Slider, self).setRange(0, sliderAccuracy)
        self.setToolTip(toolTip)
        self.setValue(defaultValue)
        self.styleLeaveCheck()
        self.valueChanged.connect(self.styleLeaveCheck)

    def enterEvent(self, event):
        self.sliderActive()

    def styleLeaveCheck(self):
        """ Hide the sub-page when value is 0 since it doesn't get hidden
        """
        if self.value() == self.floatMin:
            utils.setStylesheetObjectName(self, "SliderMin")
        else:
            utils.setStylesheetObjectName(self, "")

    def sliderActive(self):
        if self.isEnabled():
            utils.setStylesheetObjectName(self, "SliderActive")

    def leaveEvent(self, event):
        self.styleLeaveCheck()

    def _convertValueToFloat(self, intValue):
        """Converts a value from Qts slider which is int 0 - self.sliderAccuracy range to float the user expects

        :param intValue: The qt slider int value which will be in the 0 - self.sliderAccuracy range
        :type intValue: int
        :return floatValue: The float of the value now in self.floatMin - self.floatMax range
        :rtype floatValue: float
        """
        floatRange = self.floatMax - self.floatMin
        steps = floatRange / float(self.sliderAccuracy)  # say defaults 1.0/200.0 = 0.005
        return (float(intValue) * steps) + self.floatMin

    def _convertValueToInt(self, floatValue):
        """Converts a slider from a float value that the user passes in, to a Qt int value from 0 - self.sliderAccuracy

        :param floatValue: The value the user will user, in range of self.floatMin - self.floatMax
        :type floatValue: float
        :return intValue: The qt slider int value which will be in the 0 - self.sliderAccuracy range
        :rtype intValue: int
        """
        floatRange = self.floatMax - self.floatMin
        multiplier = (floatValue - self.floatMin) / floatRange
        intValue = multiplier * self.sliderAccuracy
        return int(round(intValue))

    def value(self):
        """Sliders are in ints so do the math to figure the correct user value and return the expected float

        Internally the slider is an int in the range of 0 - self.sliderAccuracy (int)
        Convert this to a float value within the correct self.floatMax - self.floatMin

        Overridden method

        :return floatValue: The value of the slider as a float the user expects, not slider raw value which is an int
        :rtype floatValue: float
        """
        intValue = super(Slider, self).value()
        floatValue = self._convertValueToFloat(intValue)
        if self.decimalPlaces is not None:
            return round(floatValue, self.decimalPlaces)  # round to decimal places
        else:
            return floatValue

    def setValue(self, floatValue):
        """Sets the value of a slider as a float in a user friendly value. Value range self.floatMax - self.floatMin

        Overridden method

        :param floatValue: The value the user will user, in range of self.floatMin - self.floatMax
        :type floatValue: float
        """
        intValue = self._convertValueToInt(float(floatValue))
        super(Slider, self).setValue(intValue)
        self.styleLeaveCheck()

    def _intValue(self):
        """The qt slider value which is an int and somewhere between 0 and self.sliderAccuracy

        :return intValue: The raw int value of the qt slide which is an int and between 0 and self.sliderAccuracy
        :rtype intValue: int
        """
        return super(Slider, self).value()

    def setSliderPosition(self, floatValue):
        """Pass in a float value within the range self.floatMax - self.floatMin

        Convert it to the int which the Qt slider expects within 0 - self.sliderAccuracy (int)

        Overridden method
        """
        intValue = self._convertValueToInt(floatValue)
        super(Slider, self).setSliderPosition(intValue)

    def setMinimum(self, floatMin):
        """Sets the minimum value of the slider as a float that the user expects
        Overridden method

        :param floatMin: The minimum value of the slider as the user expects in float range
        :type floatMin: float
        """
        self.setRange(self, floatMin, self.floatMax)

    def setMaximum(self, floatMax):
        """Sets the maximum value of the slider as a float that the user expects
        Overridden method

        :param floatMax: The maximum value of the slider as the user expects in float range
        :type floatMax: float
        """
        self.setRange(self, self.floatMin, floatMax)

    def setRange(self, floatMin, floatMax):
        """Sets the minimum and maximum range of the slider with float values that the user expects
        Qt sliders use integers and so this needs to be converted.

        Overridden method

        :param floatMin: The minimum value of the slider as the user expects in float range
        :type floatMin: float
        :param floatMax: The maximum value of the slider as the user expects in float range
        :type floatMax: float
        """
        intValue = self._intValue()  # the raw qt slider value as an int
        self.floatMin = floatMin
        self.floatMax = floatMax
        # set slider in new position
        floatValue = self._convertValueToFloat(intValue)
        self.blockSignals(True)
        self.setSliderPosition(floatValue)
        self.blockSignals(False)


class HSlider(Slider):
    def __init__(self, defaultValue=0.0, parent=None, toolTip="", sliderAccuracy=200, floatMin=0.0, floatMax=1.0,
                 decimalPlaces=None):
        """ Horizontal Slider

        See Slider() for documentation
        """
        super(HSlider, self).__init__(defaultValue=defaultValue, parent=parent, toolTip=toolTip,
                                      sliderAccuracy=sliderAccuracy, floatMin=floatMin, floatMax=floatMax,
                                      decimalPlaces=decimalPlaces, orientation=QtCore.Qt.Horizontal)


class VSlider(Slider):
    def __init__(self, defaultValue=0.0, parent=None, toolTip="", sliderAccuracy=200, floatMin=0.0, floatMax=1.0,
                 decimalPlaces=None):
        """ Vertical Slider

        See Slider() for documentation
        """
        super(VSlider, self).__init__(defaultValue=defaultValue, parent=parent, toolTip=toolTip,
                                      sliderAccuracy=sliderAccuracy, floatMin=floatMin, floatMax=floatMax,
                                      decimalPlaces=decimalPlaces, orientation=QtCore.Qt.Vertical)


class FloatSlider(QtWidgets.QWidget):
    # ------------- Slider Signals Notes -----------
    # - Use floatSliderMajorChange Only if you want changes on release of the slider, not while sliding
    # - Use floatSliderChanged not for most ui connections full interactive, it always updates, do not use
    # - For undo queues use sliderPressed sliderReleased and toggle the undo tracking, see Shader Manager GUI
    textChanged = QtCore.Signal(str)  # when the text is typed on each keystroke
    sliderChanged = QtCore.Signal()  # the slider only is changed, not the text
    textModified = QtCore.Signal(str)  # Maya style text changes, handles if text returned, or on change focus
    sliderPressed = QtCore.Signal()  # self.sliderPressed.connect(openUndoChunk) use to open the undo chunk
    sliderReleased = QtCore.Signal()  # self.sliderPressed.connect(closeUndoChunk) use to close the undo chunk
    floatSliderChanged = QtCore.Signal()  # Any change to slider/textbox, sliderChanged or textModified, not textChanged
    floatSliderMajorChange = QtCore.Signal()  # A major change, so textModified or sliderReleased

    def __init__(self, label="", defaultValue=0.0, parent=None, toolTip="", sliderMin=0.0,
                 sliderMax=1.0, sliderAccuracy=200, editWidth=None, enableMenu=False, editBox=True, labelRatio=1,
                 editBoxRatio=1, sliderRatio=1, labelBtnRatio=1, decimalPlaces=2, orientation=QtCore.Qt.Horizontal):
        """A label, lineEdit (float) and a slider all in one widget.

        Label is bypassed if there is no label
        lineEdit is bypassed if editBox=False

        :param label: The name of the label, if empty "" will not build a label
        :type label: str
        :param defaultValue: The default value of the lineEdit and slider
        :type defaultValue: float
        :param parent:  The parent Widget
        :type parent: object
        :param toolTip: The tooltip on all widgets
        :type toolTip: str
        :param sliderMin: The minimum value of the slider
        :type sliderMin: float
        :param sliderMax: The maximum value of the slider
        :type sliderMax: float
        :param sliderAccuracy: The accuracy of the slider, is an int with the steps of the slider
        :type sliderAccuracy: int
        :param editWidth:  The width in pixels of the lineEdit, None is auto
        :type editWidth: int
        :param enableMenu: Enable the right click menu on the label and lineEdit?  See StringEdit() documentation
        :type enableMenu: bool
        :param editBox: Build the lineEdit?  If false no lineEdit will be built
        :type editBox: bool
        :param labelRatio: The ratio size for laying out the label compared to other widgets, default is 1 which is 1/4
        :type labelRatio: int
        :param editBoxRatio: The ratio size for laying out the lineEdit default is 1 which is 1/4
        :type editBoxRatio: int
        :param sliderRatio: The ratio size for laying out the slider default is 1 which is 1/2
        :type sliderRatio: int
        :param labelBtnRatio: The ratio size for the label and color btn layout, default is 1 which is 1/2
        :type labelBtnRatio: int
        :param decimalPlaces: Limit the slider feedback and value return to this many decimal places, None is unlimited
        :type decimalPlaces: int
        :param orientation: The orientation of the slider QtCore.Qt.Horizontal or QtCore.Qt.Vertical
        :type orientation:
        """
        super(FloatSlider, self).__init__(parent=parent)
        utils.setSkipChildren(self, True)
        self.editBox = editBox
        self.sliderMax = sliderMax
        self.sliderMin = sliderMin
        self.layout = hBoxLayout(self, (0, 0, 0, 0), spacing=uiconstants.SREG)
        self.labelBool = False
        if label or editBox:
            labelBtnLayout = hBoxLayout(self, (0, 0, 0, 0), spacing=uiconstants.SREG)
        # Build Label -------------------
        if label:
            self.labelBool = True
            self.label = stringedit.Label(label, parent=parent, toolTip=toolTip)
            labelBtnLayout.addWidget(self.label, labelRatio)
        # Build Edit Box -------------------
        if editBox:
            defaultString = str(defaultValue)
            self.edit = stringedit.FloatLineEdit(defaultString, parent=parent, toolTip=toolTip, editWidth=editWidth,
                                             enableMenu=enableMenu)
            labelBtnLayout.addWidget(self.edit, editBoxRatio)
        if label or editBox:
            self.layout.addLayout(labelBtnLayout, labelBtnRatio)
        # Build Slider -------------------
        self.slider = Slider(defaultValue=defaultValue, parent=parent, toolTip=toolTip, floatMin=sliderMin,
                             floatMax=sliderMax, sliderAccuracy=sliderAccuracy, decimalPlaces=decimalPlaces,
                             orientation=orientation)
        self.layout.addWidget(self.slider, sliderRatio)
        # Connections
        self.uiConnections()

    def _textUpdated(self):
        """Emit signal and update the slider:

            textUpdated = QtCore.Signal(str)
        """
        value = float(self.edit.text())
        # Check min/max
        if value > self.sliderMax:
            value = self.sliderMax
            self._setEditQuiet(value)
        elif value < self.sliderMin:
            value = self.sliderMin
            self._setEditQuiet(value)
        # Signals
        self.textModified.emit(value)
        self._setSliderQuiet(value)  # set the slider with no emits
        self.floatSliderChanged.emit()
        self.floatSliderMajorChange.emit()

    def _textChanged(self):
        """Emit signal:

            textChanged = QtCore.Signal(str)
        """
        self.textChanged.emit(self.value())

    def _sliderUpdated(self):
        value = self.slider.value()  # is a float because zoo Slider
        self._setEditQuiet(value)  # set textbox quietly no signals
        self.sliderChanged.emit()
        self.floatSliderChanged.emit()

    def _sliderPressed(self):
        self.sliderPressed.emit()

    def _sliderReleased(self):
        self.sliderChanged.emit()
        self.sliderReleased.emit()
        self.floatSliderChanged.emit()
        self.floatSliderMajorChange.emit()

    def _setEditQuiet(self, value):
        """Set the text box only quietly with no signal emits.

        :param value: value to change the textbox
        :type value: float
        """
        self.edit.blockSignals(True)
        self.edit.setValue(value)
        self.edit.blockSignals(False)

    def _setSliderQuiet(self, value):
        """Sets the slider only quietly with no signal emits.

        :param value: value to change the textbox
        :type value: float
        """
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)

    def blockSignals(self, state):
        """Blocks the widget

        :param state: True will block signals to the widget
        :type state: bool
        """
        if self.editBox:
            self.edit.blockSignals(state)
        self.slider.blockSignals(state)

    def setDisabled(self, state):
        """Disables or enables the widget/s

        :param state: If True will disable, if False will enable
        :type state: bool
        """
        if self.editBox:
            self.edit.blockSignals(state)
        self.slider.blockSignals(state)

    def value(self):
        """Gets the current value of the slider as a float"""
        return self.slider.value()

    def setValue(self, value):
        """Sets the current slider and text box value with a float, quiet no emits

        :param value: The value to set the slider and lineEdit to
        :type value: float
        """
        if self.editBox:
            self._setEditQuiet(value)
        self._setSliderQuiet(value)

    def text(self):
        """Gets the current value of the slider as a float"""
        return self.slider.value()

    def setText(self, text):
        """Gets the current value of the slider as a float"""
        if type(text) == "string" or type(text) == "int":
            text = float(text)
        self.setValue(text)

    def setLabel(self, labelName):
        """Changes the label text"""
        if self.labelBool:
            self.label.setLabel(labelName)

    def label(self):
        """Gets the label text (name)

        :return labelText: The name of the label
        :rtype labelText: str
        """
        if self.labelBool:
            return self.label.text()

    def uiConnections(self):
        if self.editBox:
            self.edit.textModified.connect(self._textUpdated)
            self.edit.textChanged.connect(self._textChanged)
        self.slider.valueChanged.connect(self._sliderUpdated)
        self.slider.sliderPressed.connect(self._sliderPressed)
        self.slider.sliderReleased.connect(self._sliderReleased)
