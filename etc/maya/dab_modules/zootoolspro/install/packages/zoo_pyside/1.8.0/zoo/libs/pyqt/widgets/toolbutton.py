from Qt import QtWidgets, QtCore


class ToolButton(QtWidgets.QToolButton):
    contextMenuRequested = QtCore.Signal(object)

    def __init__(self, label=None, icon=None, parent=None):
        super(ToolButton, self).__init__(parent=parent)
        if icon is not None:
            self.setIcon(icon)
        self.setText(label or "")

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

    def contextMenu(self, position):
        menu = QtWidgets.QMenu(self)
        self.contextMenuRequested.emit(menu)
        menu.exec_(self.mapToGlobal(position))
