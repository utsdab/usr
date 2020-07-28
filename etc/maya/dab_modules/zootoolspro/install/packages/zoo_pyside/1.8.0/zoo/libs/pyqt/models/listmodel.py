from Qt import QtCore, QtGui


class ListModel(QtCore.QAbstractTableModel):
    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1
    userObject = QtCore.Qt.UserRole + 2

    def __init__(self, parent=None):
        """first element is the rowDataSource
        :param parent:
        :type parent:
        """
        super(ListModel, self).__init__(parent=parent)
        self.rowDataSource = None

    def reload(self):
        """Hard reloads the model, we do this by the modelReset slot, the reason why we do this instead of insertRows()
        is because we expect that the tree structure has already been rebuilt with its children so by calling insertRows
        we would in turn create duplicates.

        """
        self.modelReset.emit()

    def rowCount(self, parent):
        if parent.column() > 0 or not self.rowDataSource:
            return 0
        return self.rowDataSource.rowCount()
    def columnCount(self, parent):
        return 1
    def data(self, index, role):
        if not index.isValid():
            return None
        row = int(index.row())
        dataSource = self.rowDataSource
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return dataSource.data(row)
        elif role == QtCore.Qt.ToolTipRole:
            return dataSource.toolTip(row)
        elif role == QtCore.Qt.DecorationRole:
            return dataSource.icon(row)
        elif role == QtCore.Qt.BackgroundRole:
            color = dataSource.backgroundColor(row)
            if color:
                return QtGui.QColor(*color)
        elif role == QtCore.Qt.ForegroundRole:
            color = dataSource.foregroundColor(row)
            if color:
                return QtGui.QColor(*color)
        elif role in (ListModel.sortRole, ListModel.filterRole):
            return dataSource.data(row)
        elif role == ListModel.userObject:
            return dataSource.userObject(row)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or not self.rowDataSource:
            return False
        if role == QtCore.Qt.EditRole:
            self.rowDataSource.setData(index.row(), value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def mimeTypes(self):
        return self.rowDataSource.mimeTypes()

    def mimeData(self, indices):
        return self.rowDataSource.mimeData(indices)

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def flags(self, index):
        if not index.isValid() or not self.rowDataSource:
            return QtCore.Qt.NoItemFlags
        row = index.row()
        dataSource = self.rowDataSource

        flags = QtCore.Qt.ItemIsEnabled
        if dataSource.supportsDrag(row):
            flags |= QtCore.Qt.ItemIsDragEnabled
        if dataSource.supportsDrop(row):
            flags |= QtCore.Qt.ItemIsDropEnabled
        if dataSource.isEditable(row):
            flags |= QtCore.Qt.ItemIsEditable
        if dataSource.isSelectable(row):
            flags |= QtCore.Qt.ItemIsSelectable
        if dataSource.isEnabled(row):
            flags |= QtCore.Qt.ItemIsEnabled
        return flags

    def headerData(self, section, orientation, role):
        dataSource = self.rowDataSource
        if role == QtCore.Qt.DisplayRole:
            return dataSource.headerText(section)
        elif role == QtCore.Qt.DecorationRole:
            icon = dataSource.headerIcon(section)
            if icon.isNull:
                return
            return icon.pixmap(icon.availableSizes()[-1])
        return None

    def insertRow(self, position, parent=QtCore.QModelIndex(), **kwargs):
        self.beginInsertRows(parent, position, position)
        result = self.rowDataSource.insertRowDataSource(int(position), **kwargs)
        self.endInsertRows()

        return result

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        self.rowDataSource.insertRowDataSources(int(position), int(rows))
        self.endInsertRows()
        return True

    def itemFromIndex(self, index):
        """Returns the user Object from the rowDataSource

        :param index:
        :type index: QtCore.Qt.QModelIndex
        :return:
        :rtype:
        """
        return index.data(self.userObject) if index.isValid() else self.rowDataSource.userObject(index.row())
