from Qt import QtWidgets, QtCore


class PushButton(QtWidgets.QPushButton):
    contextMenuRequested = QtCore.Signal(object)

    def __init__(self, label=None, icon=None, parent=None):
        super(PushButton, self).__init__(parent=parent)
        if icon is not None:
            self.setIcon(icon)
        self.setText(label or "")

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuRequested.emit)

    def contextMenu(self, position):
        menu = QtWidgets.QMenu(self)
        self.contextMenuRequested.emit(menu)
        menu.exec_(self.mapToGlobal(position))
