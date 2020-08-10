from Qt import QtWidgets, QtCore

from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants, utils

from zoo.libs.pyqt.widgets import elements, layouts
from zoo.libs.pyqt.widgets import frame
from zoo.libs.pyqt.widgets import extendedbutton, dpiscaling
from zoo.preferences.core import preference

THEME_PREFS = preference.interface("core_interface")


class StackWidget(QtWidgets.QWidget):
    """The overall layout widget. The table underneath (self.stackTableWgt) holds all the stack items.

    StackWidget is the overall view, StackTableWidget is the actual widget that holds the StackItems themselves.
    """
    _expandIcon = iconlib.icon("roundedsquare")
    _collapseIcon = iconlib.icon("minus")

    def __init__(self, label="", parent=None, showToolbar=True, showArrows=True, showClose=True, titleEditable=True):
        super(StackWidget, self).__init__(parent=parent)

        self.stackTableWgt = StackTableWidget(showArrows=showArrows, showClose=showClose, parent=self)
        self.stackItems = self.stackTableWgt.stackItems
        self.stackSearchEdit = QtWidgets.QLineEdit(parent=self)
        self.collapseBtn = QtWidgets.QPushButton(parent=self)
        self.expandBtn = QtWidgets.QPushButton(parent=self)

        self.text = label
        self.showToolbar = showToolbar
        self.showArrows = showArrows
        self.showClose = showClose
        self.titleEditable = titleEditable

        self.initUi()

        self.connections()

    def __len__(self):
        return len(self.stackItems)

    def __iter__(self):
        for i in self.stackItems:
            yield i

    def initUi(self):

        compStackToolbarLayout = QtWidgets.QHBoxLayout()
        compStackToolbarLayout.addWidget(self.stackSearchEdit)

        # Toolbar buttons
        self.expandBtn.setIcon(self._expandIcon)
        self.expandBtn.setIconSize(QtCore.QSize(12, 12))

        self.collapseBtn.setIcon(self._collapseIcon)
        self.collapseBtn.setIconSize(QtCore.QSize(10, 10))

        size = QtCore.QSize(self.collapseBtn.sizeHint().width(), 20)  # Temporary size till we get icons here
        self.collapseBtn.setFixedSize(size)
        self.expandBtn.setFixedSize(size)

        # Add buttons and search to toolbar
        compStackToolbarLayout.addSpacing(1)
        compStackToolbarLayout.addWidget(self.collapseBtn)
        compStackToolbarLayout.addWidget(self.expandBtn)

        compStackToolbarLayout.setStretchFactor(self.stackSearchEdit, 1)

        compStackToolbarLayout.setContentsMargins(0, 0, 0, 0)
        compStackToolbarLayout.setSpacing(1)

        compStackToolbar = QtWidgets.QWidget(parent=self)
        compStackToolbar.setLayout(compStackToolbarLayout)

        mainLayout = QtWidgets.QVBoxLayout()

        if self.text != "":
            mainLayout.addWidget(QtWidgets.QLabel(self.text))

        if not self.showToolbar:
            compStackToolbar.hide()

        mainLayout.addWidget(compStackToolbar)
        mainLayout.addWidget(self.stackTableWgt)

        self.setLayout(mainLayout)

    def connections(self):
        """
        Connections for the buttons and the search edit
        :return:
        """
        self.stackSearchEdit.textChanged.connect(self.onStackSearchChanged)
        self.collapseBtn.clicked.connect(self.collapseClicked)
        self.expandBtn.clicked.connect(self.expandClicked)

    def collapseClicked(self):
        """Collapse all the StackItems in the Table
        """
        self.stackTableWgt.collapseAll()

    def expandClicked(self):
        """Expand all the StackItems in the Table
        """
        self.stackTableWgt.expandAll()

    def onStackSearchChanged(self):
        """Filter the results based on the text inputted into the search bar
        """

        text = self.stackSearchEdit.text().lower()
        self.stackTableWgt.filter(text)
        self.stackTableWgt.updateSize()

    def clearStack(self):
        """Clear all the items in the stack
        """
        self.stackTableWgt.clearStack()

    def addStackItem(self, item):
        """Add item to the StackTableWidget

        :param item: StackItem to add to the table
        """
        item.setArrowsVisible(self.showArrows)
        self.stackTableWgt.addStackItem(item)

    def replaceStackItems(self, items):
        """Clear all items and replace it with the items

        :param items: List of items to add to the stack table
        """
        self.clearStack()
        for i in items:
            self.stackTableWgt.addStackItem(i)

    def clearSearchEdit(self):
        """Clear the search bar
        """
        self.stackSearchEdit.setText("")

    def shiftItem(self, wgt, dir):
        """Shift the item up or down in the table

        :param wgt: The StackItem to shift
        :param dir: The direction to shift -1 is upwards, 1 is downwards
        """
        self.stackTableWgt.shiftTableItem(wgt, dir)

    def deleteItem(self, wgt):
        """Delete the stack item from the table

        :param wgt:
        """
        self.stackTableWgt.deleteTableItem(wgt)


