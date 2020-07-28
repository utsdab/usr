from Qt import QtCore


class LeafTreeFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None, sort=True):
        super(LeafTreeFilterProxyModel, self).__init__(parent)
        # set proxy to auto sort alphabetically
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

        if sort:
            self.setDynamicSortFilter(True)
            self.setFilterKeyColumn(0)

    def filterAcceptsRow(self, row_num, source_parent):
        search_exp = self.filterRegExp()
        search_exp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        # if there is no search criteria, exit early!
        if search_exp.isEmpty():
            return True
        # look at the node and all its children to see if we should keep or cull.
        model = self.sourceModel()
        if not source_parent.isValid():
            item = model.root.child(row_num)
        else:
            modelIndex = source_parent.child(row_num, self.filterKeyColumn())
            item = model.itemFromIndex(modelIndex)
        return self._match(search_exp, item, self.filterKeyColumn())

    def _match(self, searchExpr, item, column):
        if searchExpr.indexIn(item.data(column)) != -1:
            return True
        for idx in range(item.rowCount()):
            childItem = item.child(idx)
            if self._match(searchExpr, childItem, column):
                return True
        return False

    def setFilterFixedString(self, pattern):
        return super(LeafTreeFilterProxyModel, self).setFilterFixedString(pattern if len(pattern) >= 2 else "")


class TableFilterProxyModel(QtCore.QSortFilterProxyModel):
    """ Class to override the following behaviour:
            If a parent item doesn't match the filter,
            none of its children will be shown.

        This Model matches items which are descendants
        or ascendants of matching items.
    """

    def __init__(self, parent=None):
        super(TableFilterProxyModel, self).__init__(parent)
        # set proxy to auto sort alphabetically
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)
        self.setFilterKeyColumn(0)

    def filterAcceptsRow(self, row_num, source_parent):
        search_exp = self.filterRegExp()
        search_exp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        # if there is no search criteria, exit early!
        if search_exp.isEmpty():
            return True
        # look at the node and all its children to see if we should keep or cull.
        model = self.sourceModel()
        column = self.filterKeyColumn()

        if column == 0:
            data = model.rowDataSource.data(row_num)
        else:
            data = model.columnDataSources[column - 1].data(model.rowDataSource, row_num)
        if search_exp.indexIn(str(data)) != -1:
            return True

        return False

    def sort(self, column, order):
        """Sort table by given column number.
        """
        model = self.sourceModel()
        if not model:
            return
        self.layoutAboutToBeChanged.emit()
        if column == 0:
            model.rowDataSource.sort(index=column, order=order)
        else:
            model.columnDataSources[column - 1].sort(rowDataSource=model.rowDataSource, index=column, order=order)
        self.layoutChanged.emit()
