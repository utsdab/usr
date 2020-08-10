"""This Module contains generic classes for handle table model data items
Broken into to main base classes:

    BaseDataSource - Used to represent Table rows
    ColumnDataSource - Used to represent Table columns

Subclasses defined here contain linked delegates based on dataType i.e list == combobox

"""
from zoovendor.six.moves import range
from zoo.libs.pyqt.models import delegates
from Qt import QtCore, QtGui


class BaseDataSource(QtCore.QObject):
    enabledColor = QtGui.QColor(200, 200, 220)
    disabledColor = enabledColor.darker(200)

    def __init__(self, headerText=None, model=None, parent=None):
        super(BaseDataSource, self).__init__()
        self._parent = parent
        self.children = []
        self.model = model
        self._columnIndex = 0
        self._headerText = headerText or ""
        self._font = QtGui.QFont()
        self._font.setFamily("Roboto")
        self._font.setPointSize(10)

    def width(self):
        return 0

    def userObject(self, index):
        if index in range(self.rowCount()):
            return self.children[index]

    def userObjects(self):
        return self.children

    def setUserObjects(self, objects):
        pass

    def isRoot(self):
        """Determines if this item is the root of the tree
        :return:
        :rtype:
        """
        return True if self.parent else False

    def rowCount(self):
        """Returns the total row count for the dataSource defaults to the len of the dataSource children
        :rtype: int
        """
        return len(self.children)

    def columnCount(self):
        return 1

    def parentSource(self):
        """Returns the parent of this node
        :rtype: Node
        """
        return self._parent

    def index(self):
        if self._parent is not None and self._parent.children:
            return self._parent.children.index(self)
        return 0

    def child(self, index):
        """
        :param index: the column index
        :type index: int
        """
        if index in range(self.rowCount()):
            return self.children[index]

    def addChild(self, child):
        self.children.append(child)

    def insertChild(self, index, child):
        if child not in self.children:
            self.children.insert(index, child)

    def setData(self, index, value):
        """Sets the text value of this node at the specified column
        :param index: The column index
        :type index: int
        :return: the new text value for this nodes column index
        :rtype: str
        """
        pass

    def data(self, index):
        """The text for this node or column. index parameter with a value of 0 is
        the first column.
        :param index: The column index for the item
        :type index: int
        :return: the column text
        :rtype: str
        """
        return ""

    def toolTip(self, index):
        """The tooltip for the index.
        :param index: The column index for the item
        :type index: int
        :rtype: str
        """
        model = self.model
        if model is None:
            return ""
        msg = self.headerText(index) + ":" + str(self.data(index)) + "\n"
        return msg

    def icon(self, index):
        """The icon for the index.
        :param index: The column index for the item
        :type index: int
        :rtype: QtGui.QIcon
        """
        pass

    def headerIcon(self):
        """Returns the column header icon
        :rtype: QtGui.QIcon
        """
        return QtGui.QIcon()

    def headerText(self, index):
        """Returns the column header text
        :return: the header value
        :rtype: str
        """
        return self._headerText

    def headerVerticalText(self, index):
        """The Vertical header text, if the return type is None then no text is displayed, an empty string will
        produce a gap in the header
        :param index: The column index for the item
        :type index: int
        :rtype str or None
        """
        return None

    def headerVerticalIcon(self, index):
        """The Vertical header icon
        :param index: The column index for the item
        :type index: int
        :rtype: QtGui.QIcon()
        """
        return QtGui.QIcon()

    def isEditable(self, index):
        """Determines if this node can be editable e.g set text. Defaults to False
        :param index: The column index for the item
        :type index: int
        :return: whether or not this node is editable, defaults to False
        :rtype: bool
        """
        return self.isEnabled(index)

    def isEnabled(self, index):
        """Determines if this node is enabled
        :param index: The column index for the item
        :type index: int
        :return: whether or not this node is enabled, defaults to True
        :rtype: bool
        """
        return True

    def supportsDrag(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def supportsDrop(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def mimeData(self, indices):
        return QtCore.QMimeData()

    def dropMimeData(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def isSelectable(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return True

    def foregroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        if self.isEnabled(index):
            return self.enabledColor
        return self.disabledColor

    def backgroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return None

    def displayChangedColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return None

    def alignment(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return QtCore.Qt.AlignVCenter

    def font(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return self._font

    def isCheckable(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def insertColumnDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def removeColumnDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def removeRowDataSource(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def removeRowDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def insertRowDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return None

    def insertRowDataSource(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def onVerticalHeaderSelection(self, index):
        """Triggered by the table view(if this source is attached to one) when the vertical header is clicked
        :param index: the row index
        :type index: int
        """
        pass

    def contextMenu(self, selecton, menu):
        pass

    def sort(self, index=0, order=QtCore.Qt.DescendingOrder):
        """This sort function purpose is for sorting the data by column.

        :param index: the column index to sort
        :type index: int
        :param order: The Qt order
        :type order: int
        """

        def element(key):
            return key[1]

        toSort = [(obj, self.data(i)) for i, obj in enumerate(self.userObjects())]

        if order == QtCore.Qt.DescendingOrder:
            results = [i[0] for i in sorted(toSort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(toSort, key=element)]
        self.setUserObjects(results)


class ColumnDataSource(BaseDataSource):
    def __init__(self, headerText=None, model=None, parent=None):
        super(ColumnDataSource, self).__init__(headerText, model, parent)

    def sort(self, rowDataSource, index=0, order=QtCore.Qt.DescendingOrder):
        """This sort function purpose is for sorting the data by column.

        :param index: the column index to sort
        :type index: int
        :param order: The Qt order
        :type order: int
        """

        def element(key):
            return key[1]

        toSort = [(obj, self.data(rowDataSource, i)) for i, obj in enumerate(rowDataSource.userObjects())]

        if order == QtCore.Qt.DescendingOrder:
            results = [i[0] for i in sorted(toSort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(toSort, key=element)]
        rowDataSource.setUserObjects(results)

    def setData(self, rowDataSource, index, value):
        """Sets the text value of this node at the specified column.
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: The column index
        :type index: int
        :return: the new text value for this nodes column index
        :rtype: str
        """
        pass

    def data(self, rowDataSource, index):
        """The text for this node or column. index parameter with a value of 0 is
        the first column.
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: The column index for the text
        :type index: int
        :return: the column text
        :rtype: str
        """
        return ""

    def toolTip(self, rowDataSource, index):
        """The tooltip for this node
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :rtype: str
        """
        return ""

    def icon(self, rowDataSource, index):
        """The icon for this node
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :rtype: QtGui.QIcon
        """
        pass

    def isCheckable(self, rowDataSource, index):
        """The icon for this node
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :rtype: QtGui.QIcon
        """
        return False

    def isEditable(self, rowDataSource, index):
        """Determines if this node can be editable e.g set text. Defaults to False
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node is editable, defaults to False
        :rtype: bool
        """
        return rowDataSource.isEditable(index)

    def isEnabled(self, rowDataSource, index):
        """Determines if this node is enabled
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node is enabled, defaults to True
        :rtype: bool
        """
        return rowDataSource.isEnabled(index)

    def supportsDrag(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node supports drag
        :rtype: bool
        """
        return False

    def supportsDrop(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node supports drop
        :rtype: bool
        """
        return False

    def mimeData(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: The mime data for drag drop features
        :rtype: QtCore.QMimeData
        """
        return QtCore.QMimeData()

    def dropMimeData(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return False

    def mimeText(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return

    def isSelectable(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return True

    def foregroundColor(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return rowDataSource.foregroundColor(index)

    def backgroundColor(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return rowDataSource.backgroundColor(index)

    def displayChangedColor(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return None

    def alignment(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return QtCore.Qt.AlignVCenter

    def font(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return super(ColumnDataSource, self).font(index)


class RowDoubleDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.NumericDoubleDelegate(parent)

    def minimum(self, index):
        return -99999.0

    def maximum(self, index):
        return 99999.0


class RowIntNumericDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.NumericIntDelegate(parent)

    def minimum(self, index):
        return -99999

    def maximum(self, index):
        return 99999


class RowEnumerationDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.EnumerationDelegate(parent)

    def enums(self, index):
        return []


class IconRowDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.PixmapDelegate(parent)

    def isEditable(self, rowDataSource, index):
        return False


class RowBooleanDataSource(ColumnDataSource):
    def isCheckable(self, rowDataSource, index):
        return False


class ColumnDoubleDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.NumericDoubleDelegate(parent)

    def minimum(self, rowDataSource, index):
        return -99999.0

    def maximum(self, rowDataSource, index):
        return 99999.0


class ColumnIntNumericDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.NumericIntDelegate(parent)

    def minimum(self, rowDataSource, index):
        return -99999

    def maximum(self, rowDataSource, index):
        return 99999


class ColumnEnumerationDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.EnumerationDelegate(parent)

    def enums(self, rowDataSource, index):
        return []


class ColumnBooleanDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.CheckBoxDelegate(parent)

    def isCheckable(self, rowDataSource, index):
        return True


class IconColumnDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.PixmapDelegate(parent)

    def isEditable(self, rowDataSource, index):
        return False