class StackHiderWidget(frame.QFrame):
    """
    Css Reasons
    """
    pass


class StackTableWidget(QtWidgets.QTableWidget):
    """The Table with the actual stack and items. Maybe should merge with StackWidget
    """

    def __init__(self, showArrows=True, showClose=True, parent=None, itemTint=tuple([60, 60, 60])):
        super(StackTableWidget, self).__init__(parent)
        self.cellPadding = 5
        self.stackItems = []
        self.showArrows = showArrows
        self.showClose = showClose
        self.itemTint = itemTint
        style = """
            QTableView {{
            background-color: rgb{0};
            border-size: 0px;
            }}

            QTableView:item {{
            padding:{1}px;
            border-size: 0px;
            }}
            """.format(str(uiconstants.MAYABGCOLOR), self.cellPadding)
        self.setShowGrid(False)
        self.initUi()

        self.setStyleSheet(style)

    def initUi(self):
        self.setRowCount(0)
        self.setColumnCount(1)

        self.verticalHeader().hide()
        self.horizontalHeader().hide()

        self.horizontalHeader().setStretchLastSection(True)

        self.setContentsMargins(1, 1, 1, 1)
        self.setSpacing(1)

        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def shiftTableItem(self, wgt, dir):
        # Update componentList
        # self.shiftComponentStack(wgt, dir)
        row = self.getRow(wgt)
        if row == 0 and dir == -1 or row == self.rowCount() - 1 and dir == 1:
            return

        # newRow = row + dir
        # Have to do this in a funky way because removeRow deletes the object
        # and swapping cells gives weird results
        if dir > 0:  # Even then this is ugly lol, need to fix
            newRow = row + dir + 1
            remRow = row
        else:
            newRow = row + dir
            remRow = row + 1

        self.insertRow(newRow)
        self.setCellWidget(newRow, 0, wgt)
        self.removeRow(remRow)
        self.updateSize(wgt)

    def collapseAll(self):
        for c in self.stackItems:
            c.collapse()

    def expandAll(self):
        for c in self.stackItems:
            c.expand()

    def deleteTableItem(self, wgt):

        row = self.getRow(wgt)
        self.removeRow(row)
        self.stackItems.remove(wgt)

        wgt.deleteLater()

    def addStackItem(self, item):
        self.stackItems.append(item)
        self.addRow(item)

        self.updateSize(item)

    def addRow(self, stackItem):
        rowPos = self.rowCount()
        self.setRowCount(rowPos + 1)
        self.setItem(rowPos, 0, QtWidgets.QTableWidgetItem())
        self.setCellWidget(rowPos, 0, stackItem)

    def getRow(self, stackItem):
        for i in range(self.rowCount()):
            if stackItem == self.cellWidget(i, 0):
                return i

    def filter(self, text):
        for i in range(self.rowCount()):
            found = not (text in self.cellWidget(i, 0).getTitle().lower())
            self.setRowHidden(i, found)

    def getStackItems(self):
        return self.stackItems

    def updateSize(self, widget=None):
        """Updates the size based on the widget who sent the request.
        Can be forced by setting the widget parameter

        :param widget: None or :class:`QtWidgets.QWidget`
        """

        if widget is not None:
            stackItem = widget
        else:
            stackItem = self.sender()

            if stackItem is None:
                return

        # So ugly =( This is is so the sizeHint refreshes properly otherwise the StackItem will be stuck at zero height
        QtWidgets.QApplication.processEvents()  # this must be here otherwise the resize is calculated too quickly

        newHeight = stackItem.sizeHint().height() + self.cellPadding * 2

        self.setRowHeight(self.getRow(stackItem), newHeight)

    def clearStack(self):
        self.stackItems = []
        self.clear()
        self.setRowCount(0)

    def sceneRefresh(self):
        self.clearStack()


