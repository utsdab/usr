from collections import OrderedDict

from Qt import QtCore, QtWidgets
from Qt import QtWidgets
from zoo.libs.pyqt import uiconstants, utils
from zoo.libs.pyqt.extended.combobox import ComboBoxSearchable
from zoo.libs.pyqt.widgets.layouts import hBoxLayout

DRAG_NONE = 0
DRAG_HORIZONTAL = 1
DRAG_VERTICAL = 2

CURSOR_NONE = 0
CURSOR_BLANK = 1
CURSOR_ARROWS = 2


class DragSpinBox(QtWidgets.QSpinBox):
    def __init__(self, *args, **kwargs):
        super(DragSpinBox, self).__init__(*args, **kwargs)
        self.defaultValue = 0.0
        self._dragSensitivity = 5  # pixels per step
        self._startSensitivity = 10  # pixel move to start the dragging
        # private vars
        self._lastPos = QtCore.QPoint()
        self._leftover = 0
        self._dragStart = None
        self._firstDrag = False
        self._dragType = DRAG_NONE

    def mousePressEvent(self, event):
        if event.button() & QtCore.Qt.RightButton:
            self.setValue(self.defaultValue)
            return True

    def mouseMoveEvent(self, event):
        stepHolder = self.singleStep()
        if self._dragType:
            if self._dragType == DRAG_HORIZONTAL:
                delta = event.pos().x() - self._lastPos.x()
            else:
                delta = self._lastPos.y() - event.pos().y()

            self._leftover += delta
            self._lastPos = event.pos()

            self.stepBy(int(self._leftover / self._dragSensitivity))
            self._leftover %= self._dragSensitivity

        else:
            if event.buttons() & QtCore.Qt.LeftButton:  # only allow left-click dragging
                if self._dragStart is None:
                    self._dragStart = event.pos()

                if abs(event.x() - self._dragStart.x()) > self._startSensitivity:
                    self._dragType = DRAG_HORIZONTAL
                elif abs(event.y() - self._dragStart.y()) > self._startSensitivity:
                    self._dragType = DRAG_VERTICAL

        self.setSingleStep(stepHolder)

    def mouseReleaseEvent(self, event):
        if self._firstDrag:
            self._firstDrag = False
        elif self._dragType:
            self._dragType = DRAG_NONE
            self._lastPos = QtCore.QPoint()
            self._dragStart = None


class DragDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super(DragDoubleSpinBox, self).__init__(*args, **kwargs)
        self.defaultValue = 0.0
        self._dragSensitivity = 5  # pixels per step
        self._startSensitivity = 10  # pixel move to start the dragging
        # private vars
        self._lastPos = QtCore.QPoint()
        self._leftover = 0
        self._dragStart = None
        self._firstDrag = False
        self._dragType = DRAG_NONE

    def mousePressEvent(self, event):
        if event.button() & QtCore.Qt.RightButton:
            self.setValue(self.defaultValue)
            return True

    def mouseMoveEvent(self, event):
        stepHolder = self.singleStep()
        if self._dragType:
            if self._dragType == DRAG_HORIZONTAL:
                delta = event.pos().x() - self._lastPos.x()
            else:
                delta = self._lastPos.y() - event.pos().y()

            self._leftover += delta
            self._lastPos = event.pos()

            self.stepBy(int(self._leftover / self._dragSensitivity))
            self._leftover %= self._dragSensitivity

        else:
            if event.buttons() & QtCore.Qt.LeftButton:  # only allow left-click dragging
                if self._dragStart is None:
                    self._dragStart = event.pos()

                if abs(event.x() - self._dragStart.x()) > self._startSensitivity:
                    self._dragType = DRAG_HORIZONTAL
                elif abs(event.y() - self._dragStart.y()) > self._startSensitivity:
                    self._dragType = DRAG_VERTICAL

        self.setSingleStep(stepHolder)

    def mouseReleaseEvent(self, event):
        if self._firstDrag:
            self._firstDrag = False
        elif self._dragType:
            self._dragType = DRAG_NONE
            self._lastPos = QtCore.QPoint()
            self._dragStart = None


