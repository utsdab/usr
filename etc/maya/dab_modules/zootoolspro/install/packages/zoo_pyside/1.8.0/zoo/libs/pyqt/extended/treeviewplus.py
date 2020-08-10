from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import extendedmenu, treeview, elements, frame
from zoo.libs.pyqt.extended import viewfilterwidget
from zoo.libs.pyqt.models import sortmodel
from Qt import QtWidgets, QtCore


class TreeViewPlus(frame.QFrame):
    selectionChanged = QtCore.Signal(list, list)
    contextMenuRequested = QtCore.Signal(object, list)
    refreshRequested = QtCore.Signal()

    def __init__(self, searchable=False, parent=None, expand=True, sorting=True, labelVisible=True, comboVisible=True):
        super(TreeViewPlus, self).__init__(parent=parent)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame | QtWidgets.QFrame.Plain)
        self._labelVisible = labelVisible
        self._comboVisible = comboVisible
        self.sorting = sorting
        self.model = None
        self.columnDataSources = []
        self._setupLayouts()
        self.connections()
        self.setSearchable(searchable)
        if expand:
            self.expandAll()

    def resizeToContents(self):
        header = self.treeView.header()
        header.setSectionResizeMode(header.ResizeToContents)

    def reloadVisible(self, state):
        self.reloadBtn.setVisible(state)

    def setDragDropMode(self, mode):
        self.treeView.setDragDropMode(mode)

    def expandAll(self):
        self.treeView.expandAll()

    def collapseAll(self):
        self.treeView.collapseAll()

    def setSearchable(self, value):
        self.searchWidget.setVisible(value)

    def supportShiftExpansion(self, state):
        self.treeView.supportsShiftExpand = state

    def setAlternatingColorEnabled(self, alternating):
        """ Disable alternating color for the rows

        :type alternating: bool
        :return:
        """
        if alternating:
            utils.setStylesheetObjectName(self.treeView, "")
        else:
            utils.setStylesheetObjectName(self.treeView, "disableAlternatingColor")

    def _setupFilter(self):
        self.reloadBtn = elements.styledButton(icon="reload", parent=self)
        self.searchLayout = utils.hBoxLayout()

        self.searchWidget = viewfilterwidget.ViewSearchWidget(showColumnVisBox=False, parent=self)

        self.searchWidget.searchBoxLabel.setVisible(self._labelVisible)
        self.searchWidget.searchHeaderBox.setVisible(self._comboVisible)

        self.searchLayout.addWidget(self.reloadBtn)
        self.searchLayout.addStretch(0)
        self.searchLayout.addWidget(self.searchWidget)
        self.mainLayout.addLayout(self.searchLayout)
        self.reloadVisible(False)

    def _setupLayouts(self):

        self.mainLayout = utils.vBoxLayout()
        self.treeView = treeview.TreeView(parent=self)
        self.treeView.setSelectionMode(self.treeView.ExtendedSelection)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.treeView.customContextMenuRequested.connect(self.contextMenu)
        self._setupFilter()

        self.mainLayout.addWidget(self.treeView)

        self.proxySearch = sortmodel.LeafTreeFilterProxyModel(sort=False)  # sorting will be done in next line
        self.setSortingEnabled(self.sorting)
        self.treeView.setAlternatingRowColors(True)
        self.setLayout(self.mainLayout)

    def selectionModel(self):
        return self.treeView.selectionModel()

    def setSortingEnabled(self, enabled):
        self.treeView.setModel(self.proxySearch)
        self.treeView.setSortingEnabled(enabled)
        self.proxySearch.setDynamicSortFilter(enabled)

    def selectedItems(self):
        indices = self.selectionModel().selectedRows()
        model = self.model
        return [model.itemFromIndex(i) for i in indices]

    def selectedQIndices(self):
        indices = self.selectionModel().selectedRows()
        return indices

    def connections(self):
        self.searchWidget.columnFilterIndexChanged.connect(self.onSearchBoxChanged)
        self.searchWidget.searchTextedChanged.connect(self.proxySearch.setFilterRegExp)
        self.reloadBtn.clicked.connect(self.refresh)
        selModel = self.selectionModel()  # had to assign a var otherwise the c++ object gets deleted in PySide1
        selModel.selectionChanged.connect(self.onSelectionChanged)
        self.treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.header().customContextMenuRequested.connect(self._headerMenu)

    def _headerMenu(self, pos):
        globalPos = self.mapToGlobal(pos)
        menu = QtWidgets.QMenu(parent=self)
        headers = self.headerItems()
        for i in range(len(headers)):
            item = QtWidgets.QAction(headers[i], menu, checkable=True)
            menu.addAction(item)
            item.setChecked(not self.treeView.header().isSectionHidden(i))
            item.setData({"index": i})
        selectedItem = menu.exec_(globalPos)
        self.toggleColumn(selectedItem.data()["index"],
                          QtCore.Qt.Checked if selectedItem.isChecked() else QtCore.Qt.Unchecked)

    def setModel(self, model):
        self.proxySearch.setSourceModel(model)
        self.proxySearch.setDynamicSortFilter(True)
        self.model = model

    def onSelectionChanged(self, current, previous):
        indices = current.indexes()
        self.selectionChanged.emit([self.model.itemFromIndex(i) for i in indices],
                                   [self.model.itemFromIndex(i) for i in previous.indexes()])

    def onSearchBoxChanged(self, index, text):
        self.proxySearch.setFilterKeyColumn(index)

    def headerItems(self):
        headerItems = []
        for index in range(self.model.columnCount(QtCore.QModelIndex())):
            headerItems.append(self.model.root.headerText(index))
        return headerItems

    def refresh(self):
        headerItems = []
        for index in range(self.model.columnCount(QtCore.QModelIndex())):
            self.treeView.resizeColumnToContents(index)
            newWidth = self.treeView.columnWidth(index) + 10
            self.treeView.setColumnWidth(index, newWidth)
            headerItems.append(self.model.root.headerText(index))
        self.searchWidget.setHeaderItems(headerItems)

    def contextMenu(self, position):
        menu = extendedmenu.ExtendedMenu(parent=self)
        self.contextMenuRequested.emit(menu, self.selectedItems())
        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def toggleColumn(self, column, state):
        if column == 0:

            if state == QtCore.Qt.Checked:
                self.treeView.showColumn(0)
            else:
                self.treeView.hideColumn(0)
        else:
            if state == QtCore.Qt.Checked:
                self.treeView.showColumn(column)
            else:
                self.treeView.hideColumn(column)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    view = TreeViewPlus()
    view.show()
    sys.exit(app.exec_())
