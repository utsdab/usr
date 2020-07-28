from Qt import QtWidgets, QtCore


class TreeView(QtWidgets.QTreeView):
    contextMenuRequested = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)
        self._shiftModifierPressed = False
        self.supportsShiftExpand = True
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self._contextMenu)
        self.expanded.connect(self.expandFrom)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def _contextMenu(self, pos):
        menu = QtWidgets.QMenu()
        self.contextMenuRequested.emit(menu)
        menu.exec_(self.mapToGlobal(pos))

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            self._shiftModifierPressed = True
            event.accept()
        super(TreeView, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self._shiftModifierPressed = False
        super(TreeView, self).keyReleaseEvent(event)

    def expandFrom(self, index, expand=True):
        if not self._shiftModifierPressed and self.supportsShiftExpand:
            return
        for i in range(self.model().rowCount(index)):
            childIndex = self.model().index(i, 0, index)
            self.setExpanded(childIndex, expand)