class VectorSpinBox(QtWidgets.QWidget):
    """Vector base Widget with spin box for transformations for n axis
    3 x QDoubleSpinBox (numerical textEdit with spinBox)
    """
    valueChanged = QtCore.Signal(tuple)

    def __init__(self, label, value, min, max, axis, parent=None, step=0.1, setDecimals=2, toolTip=""):
        """Creates a double spinbox for axis and lays them out in a horizontal layout
        We give access to each spinbox with a property eg. self.x which returns the float value

        :param label: the label for the vector eg. translate, if the label is None or "" then it will be excluded
        :type label: str
        :param value: n floats corresponding with axis param
        :type value: tuple of float or list of float
        :param min: the min value for all three elements of the vector
        :type min: float
        :param max: the max value for all three elements of the vector
        :type max: float
        :param axis: every axis which will have a doubleSpinBox eg. [X,Y,Z] or [X,Y,Z,W]
        :type axis: list or tuple
        :param parent: the widget parent
        :type parent: QtWidget
        :param step: the step amount while clicking on the spin box or keyboard up/down
        :type step: float
        """
        super(VectorSpinBox, self).__init__(parent=parent)
        self.mainLayout = hBoxLayout(self, (2, 2, 2, 2), uiconstants.SREG)
        self.setToolTip(toolTip)
        if label:
            self.label = QtWidgets.QLabel(label, parent=self)
            self.mainLayout.addWidget(self.label)
        self._widgets = OrderedDict()

        for i, v in enumerate(axis):
            box = QtWidgets.QDoubleSpinBox(self)
            box.setSingleStep(step)
            box.setObjectName("".join([label, v]))
            box.setRange(min, max)
            box.setValue(value[i])
            box.setDecimals(setDecimals)
            box.valueChanged.connect(self.onValueChanged)
            self._widgets[v] = box
            self.mainLayout.addWidget(box)

    def __getattr__(self, item):
        widget = self._widgets.get(item)
        if widget is not None:
            return float(widget.value())
        return super(VectorSpinBox, self).__getAttribute__(item)

    def onValueChanged(self):
        self.valueChanged.emit(tuple([float(i.value()) for i in self._widgets.values()]))

    def widget(self, axis):
        return self._widgets.get(axis)

    def value(self):
        return tuple([float(i.value()) for i in self._widgets.values()])

    def setValue(self, value):
        # get the widgets in order
        keys = self._widgets.keys()
        for i, v in enumerate(value):
            self._widgets[keys[i]].setValue(v)



class Matrix(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(tuple)

    def __init__(self, label, matrix, min, max, parent=None):
        """

        :param label: the matrix widget label
        :type label: str
        :param matrix: a list of lists the lenght of each nested list is equal to the column length of the matrix for
         example if we're dealing with a 4x4 matrix then its a length of 4, 3x3 is 3 etc
        :type matrix: list(list(float))
        :param: min: a list of floats, each float is min for each vector
        :type min: list(float)
        :param: max: a list of floats, each float is max for each vector
        :type max: list(float)
        :param parent:
        :type parent:
        """
        super(Matrix, self).__init__(parent=parent)
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setSpacing(uiconstants.SPACING)
        self.label = QtWidgets.QLabel(label, parent=self)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.mainLayout.addWidget(self.label, 0, 0)
        self.mainLayout.addItem(spacerItem, 1, 0)
        self._widgets = OrderedDict()
        axislabels = ("X", "Y", "Z")
        for i, c in enumerate(matrix):
            vec = VectorSpinBox(label="", value=c, min=min[i], max=max[i], axis=axislabels, parent=self)
            self.mainLayout.addWidget(vec, i, 1)
            self._widgets[i] = vec

    def onValueChanged(self):
        """
        :rtype: tuple(tuple(float))
        """
        self.valueChanged.emit(tuple(self._widgets.values()))

    def widget(self, column):
        return self._widgets.get(column)


class Transformation(QtWidgets.QWidget):
    # @todo setup signals
    rotOrders = ("XYZ", "YZX", "ZXY", "XZY", "XYZ", "ZYX")
    axis = ("X", "Y", "Z")
    valueChanged = QtCore.Signal(list, list, list, str)

    def __init__(self, parent=None):
        super(Transformation, self).__init__(parent=parent)
        # self.group = QtWidgets.QGroupBox(parent=self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(*utils.marginsDpiScale(uiconstants.MARGINS))
        self.layout.setSpacing(uiconstants.SPACING)
        # self.group.setLayout(self.layout)
        self.translationVec = VectorSpinBox("Translation:", [0.0, 0.0, 0.0], -99999, 99999, Transformation.axis,
                                            parent=self)
        self.rotationVec = VectorSpinBox("Rotation:", [0.0, 0.0, 0.0], -99999, 99999, Transformation.axis, parent=self)
        self.scaleVec = VectorSpinBox("Scale:", [0.0, 0.0, 0.0], -99999, 99999, Transformation.axis, parent=self)
        self.rotationOrderBox = ComboBoxSearchable("RotationOrder:", Transformation.rotOrders, parent=self)
        self.layout.addWidget(self.translationVec)
        self.layout.addWidget(self.rotationVec)
        self.layout.addWidget(self.rotationVec)
        self.layout.addWidget(self.scaleVec)
        self.layout.addWidget(self.rotationOrderBox)

    def onValueChanged(self, value):
        self.valueChanged.emit(self.translationVec.value(),
                               self.rotationVec.value(),
                               self.scaleVec.value(),
                               self.rotationOrderBox.value())

    def translation(self):
        return self.translationVec.value()

    def rotation(self):
        return self.rotationVec.value()

    def scale(self):
        return self.scaleVec.value()

    def rotationOrder(self):
        """:return: int of the rotation order combo box, not the str
        :rtype: int
        """
        return int(self.rotationOrderBox.currentIndex())

    def rotationOrderValue(self):
        """:return: str of the rotation order combo box, the literal value
        :rtype: str
        """
        return self.rotationOrderBox.value()