class StackItem(QtWidgets.QFrame):

    minimized = QtCore.Signal()
    maximized = QtCore.Signal()
    toggleExpandRequested = QtCore.Signal(bool)
    shiftUpPressed = QtCore.Signal()
    shiftDownPressed = QtCore.Signal()
    deletePressed = QtCore.Signal()
    updateRequested = QtCore.Signal()

    def __init__(self, title, parent, collapsed=False, collapsable=True, icon=None, startHidden=False,
                 shiftArrowsEnabled=True, deleteButtonEnabled=True, titleEditable=True, itemIconSize=12,
                 titleFrame=None):
        """ The item in each StackTableWidget.

        :param title:
        :param parent:
        :param collapsed:
        :param collapsable:
        :param icon:
        :param startHidden:
        :param shiftArrowsEnabled:
        :param deleteButtonEnabled:
        :param titleEditable:
        :type titleFrame: StackTitleFrame
        """


        super(StackItem, self).__init__(parent)

        if startHidden:
            self.hide()

        self.stackWidget = parent
        self.hide()
        self.itemIconSize = itemIconSize

        # Init
        brdrWidth = utils.dpiScaleDivide(THEME_PREFS.STACK_BORDER_WIDTH)  # border thickness of the hovered toolset
        self.layout = layouts.vBoxLayout(parent=self, margins=(brdrWidth, brdrWidth, brdrWidth, brdrWidth),
                                                               spacing=0)
        self.title = title
        self.color = uiconstants.DARKBGCOLOR
        self.contentMargins = (0, 0, 0, 0)
        self.contentSpacing = 0
        self.collapsable = collapsable
        self.collapsed = collapsed

        self.titleFrame = titleFrame or StackTitleFrame(parent=self, title=title,
                                                        icon=icon,
                                                        titleEditable=titleEditable,
                                                        itemIconSize=itemIconSize, collapsed=collapsed,
                                                        shiftArrowsEnabled=shiftArrowsEnabled,
                                                        deleteButtonEnabled=deleteButtonEnabled)

        self._init()

        self.initUi()
        self.connections()

        if not collapsable:  # if not collapsable must be open
            self.collapsed = False
            self.expand()

        if self.collapsed:
            self.collapse()
        else:
            self.expand()

    def _init(self):
        """ For initializing of variables

        :return:
        """
        self.widgetHider = StackHiderWidget(parent=self)
        self._contentsLayout = layouts.vBoxLayout(self.widgetHider, spacing=0)

    def setArrowsVisible(self, visible):
        """Set the shift arrows to be visible or not. These arrows allow the StackItem to be shifted upwards or downwards.

        :param visible: bool
        """
        if visible:
            self.shiftDownBtn.show()
            self.shiftUpBtn.show()
        else:
            self.shiftDownBtn.hide()
            self.shiftUpBtn.hide()

    @property
    def contentsLayout(self):
        return self._contentsLayout

    def titleTextWidget(self):
        return self.titleFrame.lineEdit

    def showExpandIndicator(self, vis):
        self.titleFrame.expandToggleButton.setVisible(vis)

    def setTitleTextMouseTransparent(self, trans):
        self.titleFrame.lineEdit.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, trans)

    def initUi(self):
        self.buildHiderWidget()

        self.layout.addWidget(self.titleFrame)
        self.layout.addWidget(self.widgetHider)
        self.layout.setSpacing(0)

    def setItemIconColor(self, col):
        self.titleFrame.setItemIconColor(col)

    def setItemIcon(self, name):
        self.titleFrame.setItemIcon(name)

    def shiftUp(self):
        self.shiftUpPressed.emit()

    def shiftDown(self):
        self.shiftDownPressed.emit()

    def addWidget(self, widget):
        self._contentsLayout.addWidget(widget)

    def addLayout(self, layout):
        self._contentsLayout.addLayout(layout)

    def buildHiderWidget(self):
        """Builds widget that is collapsable
        Widget can be toggled so it's a container for the layout
        """
        self.widgetHider.setContentsMargins(0, 0, 0, 0)
        self._contentsLayout.setContentsMargins(*self.contentMargins)
        self._contentsLayout.setSpacing(self.contentSpacing)
        self.widgetHider.setHidden(self.collapsed)
        self.widgetHider.setObjectName("stackbody")

    def onCollapsed(self, emit=True):
        """Collapse and hide the item contents
        """
        self.widgetHider.setHidden(True)
        self.titleFrame.collapse()

        if emit:
            self.minimized.emit()
        self.collapsed = 1

    def onExpand(self, emit=True):
        """ Expand the contents and show all the widget data
        """
        self.widgetHider.setHidden(False)
        self.titleFrame.expand()

        if emit:
            self.maximized.emit()
        self.collapsed = 0

    def expand(self, emit=True):
        """ Extra Code for convenience """
        self.onExpand(emit)

    def collapse(self, emit=True):
        """ Extra Code for convenience """
        self.onCollapsed(emit)

    def toggleContents(self, emit=True):
        """Shows and hides the widget `self.widgetHider` this contains the layout `self.hiderLayout`
        which will hold the custom contents that the user specifies
        """

        if not self.collapsable:
            return
        self.toggleExpandRequested.emit(not self.collapsed)
        # If we're already collapsed then expand the layout
        if self.collapsed:
            self.expand(emit)
            self.updateSize()
            return not self.collapsed

        self.collapse(emit)
        self.updateSize()
        return self.collapsed

    def setComboToText(self, combobox, text):
        """Find the text in the combobox and sets it to active.

        :param combobox:
        :param text:
        :type text: str
        """
        index = combobox.findText(text, QtCore.Qt.MatchFixedString)
        combobox.setCurrentIndex(index)

    def updateSize(self):
        """Update the size of the widget. Usually called by collapse or expand for when the widget contents are hidden
        or shown.
        """
        self.updateRequested.emit()

    def getTitle(self):
        """Get method for the title text
        """
        return self.titleFrame.lineEdit.text()

    def setTitle(self, text):
        """Set method to get the title text

        :param text:
        """
        self.titleFrame.lineEdit.setText(text)

    def parentComboActivated(self):
        parentText = self.parentComboBox.currentText()

        parentComponent = None
        for c in self.core.components():
            if c.name() == parentText:
                parentComponent = c
                break

        if parentComponent is None:
            componentLayer = self.core.currentRig.getOrCreateComponentLayer()
            self.component.setParent(componentLayer)
            return

        self.component.setParent(parentComponent)

    def setFrameColor(self, color):
        style = """
            """.format(str(color))

        self.titleFrame.setStyleSheet(style)

    def connections(self):
        self.titleFrame.expandToggleButton.leftClicked.connect(self.toggleContents)
        self.titleFrame.shiftUpPressed.connect(self.shiftUpPressed.emit)
        self.titleFrame.shiftDownPressed.connect(self.shiftDownPressed.emit)
        self.titleFrame.maximized.connect(self.maximized.emit)
        self.titleFrame.minimized.connect(self.minimized.emit)
        self.titleFrame.updateRequested.connect(self.updateRequested.emit)
        self.titleFrame.toggleExpandRequested.connect(self.toggleExpandRequested.emit)
        self.titleFrame.deletePressed.connect(self.deletePressed.emit)


