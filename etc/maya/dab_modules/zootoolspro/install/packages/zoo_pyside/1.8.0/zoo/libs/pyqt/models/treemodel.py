"""This module is for a standard Qt tree model
"""
from Qt import QtCore
from zoovendor.six.moves import cPickle


class TreeModel(QtCore.QAbstractItemModel):
    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1
    userObject = QtCore.Qt.UserRole + 2

    def __init__(self, root, parent=None):
        super(TreeModel, self).__init__(parent)
        self.root = root
        if self.root:
            self.root.model = self

    def reload(self):
        """Hard reloads the model, we do this by the modelReset slot, the reason why we do this instead of insertRows()
        is because we expect that the tree structure has already been rebuilt with its children so by calling insertRows
        we would in turn create duplicates.
        """
        self.modelReset.emit()

    def itemFromIndex(self, index):
        return index.data(self.userObject) if index.isValid() else self.root

    def rowCount(self, parent):
        if self.root is None:
            return 0
        parentItem = self.itemFromIndex(parent)
        return parentItem.rowCount()

    def columnCount(self, parent):
        if self.root is None:
            return 0
        return self.root.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        column = index.column()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return item.data(column)
        elif role == QtCore.Qt.ToolTipRole:
            return item.toolTip(column)
        elif role == QtCore.Qt.DecorationRole:
            return item.icon(column)
        elif role == QtCore.Qt.CheckStateRole and item.isCheckable(column):
            if item.data(column):
                return QtCore.Qt.Checked
            return QtCore.Qt.Unchecked
        elif role == QtCore.Qt.BackgroundRole:
            color = item.backgroundColor(column)
            if color:
                return color
        elif role == QtCore.Qt.ForegroundRole:
            color = item.foregroundColor(column)
            if color:
                return color
        elif role == QtCore.Qt.TextAlignmentRole:
            return item.alignment(index)
        elif role == QtCore.Qt.FontRole:
            return item.font(column)
        elif role in (TreeModel.sortRole, TreeModel.filterRole):
            return item.data(column)
        elif role == TreeModel.userObject:
            return item

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        pointer = index.internalPointer()
        if role == QtCore.Qt.EditRole:
            column = index.column()
            pointer.setData(column, value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        column = index.column()
        pointer = index.internalPointer()
        flags = QtCore.Qt.ItemIsEnabled
        if pointer.supportsDrag(column):
            flags |= QtCore.Qt.ItemIsDragEnabled
        if pointer.supportsDrop(column):
            flags |= QtCore.Qt.ItemIsDropEnabled
        if pointer.isEditable(column):
            flags |= QtCore.Qt.ItemIsEditable
        if pointer.isSelectable(column):
            flags |= QtCore.Qt.ItemIsSelectable
        if pointer.isEnabled(column):
            flags |= QtCore.Qt.ItemIsEnabled
        if pointer.isCheckable(column):
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-datasource"]

    def mimeData(self, indices):
        """Encode serialized data from the item at the given index into a QMimeData object."""
        data = ""
        for i in indices:
            item = self.itemFromIndex(i)
            pickleData = item.mimeData(i)
            if pickleData:
                data += "//"+cPickle.dumps(pickleData)
        mimedata = QtCore.QMimeData()
        if data:
            mimedata.setData("application/x-datasource", data)
        return mimedata

    def dropMimeData(self, mimedata, action, row, column, parentIndex):
        if not mimedata.hasFormat("application/x-datasource"):
            return False
        data = str(mimedata.data("application/x-datasource"))
        items = []
        for d in data.split("//"):
            if not d:
                continue
            try:
                item = cPickle.loads(d)
            except Exception as e:
                raise
            items.append(item)
        if not items:
            return False
        dropParent = self.itemFromIndex(parentIndex)
        returnKwargs = dropParent.dropMimeData(items)

        self.insertRows(dropParent.rowCount()-1, len(items), parentIndex, **returnKwargs)
        self.dataChanged.emit(parentIndex, parentIndex)
        return True

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.root.headerText(section)
            elif role == QtCore.Qt.DecorationRole:
                icon = self.root.headerIcon()
                if icon.isNull:
                    return
                return icon.pixmap(icon.availableSizes()[-1])
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parentItem = self.itemFromIndex(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parentSource()
        if parentItem == self.root or parentItem is None:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.index(), 0, parentItem)

    def insertRow(self, position, parent=QtCore.QModelIndex(), **kwargs):
        parentItem = self.itemFromIndex(parent)

        if position < 0 or position > len(parentItem.children):
            return False
        self.beginInsertRows(parent, position, position)
        parentItem.insertRowDataSource(position, **kwargs)
        self.endInsertRows()

        return True

    def insertRows(self, position, count, parent=QtCore.QModelIndex(), **kwargs):
        parentItem = self.itemFromIndex(parent)

        if position < 0:
            return False
        self.beginInsertRows(parent, position, position + count - 1)
        parentItem.insertRowDataSources(int(position), int(count), **kwargs)
        self.endInsertRows()
        return True

    def removeRows(self, position, count, parent=QtCore.QModelIndex(), **kwargs):
        parentNode = self.itemFromIndex(parent)

        if position < 0 or position > len(parentNode.children):
            return False
        self.beginRemoveRows(parent, position, position + count - 1)
        result = parentNode.removeRowDataSources(int(position), int(count), **kwargs)
        self.endRemoveRows()

        return result

    def removeRow(self, position, parent=QtCore.QModelIndex()):
        parentNode = self.itemFromIndex(parent)

        if position < 0 or position > len(parentNode.children):
            return False
        self.beginRemoveRows(parent, position, position)
        success = parentNode.removeRowDataSource(position)

        self.endRemoveRows()

        return success
