from functools import partial

from Qt import QtWidgets, QtCore


class SpinboxSlider(QtWidgets.QWidget):
    """docstring for SpinboxSlider"""

    valueChanged = QtCore.Signal(int)

    def __init__(self, min_=0, max_=100, parent=None):
        super(SpinboxSlider, self).__init__(parent=parent)
        self.range = (min_, max_)

        hbox = QtWidgets.QHBoxLayout(self)

        self.slider = QtWidgets.QSlider(parent=self)
        hbox.addWidget(self.slider)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setRange(*self.range)

        self.spinbox = QtWidgets.QSpinBox(parent=self)
        hbox.addWidget(self.spinbox)
        self.spinbox.setRange(*self.range)

        self.slider.valueChanged.connect(partial(self.onUpdate, self.spinbox))
        self.spinbox.valueChanged.connect(partial(self.onUpdate, self.slider))

    def onUpdate(self, widget, value):
        widget.blockSignals(True)
        widget.setValue(value)
        widget.blockSignals(False)
        self.valueChanged.emit(value)

    def setRange(self, min_, max_):
        self.range = (min_, max_)
        self.slider.setRange(*self.range)
        self.spinbox.setRange(*self.range)

