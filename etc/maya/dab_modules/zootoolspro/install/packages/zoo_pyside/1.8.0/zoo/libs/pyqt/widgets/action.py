__all__ = ("ExtendedQAction", "ColorAction", "SliderAction")

from Qt import QtWidgets, QtGui, QtCore
from zoo.libs import iconlib
from zoo.libs.pyqt.widgets import frame


class ColorAction(QtWidgets.QWidgetAction):
    def __init__(self, actionData, parent):
        super(ColorAction, self).__init__(parent)
        widget = QtWidgets.QWidget(parent)
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QtWidgets.QPushButton(actionData.get("label", ""), parent=widget)
        button.setStyleSheet(
            "QLabel {" + " background-color: {}; color: {};".format(actionData.get("backgroundColor", ""),
                                                                    actionData.get("color", "")) + "}")
        icon = actionData.get("icon")
        if icon:
            if isinstance(icon, QtGui.QIcon):
                button.setIcon(icon)
            else:
                icon = iconlib.icon(icon)
                if not icon.isNull():
                    button.setIcon(icon)
        button.setToolTip(actionData.get("tooltip", ""))
        button.clicked.connect(self.triggered.emit)
        layout.addWidget(button)
        self.setDefaultWidget(widget)


class SliderAction(QtWidgets.QWidgetAction):

    def __init__(self, label="", parent=None):
        """
        :type parent: QtWidgets.QMenu
        """
        QtWidgets.QWidgetAction.__init__(self, parent)

        self.widget = frame.QFrame(parent)
        self.label = QtWidgets.QLabel(label, self.widget)

        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.widget)
        self._slider.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        self.valueChanged = self._slider.valueChanged

    def createWidget(self, menu):
        """
        This method is called by the QWidgetAction base class.

        :type menu: QtWidgets.QMenu
        """
        actionWidget = self.widget
        actionLayout = QtWidgets.QHBoxLayout(actionWidget)
        actionLayout.setContentsMargins(0, 0, 0, 0)
        actionLayout.addWidget(self.label)
        actionLayout.addWidget(self.slider)
        actionWidget.setLayout(actionLayout)

        return actionWidget


class ExtendedQAction(QtWidgets.QWidgetAction):
    """OptionBox style QAction, mirrors as close as possible to autodesk maya's QAction
    """
    optionBoxTriggered = QtCore.Signal()
    triggered = QtCore.Signal()

    def __init__(self, label, iconPath=None, hasOptionBox=False,parent=None):
        super(ExtendedQAction, self).__init__(parent)
        self._label = label
        self._optionBoxIcon = None
        self._icon =None
        if iconPath:
            self.setIcon(iconPath)
        self.hasOptionBox = hasOptionBox
        self._initUi()

    def _initUi(self):
        parent = self.parent()
        self.frame = QtWidgets.QFrame(parent)
        self.iconWidget = QtWidgets.QLabel(parent)
        self.iconWidget.setFixedWidth(29)
        self.label = _ExtendedQLabel(self._label, parent)
        self.optionBox = QtWidgets.QToolButton(parent)
        self.iconWidget.setFixedWidth(29)
        self.label.clicked.connect(self.triggered.emit)
        self.optionBox.clicked.connect(self.optionBoxTriggered.emit)

    def setOptionBoxIcon(self, iconPath):
        self._optionBoxIcon = QtGui.QPixmap(iconPath)
        self.optionBox.setPixmap(self._optionBoxIcon)
        return self._optionBoxIcon

    def setIcon(self, iconPath):
        self._icon = QtGui.QPixmap(iconPath)
        self._iconWidget.setPixmap(self._icon)
        return self._icon

    def createWidget(self, parent):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.iconWidget)
        layout.addWidget(self.label)
        layout.addWidget(self.optionBox)
        self.optionBox.setVisible(self.hasOptionBox)
        self.frame.setLayout(layout)
        return self.frame


class _ExtendedQLabel(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(_ExtendedQLabel, self).__init__(*args, **kwargs)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()

    def enterEvent(self, event):
        self.setStyleSheet("background: palette(highlight);color: palette(highlighted-text);")
        super(_ExtendedQLabel, self).enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("background-color: transparent;")
        super(_ExtendedQLabel, self).leaveEvent(event)