class StackTitleFrame(frame.QFrame, dpiscaling.DPIScaling):

    _itemIcon = "stream"

    _deleteIconName = "xMark"
    _collapsedIconName = "sortClosed"
    _expandIconName = "sortDown"
    _downIconName = "arrowSingleDown"
    _upIconName = "arrowSingleUp"

    minimized = QtCore.Signal()
    maximized = QtCore.Signal()
    toggleExpandRequested = QtCore.Signal(bool)
    shiftUpPressed = QtCore.Signal()
    shiftDownPressed = QtCore.Signal()
    deletePressed = QtCore.Signal()
    updateRequested = QtCore.Signal()

    def __init__(self, parent=None, title="", titleEditable=False, icon=None, itemIconSize=16, collapsed=True,
                 shiftArrowsEnabled=True, deleteButtonEnabled=True):
        """ Stack Item Title Frame

        :param parent:
        :param title:
        :param titleEditable:
        """

        self.spacesToUnderscore = True

        self.collapsed = collapsed

        self.itemIconSize = itemIconSize
        self._itemIcon = icon or self._itemIcon

        self.extrasLayout = layouts.hBoxLayout(margins=(0, 0, 0, 0), spacing=0)  # elements.hBoxLayout() breaks
        self.horizontalLayout = layouts.hBoxLayout(spacing=0)

        self.lineEdit = LineClickEdit(title)
        self.horizontalLayout = None

        # so we can drag drop without the lineEdit interrupting
        self.lineEdit.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.titleEditable = titleEditable

        if not titleEditable:
            self.lineEdit.setReadOnly(True)

        super(StackTitleFrame, self).__init__(parent=parent)

        self.expandToggleButton = extendedbutton.ExtendedButton(parent=self)
        self.itemIcon = extendedbutton.ExtendedButton(parent=self)
        self.shiftDownBtn = extendedbutton.ExtendedButton(parent=self)
        self.shiftUpBtn = extendedbutton.ExtendedButton(parent=self)
        self.deleteBtn = extendedbutton.ExtendedButton(parent=self)

        if not shiftArrowsEnabled:
            self.shiftDownBtn.hide()
            self.shiftUpBtn.hide()

        if not deleteButtonEnabled:
            self.deleteBtn.hide()

        self.initUi()
        self.connections()

    def mouseDoubleClickEvent(self, event):
        event.pos()
        if self.titleEditable:
            self.lineEdit.editEvent(event)

    def shiftUp(self):
        self.shiftUpPressed.emit()

    def shiftDown(self):
        self.shiftDownPressed.emit()

    def initUi(self):

        """ Builds the title part of the layout with a QFrame widget
        """

        self.itemIcon.setIconByName(self._itemIcon, colors=None, size=self.itemIconSize)
        self.itemIcon.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

        self.extrasLayout.setContentsMargins(0, 0, 0, 0)
        self.extrasLayout.setSpacing(0)

        self.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))

        # the horizontal layout
        self.horizontalLayout = layouts.hBoxLayout(self, spacing=0)
        # the icon and title and spacer
        self.expandToggleButton.setParent(self)
        if self.collapsed:
            self.expandToggleButton.setIconByName(self._collapsedIconName)
        else:
            self.expandToggleButton.setIconByName(self._expandIconName)

        iconSize = 12
        highlightOffset = 40

        self.deleteBtn.setIconByName(self._deleteIconName, colors=None, size=iconSize, colorOffset=highlightOffset)
        self.shiftUpBtn.setIconByName(self._upIconName, colors=None, size=iconSize, colorOffset=highlightOffset)
        self.shiftDownBtn.setIconByName(self._downIconName, colors=None, size=iconSize, colorOffset=highlightOffset)
        self.expandToggleButton.setIconByName(self._expandIconName, colors=(192, 192, 192), size=iconSize)

        spacerItem = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        # add to horizontal layout
        self.horizontalLayout.addWidget(self.expandToggleButton)
        self.horizontalLayout.addWidget(self.itemIcon)
        self.horizontalLayout.addItem(spacerItem)
        self.setFixedHeight(self.sizeHint().height())
        self.setObjectName("title")

        self.setMinimumSize(self.sizeHint().width(), self.sizeHint().height() + 1)

        self.horizontalLayout.addWidget(self.lineEdit)
        self.horizontalLayout.addLayout(self.extrasLayout)
        self.horizontalLayout.addWidget(self.shiftUpBtn)
        self.horizontalLayout.addWidget(self.shiftDownBtn)
        self.horizontalLayout.addWidget(self.deleteBtn)

        self.horizontalLayout.setStretchFactor(self.lineEdit, 4)

    def collapse(self):
        self.expandToggleButton.setIconByName(self._collapsedIconName)

    def expand(self):
        self.expandToggleButton.setIconByName(self._expandIconName)

    def connections(self):
        """ Connections for stack items"""

        self.shiftUpBtn.leftClicked.connect(self.shiftUp)
        self.shiftDownBtn.leftClicked.connect(self.shiftDown)
        self.deleteBtn.leftClicked.connect(self.deletePressed.emit)

        self.lineEdit.textChanged.connect(self.titleValidate)
        self.lineEdit.selectionChanged.connect(self.selectCheck)

    def selectCheck(self):
        """ Stops any selection from happening if title is not editable

        :return:
        :rtype:
        """
        if not self.titleEditable:
            self.lineEdit.deselect()

    def titleValidate(self):
        """Removes invalid characters and replaces spaces with underscores
        """
        if self.spacesToUnderscore:
            nameWgt = self.lineEdit
            text = self.lineEdit.text()
            pos = nameWgt.cursorPosition()

            text = text.replace(" ", "_")
            nameWgt.blockSignals(True)
            nameWgt.setText(text)
            nameWgt.blockSignals(False)

            # set cursor back to original position
            nameWgt.setCursorPosition(pos)

    def setItemIconColor(self, col):
        self.itemIcon.setIconColor(col)

    def setItemIcon(self, name):
        self.itemIcon.setIconByName(name)


