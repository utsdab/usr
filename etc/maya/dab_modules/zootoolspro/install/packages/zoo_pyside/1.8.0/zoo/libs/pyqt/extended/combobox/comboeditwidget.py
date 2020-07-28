from Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils, uiconstants as uic
from zoo.libs.pyqt.extended.combobox import combomenupopup
from zoo.libs.pyqt.widgets import layouts, label as lbl, iconmenu, stringedit, buttons
import math


class ComboMainWidget(QtWidgets.QFrame):
    """ Main combo widget that holds the labels and drop down menu button

    """
    doubleClicked = QtCore.Signal(object)
    clicked = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super(ComboMainWidget, self).__init__(*args, **kwargs)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(event)

    def mousePressEvent(self, event):
        """ Mouse Press event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self.clicked.emit(event)


class ComboEditSub(object):
    clicked = QtCore.Signal(object)

    def updateZooStyle(self):
        """

        :return:
        :rtype:
        """
        from zoo.preferences.core import preference
        themePref = preference.interface("core_interface")
        self.setStyleSheet("color: rgb{}".format(themePref.MAIN_FOREGROUND_COLOR))

    def mousePressEvent(self, event):
        """ Mouse Press event

        :param event:
        :type event:
        :return:
        :rtype:
        """

        ret = super(ComboEditSub, self).mousePressEvent(event)
        self.clicked.emit(event)
        return ret


class ComboEdit(stringedit.StringEdit, ComboEditSub):
    def __init__(self, *args, **kwargs):
        super(ComboEdit, self).__init__(*args, **kwargs)
        self.updateZooStyle()


class ComboEditFloat(stringedit.FloatEdit, ComboEditSub):
    def __init__(self, *args, **kwargs):
        super(ComboEditFloat, self).__init__(*args, **kwargs)
        self.updateZooStyle()


class ComboEditInt(stringedit.IntEdit, ComboEditSub):
    def __init__(self, *args, **kwargs):
        super(ComboEditInt, self).__init__(*args, **kwargs)
        self.updateZooStyle()



class ComboEditWidget(QtWidgets.QWidget):
    """ Create our own combobox
    """
    itemChanged = QtCore.Signal(object)  # When the item is clicked
    itemRenamed = QtCore.Signal(object)  # When the item was renamed
    editingFinished = QtCore.Signal(object)  # When the editing is finished
    editModified = QtCore.Signal(object)  # Only when the edit has changed
    comboEditChanged = QtCore.Signal(object)  # For when the edit was changed. Pretty much inclusive of itemChanged and editModified
    aboutToShow = QtCore.Signal()  # Emits just before the menu is drawn after clicking the menu buttons

    Default = 0
    EditWidget = 1
    SearchWidget = 2
    SeparatorString = combomenupopup.SEPARATOR_STR

    def __init__(self, parent=None, label="", text=None, items=None, data=None, editCount=1, primaryIcon="sortDown",
                 secondaryIcon="sortDown",
                 primaryActive=True, secondaryActive=False, aspectRatioButton=False,
                 primaryTooltip="", secondaryTooltip="",
                 labelStretch=0, mainStretch=0, renamesItem=False, inputMode="float", comboRounding=None, toolTip=None):
        """ Initialize class

        :param label: the label of the combobox
        :type label: str
        :param items: the item list of the combobox
        :type items: list
        :param parent: the qt parent
        :type parent: class
        :param toolTip: the tooltip info to display with mouse hover
        :type toolTip: str
        :param setIndex: set the combo box value as an int - 0 is the first value, 1 is the second
        :type setIndex: int
        :param boxMinWidth: set the combo box to be a minimum width in pixels, dpi handled
        :type boxMinWidth: int
        """
        super(ComboEditWidget, self).__init__(parent=parent)
        self._enterPressed = False
        utils.setSkipChildren(self, True)
        self.itemRenamed.connect(self.itemRenamedEvent)
        self.mainLayout = layouts.hBoxLayout()
        if label:
            self.nameLabel = lbl.Label(parent=self, text=label)
            self.nameLabel.setToolTip(toolTip)
        else:
            self.nameLabel = None  # type: lbl.Label

        self.comboMainWidget = ComboMainWidget(parent=self)
        self.mainWidgetLayout = layouts.hBoxLayout(spacing=2)
        self.primaryButton = iconmenu.ExtendedButton(parent=self)
        self.primaryButton.setIconByName(primaryIcon)
        self.primaryButton.setIconSize(QtCore.QSize(16, 16))
        self.primaryButton.setToolTip(primaryTooltip)
        self.primaryButton.setProperty("menuButton", "Primary")
        self.secondaryButton = iconmenu.ExtendedButton(parent=self)
        self.secondaryButton.setIconByName(secondaryIcon)
        self.secondaryButton.setToolTip(secondaryTooltip)
        self.secondaryButton.setIconSize(QtCore.QSize(16, 16))
        self.secondaryButton.setProperty("menuButton", "Secondary")

        self._aspectLinkedActive = aspectRatioButton
        self.prevTexts = None

        if self._aspectLinkedActive:
            self.aspectLinkedBtn = buttons.styledButton(text="",
                                                        icon="linkConnected",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_TRANSPARENT_BG,
                                                        minWidth=uic.BTN_W_ICN_REG)
            self.aspectLinkedBtn.setProperty("linked", True)

        if toolTip is not None:
            self.setToolTip(toolTip)

        if not primaryActive:
            self.primaryButton.hide()

        if not secondaryActive:
            self.secondaryButton.hide()

        self.comboPopup = combomenupopup.ComboMenuPopup(comboEdit=self, rounding=comboRounding)

        self.comboEdits = []
        for i in range(editCount):

            if inputMode == "float":
                self.comboEdits.append(ComboEditFloat(parent=self))
            elif inputMode == "int":
                self.comboEdits.append(ComboEditInt(parent=self))
            else:
                self.comboEdits.append(ComboEdit(parent=self))

        self._inputMode = inputMode


        self.initUi(labelStretch, mainStretch)
        self.connections()
        self.addItems(items, data)
        self.renameMode = renamesItem

        if text is not None:
            self.setValue(text)

    def initUi(self, labelStretch, mainStretch):
        """ Init ui

        :param labelStretch:
        :type labelStretch:
        :param mainStretch:
        :type mainStretch:
        :return:
        :rtype:
        """

        for c in self.comboEdits:
            c.setProperty("clearFocus", True)
            c.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Maximum)

        self.comboMainWidget.setLayout(self.mainWidgetLayout)
        if self.nameLabel:
            self.mainLayout.addWidget(self.nameLabel, labelStretch)
        self.mainLayout.addWidget(self.comboMainWidget, mainStretch)
        editLayout = layouts.hBoxLayout()
        for c in self.comboEdits:
            editLayout.addWidget(c)

        if self._aspectLinkedActive:
            editLayout.insertWidget(1, self.aspectLinkedBtn)
            editLayout.setSpacing(0)

        self.mainWidgetLayout.addLayout(editLayout)
        self.mainWidgetLayout.addWidget(self.primaryButton)
        self.mainWidgetLayout.addWidget(self.secondaryButton)

        self.setLayout(self.mainLayout)

        self.activateWidget(ComboEditWidget.Default)

    def connections(self):
        """ Set up connections

        :return:
        :rtype:
        """
        self.primaryButton.leftClicked.connect(self.activatePopup)
        self.secondaryButton.leftClicked.connect(self.activatePopup)
        self.comboPopup.indexChanged.connect(self.indexChanged)
        self.comboMainWidget.clicked.connect(self.activateMainWidget)
        # self.comboEdit.clicked.connect(self.activateRenameWidget)
        if self._aspectLinkedActive:
            self.aspectLinkedBtn.leftClicked.connect(self.toggleAspectLinkBtn)

        for c in self.comboEdits:
            c.returnPressed.connect(self.comboEditReturnPressed)
            c.editingFinished.connect(self.editFinished)

    def aspectLinked(self, button=None):
        """ Returns True if aspect is linked, false otherwise

        :return:
        :rtype:
        """
        if self._aspectLinkedActive:
            button = button or self.aspectLinkedBtn
            return button.property("linked")

    def toggleAspectLinkBtn(self, updateAspect=False):
        """ Toggle Aspect Link button

        :return:
        :rtype:
        """
        newLinked = not self.aspectLinked()
        self.setAspectLinked(newLinked, self.sender(), updateAspect)

    def setAspectLinked(self, newLinked, button=None, updateAspect=False):
        """ Set aspect linked to True or False

        :param button:
        :type button:
        :param newLinked:
        :type newLinked:
        :param updateAspect:
        :type updateAspect:
        :return:
        :rtype:
        """
        if self._aspectLinkedActive:
            button = button or self.aspectLinkedBtn
        else:
            return

        button.setProperty("linked", newLinked)
        if newLinked:
            # todo: fix set iconbyname colours in styledbutton!
            button.setIconByName("linkConnected", colors=[(192, 192, 192)])
            if updateAspect:
                self.updateAspect()
        else:
            button.setIconByName("linkBroken", colors=[(192, 192, 192)])

    def updateAspect(self, sender=None):
        """ Update aspect ratio of scene

        :type sender: ComboEdit
        :return:
        :rtype:
        """

        sender = sender or None
        # default to use the resolution width as the major input
        if sender is None:
            sender = self.comboEdits[0]

        # If aspect locked update the opposing resolution
        if not self._aspectLinkedActive or not self.aspectLinked():
            #self.prevTexts = self.values()
            return

        # should probably handle more than 2 edits for aspect ratios
        senderIndex = self.comboEdits.index(sender)
        otherIndex = int(not senderIndex)
        other = self.comboEdits[otherIndex]

        value = str(int(
            math.ceil(float(sender.text()) * (float(self.prevTexts[otherIndex]) / float(self.prevTexts[senderIndex])))))

        # other.blockSignals(True)
        other.setValue(value)
        # other.blockSignals(False)
        #self.prevTexts = self.values()


    def addItems(self, items, data=None):
        """ Add items to widget

        :param items: List of items as string to add
        :type items: list[basestring]
        :param data: List of objects
        :type data: list[object]
        :return:
        :rtype:
        """
        items = items or []
        data = data or []

        for i, item in enumerate(items):
            d = None

            if i < len(data):
                d = data[i]
            self.addItem(item, d)

    def setText(self, text, index=0, setItem=False):
        """ Set text of the combo edit

        :type setItem: If the text matches the item text then set the item as well
        :param setItem:
        :param text:
        :type text:
        :return:
        :rtype:
        """

        self.comboEdits[index].setText(text)

    def setValue(self, value, index=0):
        self.comboEdits[index].setValue(value)

    def setValues(self, values, setItem=True):
        """ Set the values. Float or int

        :param values:
        :type values:
        :param setItem:
        :type setItem:
        :return:
        :rtype:
        """

        if type(values) is not list:
            values = [values]

        for i, v in enumerate(values):
            self.comboEdits[i].setValue(v)
        if setItem:
            self.findMatchingIndex(values, blockSignals=True)

    def setTexts(self, texts, setItem=False, blockSignals=False):
        """ Set text of the combo edit

        :type setItem: If the text matches the item text then set the item as well
        :param setItem:
        :param texts:
        :type texts: list(str)
        :return:
        :rtype:
        """

        if type(texts) is not list:
            texts = [texts]

        for i, t in enumerate(texts):
            self.comboEdits[i].setText(t)

        # If text matches item set item

        if setItem:
            self.findMatchingIndex(texts, blockSignals=True)

    def findMatchingIndex(self, texts, blockSignals=True):
        """ Find matching index based on the list of texts

        :param texts:
        :type texts: list
        :param blockSignals:
        :type blockSignals:
        :return:
        :rtype:
        """
        rowMatchFound = -1
        singleMatchFound = -1

        texts = [texts] if type(texts) is not list else texts

        # Check Exact match for all items first
        itemRows = self.items()
        for r, itemRow in enumerate(itemRows):
            if [item.itemData() for item in itemRow] == texts:
                rowMatchFound = r
                break

            # If not just find a match for the first text item
            if singleMatchFound == -1 and itemRow[0].itemData() == texts[0]:
                singleMatchFound = r

        newIndexInt = rowMatchFound if rowMatchFound != -1 else singleMatchFound

        # Apply the new index
        if newIndexInt != -1:
            if blockSignals:
                self.blockSignals(True)
            self.setIndexInt(rowMatchFound)
            if blockSignals:
                self.blockSignals(False)

    def addSeparator(self):
        """ Add Separator

        :return:
        :rtype:
        """
        self.comboPopup.addSeparator()

    def model(self):
        """ Get the model

        :return:
        :rtype:
        """
        return self.comboPopup.listView.model()

    def items(self):
        """ Get All items

        :return:
        :rtype:
        """
        for i in range(self.model().rowCount()):
            yield self.comboPopup.rowItems(self.model().index(i, 0))

    def addItem(self, text, data=None):
        """ Add item to menu

        :param text:
        :type text:
        :param data:
        :type data:
        :return:
        :rtype:
        """
        self.comboPopup.addItem(text, data)
        if self.currentItem() is None:
            index = self.model().index(0, 0)
            self.blockSignals(True)
            self.comboPopup.setCurrentIndex(index)
            self.blockSignals(False)

    def setLabelMenu(self, menu, mouseButton=QtCore.Qt.LeftButton):
        """ Set the name label menu

        :param menu:
        :type menu:
        :param mouseButton:
        :type mouseButton:
        :return:
        :rtype:
        """
        if self.nameLabel:
            self.nameLabel.setMenu(menu, mouseButton=mouseButton)

    def currentItem(self):
        """ Current Item

        :return:
        :rtype: Qt.QtGui.QStandardItem
        """

        return self.comboPopup.currentItem()

    def comboEditReturnPressed(self):
        """ When the return key is pressed for the combo edit

        :return:
        :rtype:
        """
        self._enterPressed = True

    def editFinished(self):
        """ Edit finished

        :return:
        :rtype:
        """

        if self._enterPressed:
            self.updateAspect(self.sender().parentWidget())
        self.activateWidget(ComboEditWidget.Default)
        event = EditChangedEvent(before=self.prevTexts, after=self.values())
        if self.renameMode:
            self.itemRenamed.emit(event)
        self.editingFinished.emit(event)

        # If its the same then don't emit
        if self.prevTexts != self.values():
            self.editModified.emit(event)
            self.comboEditChanged.emit(event)

        self.findMatchingIndex(self.values())

        if self.prevTexts is None:
            self.prevTexts = self.values()

    def itemRenamedEvent(self, event):
        """ On Item renamed event

        :param event:
        :type event: EditChangedEvent
        :return:
        :rtype:
        """
        self.comboPopup.currentItem().setText(str(event.after))

    def wheelEvent(self, event):
        """ Mouse Wheel event

        :param event:
        :type event:
        :return:
        :rtype:
        """

        if event.delta() > 0:
            self.scrollPrev()
        else:
            self.scrollNext()

        event.accept()

    def currentMouseOver(self):
        """ Gets the widget currently moused over

        :return:
        :rtype: QtWidgets.QWidget
        """
        pos = QtGui.QCursor.pos()
        return QtWidgets.QApplication.widgetAt(pos)

    def scrollPrev(self):
        """ Scrolls to previous index

        :return:
        :rtype:
        """
        self.scrollIndex(next=False)

    def scrollNext(self):
        """ Scrolls to next index

        :return:
        :rtype:
        """
        self.scrollIndex(next=True)

    def scrollIndex(self, next=True):
        """ Scroll index

        :param next:
        :type next:
        :return:
        :rtype:
        """

        if next:
            newIndex = self.comboPopup.listView.nextIndex()
        else:
            newIndex = self.comboPopup.listView.prevIndex()

        mouseOver = self.currentMouseOver()
        if mouseOver == self.primaryButton or mouseOver == self.secondaryButton:
            self.comboPopup.sourceButton = mouseOver
        else:
            self.comboPopup.sourceButton = self.primaryButton

        if newIndex.isValid():
            self.comboPopup.setCurrentIndex(newIndex)

    def blockSignals(self, b):
        """ Block signals.

        Make sure it blocks the signals of the child widgets as well

        :param b:
        :type b:
        :return:
        :rtype:
        """

        super(ComboEditWidget, self).blockSignals(b)

        [w.blockSignals(b) for w in utils.iterChildren(self)]
        [w.blockSignals(b) for w in utils.iterChildren(self.comboPopup)]

    def indexChanged(self, event):
        """ Item clicked

        :param event:
        :type event: zoo.libs.pyqt.extended.combobox.combomenupopup.ComboCustomEvent
        :return:
        :rtype:
        """
        if event is None:
            return

        if event.source == self.secondaryButton:
            menuButton = IndexChangedEvent.Secondary
        else:
            menuButton = IndexChangedEvent.Primary

        self.activateWidget(ComboEditWidget.Default)
        newTexts = []
        for item in event.items:
            newTexts.append(item.itemData())

        emitEvent = IndexChangedEvent(event.items, event.index, menuButton)

        self.setValues(newTexts, setItem=False)
        self.itemChanged.emit(emitEvent)
        self.comboEditChanged.emit(emitEvent)
        self.prevTexts = self.values()


    def itemText(self, index):
        """ Get item text from an index

        :param index:
        :type index: QtGui.QModelIndex
        :return:
        :rtype:
        """
        return self.comboPopup.model().itemFromIndex(index).text()

    def activatePopup(self):
        """ Activate the popup and place it below the widget

        :return:
        :rtype:
        """
        self.aboutToShow.emit()  # emits before the menu is drawn
        menuButton = self.sender()
        self.comboPopup.show(menuButton)
        pos = self.mapToGlobal(self.comboMainWidget.pos())
        rightPos = menuButton.mapToGlobal(QtCore.QPoint(menuButton.rect().right(), 0))
        pos.setY(pos.y() + self.comboMainWidget.height())
        width = rightPos.x() - pos.x()
        self.comboPopup.setFixedWidth(width)
        self.comboPopup.move(pos)
        [comboEdit.setFocusPolicy(QtCore.Qt.StrongFocus) for comboEdit in self.comboEdits]
        #self.comboPopup.setFocusProxy(self.comboEdits[0])

    def activateWidget(self, widgetType, sender=None):
        """ Activate the widget based on the type used

        :param widgetType:
        :type widgetType:
        :param sender:
        :type sender: QtWidgets.QWidget or elements.ComboEdit
        :return:
        :rtype:
        """
        if widgetType == ComboEditWidget.Default:
            for comboEdit in self.comboEdits:
                comboEdit.blockSignals(True)
                comboEdit.setEnabled(False)
                comboEdit.blockSignals(False)

        elif widgetType == ComboEditWidget.EditWidget:
            [c.clearFocus() for c in self.comboEdits]
            sender.setEnabled(True)
            sender.show()
            sender.selectAll()
            sender.setFocus()

    def activateMainWidget(self, event):
        """ Activate Rename Widget

        :param event:
        :type event:
        :return:
        :rtype:
        """
        if self.prevTexts is None:
            self.prevTexts = self.values()

        mouseOver = self.currentMouseOver()
        if mouseOver is not None:
            sender = utils.ancestor(mouseOver, ComboEdit) or utils.ancestor(mouseOver, ComboEditFloat) or utils.ancestor(mouseOver, ComboEditInt)
            if sender is not None:
                self.activateWidget(ComboEditWidget.EditWidget, sender=sender)

    def setIndexInt(self, index):
        """ Set the index by int, instead of a QModelIndex

        :param index:
        :type index: int
        :return:
        :rtype:
        """
        newIndex = self.comboPopup.listView.currentIndex().sibling(index, 0)

        self.comboPopup.setCurrentIndex(newIndex)

    def label(self):
        """ Returns the label

        :return:
        :rtype:
        """
        return self.nameLabel.text()

    def currentIndexInt(self):
        """ Get the current index as int

        :return:
        :rtype:
        """

        index = self.comboPopup.listView.currentIndex()
        return index.row()

    def currentData(self):
        """ Gets the current data

        :return:
        :rtype:
        """
        if self.comboPopup.currentItem() is None:
            return None
        return self.comboPopup.currentItem().itemData()

    def itemData(self, index):
        """ Get the item data

        :param index:
        :type index: int
        :return:
        :rtype: Qt.QtGui.QStandardItem
        """

        return self.model().item(index, 0).itemData()

    def iterItemData(self):
        """ Iterate through the item data

        :return:
        :rtype: collections.Iterable[Qt.QtGui.QStandardItem]
        """
        for i in range(self.model().rowCount()):
            yield self.itemData(i)

    def currentText(self, index=0):
        """ The text of the combo menu

        :return:
        :rtype:
        """
        return self.comboEdits[index].text()

    def text(self, index=0):
        """ Returns value of the text boxes as a list as float or int or string depending on the edit mode

        :param index: Current index of the possible text edits
        :type index: int
        :return value: Returns value of the text edit, can be float or int or string depending on the edit mode
        :rtype value: float or int or string
        """
        return self.comboEdits[index].text()

    def texts(self):
        """Returns all values of the text boxes as a list

        Same as self.values()

        :return valueList: Returns values of the text edits, can be float or int or string depending on the edit mode
        :rtype valueList: list(float or int or string)
        """
        texts = [t.text() for t in self.comboEdits]
        return texts[0] if len(texts) == 1 else texts

    def values(self):
        """ Return the values of the combo edits

        :return:
        :rtype:
        """
        values = [t.value() for t in self.comboEdits]
        return values[0] if len(values) == 1 else values

    def count(self):
        """ Number of items

        :return:
        :rtype:
        """
        return self.model().rowCount()

    def clear(self):
        """ Clear out the items

        :return:
        :rtype:
        """
        self.model().clear()

    def updateList(self, nameList, dataList=None, setName=None):
        """Updates the lists and optionally sets the index by the given name.

        The name list can contain separators in the format:
            self.SeparatorString = "---=---"

        :param nameList: A list of names to populate the comboEdit, can be
        :type nameList: list(str)
        :param dataList: Optional list of any data type to insert along with the names
        :type dataList: list
        :param setName: The name to set as the current index
        :type setName: str
        """
        dataList = dataList or []
        # Build the comboEdit list -----------------------------------------
        self.clear()
        index = None
        self.blockSignals(True)
        for i, name in enumerate(nameList):
            if str(name) == self.SeparatorString:
                self.addSeparator()
                continue
            if dataList:
                self.addItem(name, dataList[i])
            else:
                self.addItem(name, name)
            if setName is not None and name == setName:  # set as index
                index = i
        # Set the current index only if found ------------------------------
        self.blockSignals(True)
        self.setIndexInt(index or 0)
        self.blockSignals(False)

    def state(self, newValue=None):
        """ Get the state of the widget

        :return:
        :rtype:
        """
        newValue = newValue or self.values()
        if type(newValue) != list:
            newValue = [newValue]

        return {"values": newValue,
                "aspectLinked": self.aspectLinked()}

    def setState(self, state):
        """ Set the state of the widget

        :param state:
        :type state: dict
        :return:
        :rtype:
        """
        # Block signals so we can do it all at once after
        self.blockSignals(True)
        self.setValues(state['values'], setItem=True)

        aspectLinked = state.get('aspectLinked', None)
        if aspectLinked is not None:
            self.setAspectLinked(aspectLinked, self.aspectLinkedBtn)
        self.blockSignals(False)


class ComboEditRename(ComboEditWidget):
    """ Same as Combo Menu Rename
    Functionality for toolsets
    """

    def __init__(self, *args, **kwargs):
        newKwargs = {"renamesItem": True}
        if newKwargs.get("inputMode", None) is None:
            newKwargs.update({"inputMode": "string"})
        kwargs.update(newKwargs)
        super(ComboEditRename, self).__init__(*args, **kwargs)


class EditChangedEvent(object):
    before = None
    after = None

    def __init__(self, before, after):
        """ The event object that is sent after an event is signalled

        :param before:
        :type before:
        :param after:
        :type after:
        """
        self.before = before
        self.after = after


class IndexChangedEvent(object):
    Primary = "Primary"
    Secondary = "Secondary"
    index = None
    items = None

    def __init__(self, items, index, menuButton):
        """

        :param item:
        :type item: QtGui.QStandardItem
        :param index:
        :type index:
        :param menuButton: Primary or Secondary
        :type menuButton: "Primary" or "Secondary"
        """
        self.items = items
        self.index = index
        self.menuButton = menuButton
