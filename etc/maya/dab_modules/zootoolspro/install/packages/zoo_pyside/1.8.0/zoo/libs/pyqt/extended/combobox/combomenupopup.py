from Qt import QtCore, QtWidgets, QtGui

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dialog, layouts

from zoo.preferences.core import preference

SEPARATOR_STR = "---=---"
SEPARATOR_HEIGHT = 8


class ComboStandardItem(QtGui.QStandardItem):

    def __init__(self, *args, **kwargs):
        """ Our own custom standard item as it crashes maya 2019 if setData with dag nodes are used

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        """
        self._parent = kwargs['parent']
        super(ComboStandardItem, self).__init__(*args, **kwargs)

    def setData(self, value, role=QtCore.Qt.UserRole + 1):
        """ Use our own set data as using Qt's ones crashes Maya 2019

        :param value:
        :type value:
        :param role:
        :type role:
        :return:
        :rtype:
        """

        newDict = self._parent.property("data")

        if newDict is None:
            newDict = {}
        newDict.update({id(self): value})

        self._parent.setProperty("data", newDict)

    def itemData(self):
        """ Use this one as .data() crashes maya on 2019

        :return:
        :rtype:
        """
        return self._parent.property("data").get(id(self), None)


class ComboCustomEvent(object):
    index = None
    row = None
    items = None
    source = None

    def __init__(self, index, row, items, sourceMenu):
        """ Combo custom event that has everything related to the selected item

        :param index:
        :type index: QtCore.QModelIndex
        :param row:
        :type row: int
        :param items: The items from all the columns of this row
        :type items: list[ComboStandardItem]
        :param sourceMenu: The source menu
        :type sourceMenu: QtWidgets.QWidget

        """

        self.index = index
        self.row = row
        self.items = items
        self.rowText = items[0].text() if len(items) > 0 else ""
        self.source = sourceMenu


