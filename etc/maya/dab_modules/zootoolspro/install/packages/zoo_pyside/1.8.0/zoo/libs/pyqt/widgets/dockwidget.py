from Qt import QtWidgets


class DockWidget(QtWidgets.QDockWidget):
    def __init__(self, title, parent=None, floating=False):
        super(DockWidget, self).__init__(title, parent)
        self.setFloating(floating)
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable |
            QtWidgets.QDockWidget.DockWidgetClosable)
