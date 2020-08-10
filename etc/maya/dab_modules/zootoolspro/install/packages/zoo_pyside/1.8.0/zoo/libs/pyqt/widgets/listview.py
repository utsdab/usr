from Qt import QtWidgets, QtCore


class ListView(QtWidgets.QListView):
    # emits the selection List as items directly from the model and the QMenu at the mouse position
    contextMenuRequested = QtCore.Signal(list, object)

    def __init__(self, parent=None):
        super(ListView, self).__init__(parent=parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenu)

    def _contextMenu(self, position):
        model = self.model()
        if model is None:
            return
        menu = QtWidgets.QMenu(self)
        selectionModel = self.selectionModel()
        selection = [model.itemFromIndex(index) for index in selectionModel.selectedIndexes()]
        self.contextMenuRequested.emit(selection, menu)
        menu.exec_(self.viewport().mapToGlobal(position))

    def model(self):
        """

        :return:
        :rtype: QtGui.QStandardItemModel
        """
        return super(ListView, self).model()