class LineClickEdit(QtWidgets.QLineEdit):

    def __init__(self, text, single=False, double=True, passThroughClicks=True):
        """ Creates a line edit that becomes editable on click or doubleclick

        :param text:
        :param single:
        :param double:
        :param passThroughClicks:
        """

        super(LineClickEdit, self).__init__(text)
        self.setReadOnly(True)
        self.editingFinished.connect(self.editFinished)
        self.editingStyle = self.styleSheet()
        self.defaultStyle = "QLineEdit {border: 0}"
        self.setStyleSheet(self.defaultStyle)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

        if single:
            self.mousePressEvent = self.editEvent
        else:
            if passThroughClicks:
                self.mousePressEvent = self.mouseClickPassThrough

        if double:
            self.mouseDoubleClickEvent = self.editEvent
        else:
            if passThroughClicks:
                self.mousePressEvent = self.mouseClickPassThrough

    def editFinished(self):
        self.setReadOnly(True)
        self.setStyleSheet(self.defaultStyle)
        self.deselect()

    def editEvent(self, event):
        self.setStyleSheet(self.editingStyle)
        self.selectAll()
        self.setReadOnly(False)
        self.setFocus()

        event.accept()

    def focusOutEvent(self, e):
        super(LineClickEdit, self).focusOutEvent(e)  # required to remove cursor on focusOut
        self.editFinished()

    def mouseClickPassThrough(self, event):
        # Pass through the click
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()


