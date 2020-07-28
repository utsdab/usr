"""
Breadcrumb Widget

..code-block:: python

    from zoo.libs.pyqt.widgets.breadcrumb import Breadcrumb
    parentWidget = QtWidgets.QWidget()
    parentLayout = elements.hBoxLayout(parent=parentWidget)
    bread = Breadcrumb(parent=parentWidget)
    parentLayout.addWidget(bread)
    bread.setWidgetList([
        {"text": "home", "icon": "redshift"},
        {"text": "bob", "icon": "renderman"},
        {"text": "bob2", "icon": "transfer"}
    ])

    parentWidget.show()

"""
from zoo.libs.pyqt.widgets import elements
from Qt import QtWidgets


class Breadcrumb(QtWidgets.QWidget):
    """Breadcrumb creates a interactive path like widget where each item is a button
    """
    def __init__(self, separator='/', parent=None):
        super(Breadcrumb, self).__init__(parent)
        self._separator = separator
        self._mainLayout = elements.hBoxLayout(parent=self)
        self._mainLayout.addStretch()
        self.setLayout(self._mainLayout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self._buttonGroup = QtWidgets.QButtonGroup()

    def setWidgetList(self, widgetList):
        """Set the breadcrumb items.
        """
        for button in self._buttonGroup.buttons():
            self._button_group.removeButton(button)
            self._mainLayout.removeWidget(button)
            button.setVisible(False)

        for index, widgetData in enumerate(widgetList):
            self.addWidget(widgetData, index)

    def addWidget(self, widgetData, index=None):
        """Add a item the the path.

        :param widgetData a list of dict with the same arguments :func:`elements.styledButton`, \
        "leftClickCallback" will connect the leftclick signal to the specified function.
        :type widgetData: list(dict)
        :param index: The position in the layout to add the widget
        :type index: int
        """
        button = elements.styledButton(parent=self,
                                       **widgetData
                                       )

        if self._buttonGroup.buttons():
            separator = elements.Label(self._separator)
            self._mainLayout.addWidget(separator)

        self._mainLayout.addWidget(button)

        if index is None:
            self._buttonGroup.addButton(button)
        else:
            self._buttonGroup.addButton(button, index)
        lmbCallback = widgetData.get("leftClickCallback")
        if lmbCallback is not None:
            button.leftClicked.connect(lmbCallback)
        return button
