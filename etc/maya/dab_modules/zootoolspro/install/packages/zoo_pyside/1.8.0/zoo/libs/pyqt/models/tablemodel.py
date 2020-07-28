from Qt import QtCore, QtGui
from zoo.libs.pyqt.models import constants


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent=None):
        """first element is the rowDataSource

        :param parent:
        :type parent:
        """
        super(TableModel, self).__init__(parent=parent)
        self._rowDataSource = None
        self.columnDataSources = []

    @property
    def rowDataSource(self):
        return self._rowDataSource

    @rowDataSource.setter
    def rowDataSource(self, source):
        self._rowDataSource = source

    def columnDataSource(self, index):
        if not self._rowDataSource or not self.columnDataSources:
            return

        return self.columnDataSources[index - 1]

    def dataSource(self, index):
        if index == 0:
            return self._rowDataSource
        return self.columnDataSources[index - 1]

    def reload(self):
        """Hard reloads the model, we do this by the modelReset slot, the reason why we do this instead of insertRows()
        is because we expect that the tree structure has already been rebuilt with its children so by calling insertRows
        we would in turn create duplicates.
        """
        self.modelReset.emit()

    def rowCount(self, parent):
        if parent.column() > 0 or not self._rowDataSource or not self.columnDataSources:
            return 0
        return self._rowDataSource.rowCount()

    def columnCount(self, parent):
        if not self._rowDataSource or not self.columnDataSources:
            return 0
        return len(self.columnDataSources) + 1

    def data(self, index, role):
        if not index.isValid():
            return None

        column = int(index.column())
        row = int(index.row())
        dataSource = self.dataSource(column)

        if dataSource is None:
            return
        if column == 0:
            kwargs = {"index": row}
        else:
            kwargs = {"rowDataSource": self._rowDataSource,
                      "index": row}
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return dataSource.data(**kwargs)
        elif role == QtCore.Qt.ToolTipRole:
            return dataSource.toolTip(**kwargs)
        elif role == QtCore.Qt.DecorationRole:
            return dataSource.icon(**kwargs)
        elif role == QtCore.Qt.CheckStateRole and dataSource.isCheckable(**kwargs):
            if dataSource.data(**kwargs):
                return QtCore.Qt.Checked
            return QtCore.Qt.Unchecked
        elif role == constants.editChangedRole:
            return dataSource.displayChangedColor(**kwargs)
        elif role == QtCore.Qt.TextAlignmentRole:
            return dataSource.alignment(**kwargs)
        elif role == QtCore.Qt.FontRole:
            return dataSource.font(**kwargs)
        elif role == QtCore.Qt.BackgroundRole:
            color = dataSource.backgroundColor(**kwargs)
            if color:
                return color
        elif role == QtCore.Qt.ForegroundRole:
            color = dataSource.foregroundColor(**kwargs)
            if color:
                return color
        elif role == constants.minValue:
            return dataSource.minimum(**kwargs)
        elif role == constants.maxValue:
            return dataSource.maximum(**kwargs)
        elif role == constants.enumsRole:
            return dataSource.enums(**kwargs)
        elif role == constants.userObject:
            return dataSource.userObject(row)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or not self._rowDataSource:
            return False
        if role == QtCore.Qt.EditRole:
            column = index.column()
            if column == 0:
                result = self._rowDataSource.setData(index.row(), value)
            else:
                result = self.columnDataSources[column - 1].setData(self._rowDataSource, index.row(), value)
            if result:
                self.dataChanged.emit(index, index)
                return True
        return False

    def flags(self, index):
        if not index.isValid() or not self._rowDataSource:
            return QtCore.Qt.NoItemFlags
        row = index.row()
        column = index.column()
        dataSource = self.dataSource(column)
        if column == 0:
            kwargs = {"index": row}
        else:
            kwargs = {"rowDataSource": self._rowDataSource,
                      "index": row}
        flags = QtCore.Qt.ItemIsEnabled
        if dataSource.isCheckable(**kwargs):
            flags |= QtCore.Qt.ItemIsUserCheckable
        if dataSource.isEditable(**kwargs):
            flags |= QtCore.Qt.ItemIsEditable
        if dataSource.isSelectable(**kwargs):
            flags |= QtCore.Qt.ItemIsSelectable
        if dataSource.isEnabled(**kwargs):
            flags |= QtCore.Qt.ItemIsEnabled
        return flags

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            dataSource = self.dataSource(section)

            if role == QtCore.Qt.DisplayRole:
                return dataSource.headerText(section)
            elif role == QtCore.Qt.DecorationRole:
                icon = dataSource.headerIcon()
                if icon.isNull:
                    return
                return icon.pixmap(icon.availableSizes()[-1])

        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return self._rowDataSource.headerVerticalText(section)
            elif role == QtCore.Qt.DecorationRole:
                icon = self._rowDataSource.headerVerticalIcon(section)
                if icon.isNull():
                    return
                return icon.pixmap(icon.availableSizes()[-1])
        return None

    def insertRow(self, position, parent=QtCore.QModelIndex(), **kwargs):
        self.beginInsertRows(parent, position, position)
        result = self._rowDataSource.insertRowDataSource(int(position), **kwargs)
        self.endInsertRows()

        return result

    def insertRows(self, position, rows, parent=QtCore.QModelIndex(), **kwargs):
        self.beginInsertRows(parent, position, position + rows - 1)
        result = self._rowDataSource.insertRowDataSources(int(position), int(rows), **kwargs)
        self.endInsertRows()
        return result

    def insertColumns(self, position, columns, parent=QtCore.QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        result = self._rowDataSource.insertColumnDataSources(int(position), int(columns))
        self.endInsertColumns()
        return result

    def removeRow(self, position, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position)
        result = self._rowDataSource.removeRowDataSource(int(position))
        self.endRemoveRows()
        return result

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        result = self._rowDataSource.insertColumnDataSources(int(position), int(rows))
        self.endRemoveRows()
        return result

    def itemFromIndex(self, index):
        """Returns the user Object from the rowDataSource
        :param index:
        :type index:
        :return:
        :rtype:
        """
        return index.data() if index.isValid() else self._rowDataSource.userObject(index.row())

    def sort(self, column, order):
        """Sort table by given column number.
        """

        self.layoutAboutToBeChanged.emit()
        if column == 0:
            self.rowDataSource.sort(index=column, order=order)
        else:
            self.columnDataSources[column - 1].sort(rowDataSource=self.rowDataSource, index=column, order=order)
        self.layoutChanged.emit()