class ComboDelegate(QtWidgets.QStyledItemDelegate):
    """ Combo Delegate so we can draw out the separator

    """

    def paint(self, painter, option, index):
        """ Paint out normal text or a separator

        :param painter:
        :type painter: QtGui.QPainter
        :param option:
        :type option: QtWidgets.QStyleOptionViewItem
        :param index:
        :type index: QtCore.QModelIndex
        :return:
        :rtype:
        """
        if index.data() == SEPARATOR_STR:
            painter.setPen(QtCore.Qt.darkGray)
            y = option.rect.center().y()
            painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        else:
            super(ComboDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        if index.data() == SEPARATOR_STR:
            return QtCore.QSize(0, utils.dpiScale(SEPARATOR_HEIGHT))
        else:
            return super(ComboDelegate, self).sizeHint(option, index)


class ComboCustomListView(QtWidgets.QListView):
    def __init__(self, *args, **kwargs):
        """ The list view for the menu popup

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        """
        super(ComboCustomListView, self).__init__(*args, **kwargs)
        self.setItemDelegate(ComboDelegate())
        self.setProperty("data", {})

    def filter(self, text):
        """ Hide anything that that doesnt have text. Used for searches.

        :param text:
        :type text: basestring
        """
        text = text.lower()
        for r in range(self.model().rowCount()):
            if text not in self.model().item(r, 0).text().lower():
                self.setRowHidden(r, True)
            else:
                self.setRowHidden(r, False)

    def clearFilter(self):
        """ Clear the search filter

        :return:
        :rtype:
        """
        for r in range(self.model().rowCount()):
            self.setRowHidden(r, False)

    def firstVisibleIndex(self):
        """ Get the first visible index

        :return:
        :rtype:
        """
        for r in range(self.model().rowCount()):
            if not self.isRowHidden(r):
                return self.model().index(r, 0)

    def nextIndex(self, mustBeVisible=True):
        """ Get the next index from the current index

        :param mustBeVisible: Only returns if the next index is visible
        :type mustBeVisible:
        :return:
        :rtype:
        """
        index = self.currentIndex()
        row = index.row() + 1

        while (mustBeVisible and self.isRowHidden(row) and row < self.model().rowCount()) or \
                index.sibling(row, 0).data() == SEPARATOR_STR:
            row += 1

        return index.sibling(row, 0)

    def prevIndex(self, mustBeVisible=True):
        """ Get the previous index relative from the current index

        :param mustBeVisible: Only returns if the next index is visible
        :type mustBeVisible:
        :return:
        :rtype:
        """

        index = self.currentIndex()
        row = index.row() - 1

        while (mustBeVisible and self.isRowHidden(row) and row > 0) or \
                index.sibling(row, 0).data() == SEPARATOR_STR:
            row -= 1

        return index.sibling(row, 0)

    def parentWidget(self):
        """ Parent Widget

        :return:
        :rtype: ComboMenuPopup
        """
        return super(ComboCustomListView, self).parentWidget()

    def addItem(self, text, data=None):
        """ Add standard item with text and data

        :param text:
        :type text:
        :param data:
        :type data:
        :return: ComboStandardItem
        :rtype:
        """

        if type(text) != list:
            text = [text]

        if data is not None and type(data) != list and type(data) != tuple:
            data = [data]

        if data is None:
            data = text

        items = []
        for i, d in enumerate(data):
            if self.parentWidget().comboRounding is not None and type(text[0]) is float:
                formatText = "{:.#f}".replace("#", str(self.parentWidget().comboRounding))
                item = ComboStandardItem(formatText.format(round(text[0], self.parentWidget().comboRounding)), parent=self)
            else:
                item = ComboStandardItem(str(text[0]), parent=self)

            if d is None:
                newData = text  # If no data is found use text as data
            else:
                newData = d

            item.setData(newData)
            items.append(item)

        self.model().appendRow(items)
        return items

    def data(self, item):
        """

        :param item:
        :type item: ComboStandardItem
        :return:
        :rtype:
        """
        return item.itemData()

    def addSeparator(self):
        """ Add a separator to the list view

        :return:
        :rtype:
        """
        item = ComboStandardItem(SEPARATOR_STR, parent=self)

        self.model().appendRow(item)

    def visibleRowCount(self):
        """ Number of rows that are visible

        :return:
        :rtype: int
        """
        return sum([not self.isRowHidden(i) for i in range(self.model().rowCount())])


class ComboMenuPopup(dialog.Dialog):
    itemClicked = QtCore.Signal(ComboCustomEvent)
    indexChanged = QtCore.Signal(ComboCustomEvent)
    comboRounding = -1

    def __init__(self, parent=None, maxHeight=300, showOnInitialize=False, comboEdit=None, rounding=None):
        """ The popup dialog for the custom combo menu

        :param parent:
        :type parent:
        :param showOnInitialize:
        :type showOnInitialize:
        :type comboEdit: zoo.libs.pyqt.extended.combobox.comboeditwidget.ComboEditWidget
        """

        super(ComboMenuPopup, self).__init__("Title", parent=parent, showOnInitialize=showOnInitialize)

        themePref = preference.interface("core_interface")
        self.sourceButton = None

        self.setStyleSheet(str(themePref.stylesheet().data))
        self.mainLayout = layouts.vBoxLayout(self, margins=(0, 0, 0, 0), spacing=0)

        self.searchEdit = QtWidgets.QLineEdit(self)
        self.listView = ComboCustomListView(self)
        self._currentItem = None
        self.comboEdit = comboEdit
        self._maxHeight = maxHeight
        self._savedRow = -1  # Empty index
        self.comboRounding = rounding

        self._model = QtGui.QStandardItemModel()
        self.defaultWindowFlags = self.windowFlags()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.buttons = []
        self.initUi()
        self.connections()

    def initUi(self):
        """ Initialize Ui

        :return:
        :rtype:
        """
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)
        self.buttons = []

        self.initSearchEdit()

        # Main Layout settings
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.searchEdit)
        self.mainLayout.addWidget(self.listView)
        self.listView.setModel(self._model)
        self.listView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.listView.clicked.connect(self.listViewItemClicked)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

    def connections(self):
        """ Get the connections

        :return:
        :rtype:
        """
        self.searchEdit.textEdited.connect(self.searchEditChanged)
        self.searchEdit.returnPressed.connect(self.searchReturnedPressed)

    def searchEditChanged(self, text):
        """ The search edit value changed

        :param text:
        :type text:
        :return:
        :rtype:
        """
        self.listView.filter(text)
        self.resizeUpdate()

    def keyPressEvent(self, event):
        """ For key up and key down events

        :param event:
        :type event:
        :return:
        :rtype:
        """
        if event.key() == QtCore.Qt.Key_Up:
            self.scrollPrev()
        elif event.key() == QtCore.Qt.Key_Down:
            self.scrollNext()
        event.accept()

    def scrollPrev(self):
        """ Scroll to previous index item

        :return:
        :rtype:
        """
        newIndex = self.listView.prevIndex()
        if newIndex.isValid():
            self.setCurrentIndex(newIndex)

    def scrollNext(self):
        """ Scroll to next index item

        :return:
        :rtype:
        """

        newIndex = self.listView.nextIndex()
        if newIndex.isValid():
            self.setCurrentIndex(newIndex)

    def itemFromRow(self, row):
        """ Get item from row

        :param row:
        :type row:
        :return:
        :rtype:
        """
        return self.model().item(row)

    def currentIndex(self):
        """ Get current index

        :return:
        :rtype: QtCore.QModelIndex
        """
        return self.listView.currentIndex()

    def searchReturnedPressed(self):
        """

        :return:
        :rtype:
        """
        if len(self.listView.selectedIndexes()) == 0:
            sel = self.listView.firstVisibleIndex()
        else:
            sel = self.listView.selectedIndexes()[0]

        self.setCurrentIndex(sel)
        self.close()

    def currentItem(self):
        """ Get the current item

        :return:
        :rtype: ComboStandardItem
        """
        return self.model().itemFromIndex(self.listView.currentIndex())

    def addItem(self, text, data=None):
        """ Add item

        :param text:
        :type text:
        :param data:
        :type data:
        :return:
        :rtype:
        """
        item = self.listView.addItem(text, data)

        if self._currentItem is None:
            self._currentItem = item

        #
        self._savedRow = self.currentIndex()

    def addSeparator(self):
        """ Add a separator

        :return:
        :rtype:
        """
        self.listView.addSeparator()

    def model(self):
        """ Return the model

        :return:
        :rtype: QtGui.QStandardItemModel
        """

        return self._model

    def listViewItemClicked(self, index):
        """ For when the list view item is clicked

        :param index:
        :type index: QtCore.QModelIndex
        :return:
        :rtype:
        """

        self.setCurrentIndex(index)
        self.close()

        event = self.eventFromIndex(index)

        if index.isValid():
            self.itemClicked.emit(event)

    def eventFromIndex(self, index):
        """ Get a ComboCustomEvent from index

        :param index:
        :type index: QtCore.QModelIndex
        :return:
        :rtype: ComboCustomEvent
        """
        items = self.rowItems(index)

        return ComboCustomEvent(index=index, row=index.row(), items=items,
                                sourceMenu=self.sourceButton)

    def rowItems(self, index):
        """ Gets all the items in the row (From the columns)

        :param index:
        :type index: QtCore.QModelIndex
        :return:
        :rtype: list[ComboStandardItem]
        """

        items = []
        iterIndex = index

        # Add all the items from the columns
        while iterIndex.isValid():
            items.append(self.listView.model().itemFromIndex(iterIndex))
            iterIndex = iterIndex.sibling(iterIndex.row(), iterIndex.column() + 1)

        return items

    def setCurrentIndex(self, index):
        """ Set the current index of the combo menu

        :param index:
        :type index: QtCore.QModelIndex
        :return:
        :rtype:
        """

        if self._savedRow == index.row():
            return  # dont do anything if the index is the same
        self.listView.setCurrentIndex(index)
        self._currentItem = self._model.itemFromIndex(index)
        event = self.eventFromIndex(index)
        if event.index.isValid():
            self.indexChanged.emit(event)

        self._savedRow = index.row()

        # There's a QT bug where if index is zero it doesn't update properly.
        if index.row() == 0:
            [c.update() for c in self.comboEdit.comboEdits]

    def sizeHint(self):
        """ Change the size hint to resize based on the buttons in the icon popup

        :return:
        """
        return super(ComboMenuPopup, self).sizeHint()

    def initSearchEdit(self):
        """ Search edit to filter out the button

        :return:
        """

        self.searchEdit.setPlaceholderText("Search...")
        self.searchEdit.textChanged.connect(self.updateSearch)

    def updateSearch(self, searchString):
        """ Filter buttons by search string

        :param searchString:
        :return:
        """
        searchString = searchString or ""
        for b in self.buttons:
            if searchString.lower() in b.name.lower() or searchString == "":
                b.show()
            else:
                b.hide()

    def show(self, sender):
        """ Clear out and set up on popup show

        :return:
        :rtype:
        """
        self.sourceButton = sender
        self.searchEdit.setText("")
        self.listView.clearFilter()
        super(ComboMenuPopup, self).show()
        self.searchEdit.setFocus()
        self.resizeUpdate()

    def resizeUpdate(self):
        """ Resize the popup based on the distance to bottom of monitor

        :return:
        :rtype:
        """
        botOffset = utils.dpiScale(10)
        comboPos = self.comboEdit.mapToGlobal(QtCore.QPoint(0, self.comboEdit.height()))

        heightToBottom = utils.currentScreenGeometry().height() - botOffset - comboPos.y()
        searchEditHeight = self.searchEdit.sizeHint().height()
        maxHeight = min(heightToBottom, self._maxHeight)
        itemHeight = max(self.listView.visibleRowCount(), 1) * self.listView.sizeHintForRow(0) + searchEditHeight
        height = min(maxHeight, itemHeight)
        self.setFixedHeight(height)
