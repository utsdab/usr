from Qt import QtWidgets, QtCore


class TableView(QtWidgets.QTableView):
    contextMenuRequested = QtCore.Signal()

    def __init__(self, parent):
        super(TableView, self).__init__(parent)
        self.setSelectionMode(self.ExtendedSelection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.customContextMenuRequested.connect(self.contextMenuRequested.emit)

    def commitData(self, editor):
        theModel = self.currentIndex().model()
        data = theModel.data(self.currentIndex(), QtCore.Qt.EditRole)

        for index in self.selectedIndexes():
            if index == self.currentIndex():
                continue
            # Supply None as the value
            self.model().setData(index, data, QtCore.Qt.EditRole)
        super(TableView, self).commitData(editor)
