from Qt import QtCore, QtWidgets

from zoo.apps.hotkeyeditor.core import hotkeys
from zoo.apps.hotkeyeditor.core import utils
from zoo.libs.pyqt import utils as qtUtils
from zoo.libs import iconlib
from zoo.libs.pyqt import utils as qtutils
from zoo.libs.pyqt.widgets import elements, searchwidget
from zoo.libs.pyqt.widgets import iconmenu
from zoo.libs.utils import zlogging
from zoo.preferences.core import preference

logger = zlogging.getLogger(__name__)

THEME_PREFS = preference.interface("core_interface")


class HotkeyTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):

        super(HotkeyTableWidget, self).__init__(parent)

        self.selectedHotkey = None  # type: hotkeys.Hotkey
        self.selectedRow = -1
        self.hotkeyView = parent
        self.headers = ('Application Command', 'Hotkey')
        self.keySetManager = self.hotkeyView.keySetManager
        self.hotkeyPropertiesWgt = self.hotkeyView.hotkeyPropertiesWgt
        self.setAlternatingRowColors(True)

        self.initUi()

        self.connections()

    def initUi(self):

        self.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

        self.verticalHeader().hide()
        self.setWordWrap(False)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(self.headers)

        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    def setKeySet(self, keyset):
        """
        Sets the tables contents based on the given keyset

        :param keyset:
        :return:
        """
        # self.clear() makes it lag like crazy so we use this instead
        self.setRowCount(0)
        self.setRowCount(keyset.count())

        for i, h in enumerate(keyset.hotkeys):
            self.setRow(i, h)

        self.resizeColumnsToContents()

    def setRow(self, index, hotkey):
        if not isinstance(hotkey, hotkeys.Hotkey):
            return

        # Stylesheeting being a pain so we'll add some spaces instead
        cmdItem = HotkeyWidgetItem("  {}  ".format(hotkey.getPrettyName()))

        self.setItem(index, 0, cmdItem)
        hotkeyItem = QtWidgets.QTableWidgetItem()

        self.setItem(index, 1, hotkeyItem)
        hotkeyEdit = HotkeyDetectEditMod(text=hotkey.toString(), parent=self, item=hotkeyItem)
        hotkeyEdit.hotkeyData = hotkey

        self.setCellWidget(index, 1, hotkeyEdit)

        # Redundant data to make all the codes happy
        cmdItem.hotkeyData = hotkey

        hotkeyEdit.hotkeyEdited.connect(
            lambda hke=hotkeyEdit, i=index, h=hotkey: self.hotkeyEditFinished(hke, i, h))

        if self.keySetManager.isLockedKeySet() and not utils.isAdminMode():
            hotkeyEdit.setEnabled(False)
        else:
            hotkeyEdit.setEnabled(True)

    def addRow(self, hotkey):
        """ Adds a row based on the hotkey

        :param hotkey:
        :type hotkey:
        :return:
        :rtype:
        """
        # Only adds a row based on Hotkey()
        if not isinstance(hotkey, hotkeys.Hotkey):
            return

        self.insertRow(0)
        self.setRow(0, hotkey)

    def empty(self):
        self.setRowCount(0)
        self.setHorizontalHeaderLabels(self.headers)

    def updateHotkeys(self):

        self.setKeySet(self.keySetManager.currentKeySet())

        # Update properties as well
        self.refreshProperties()

    def connections(self):
        self.clicked.connect(self.tableClicked)

    def hotkeyEditFinished(self, hotkeyEdit, index, hotkey):
        newHotkey = hotkeyEdit.text()

        # If it's not the same then save the changes
        if newHotkey != hotkey.toString():
            logger.info("Saving")
            hotkey.setHotkey(newHotkey)
            self.keySetManager.setModified(True)
            self.hotkeyView.updateRevertUi()

    def refreshProperties(self):
        self.tableClicked()

    def updateRow(self):
        """
        Updates the current row with the pretty name of the current hotkey
        :return:
        """
        hotkeyName = self.selectedHotkey.getPrettyName()
        row = self.selectedRow
        self.item(row, 0).setText("  {}  ".format(hotkeyName))

    def tableClicked(self, modelIndex=""):
        """
        :param modelIndex: Can be one of three things:
            QtCore.QModelIndex - From the actual table event click
            "" - nothing here so they just want to refresh the data
            int - set data based on the row index int
        :return:
        """

        # Maybe can do this better
        if isinstance(modelIndex, QtCore.QModelIndex):
            index = modelIndex.row()
        elif modelIndex == "":
            index = self.selectedRow
        else:
            index = modelIndex

        # always get first column
        hotkeyData = self.item(index, 0).hotkeyData

        self.selectedHotkey = hotkeyData  # type: hotkeys.Hotkey
        self.selectedRow = index
        self.hotkeyPropertiesWgt.setPropertiesByHotkey(hotkeyData)
        self.hotkeyPropertiesWgt.setupRuntimeCmdUi(hotkeyData.runtimeCommand)
        self.updateRow()

        if self.keySetManager.isLockedKeySet() and not utils.isAdminMode():
            self.hotkeyView.deleteHotkeyBtn.setEnabled(False)
        else:
            self.hotkeyView.deleteHotkeyBtn.setEnabled(True)

    def filterText(self, text):
        """ Filter the table by text

        :param text:
        :return:
        """
        col = 0
        model = self.model()

        self.setUpdatesEnabled(False)

        for r in range(model.rowCount()):
            index = model.index(r, col)
            if text == "" or text in index.data().lower():
                if self.isRowHidden(r):
                    self.setRowHidden(r, False)
            else:
                self.setRowHidden(r, True)

        self.setUpdatesEnabled(True)

    def filterHotkey(self, hotkey):
        """ Filter the table by hotkey

        :param hotkey:
        :return:
        """
        col = 1
        model = self.model()
        hotkeyD = hotkeys.strToData(hotkey, True)

        self.setUpdatesEnabled(False)

        for r in range(model.rowCount()):
            data = hotkeys.strToData(self.cellWidget(r, col).text(), True)
            if hotkeyD == data or hotkey == "":
                if self.isRowHidden(r):
                    self.setRowHidden(r, False)
            else:
                self.setRowHidden(r, True)

        self.setUpdatesEnabled(True)


class SearchWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, hotkeyTable=None, minWidth=200):
        """ Search Widget for the hotkey table

        :param parent:
        :param hotkeyTable:
        """
        super(SearchWidget, self).__init__(parent=parent)

        self.searchEdit = HotkeySearchEdit(self, hotkeyTable)
        self.searchEdit.setMinimumWidth(qtutils.dpiScale(minWidth))
        self.hotkeyEdit = HotkeyEdit(self, hotkeyTable)
        self.hotkeyEdit.setMinimumWidth(qtutils.dpiScale(minWidth))

        self.searchFilterMenu = SearchFilterMenu(self)

        mainLayout = elements.hBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(self.searchEdit)
        mainLayout.addWidget(self.hotkeyEdit)
        mainLayout.addWidget(self.searchFilterMenu)

        self.showSearchEdit()

        self.searchFilterMenu.filterTextAction.connect(self.showSearchEdit)
        self.searchFilterMenu.filterHotkeyAction.connect(self.showHotkeyEdit)

        self.setLayout(mainLayout)

    def showSearchEdit(self):
        """ Hide hotkey edit widget, show searchEdit

        :return:
        """
        self.searchEdit.show()
        self.hotkeyEdit.hide()
        self.hotkeyEdit.clear()

    def showHotkeyEdit(self):
        """ Hide searchEdit, show hotkey edit widget

        :return:
        """
        self.searchEdit.hide()
        self.hotkeyEdit.show()
        self.searchEdit.clear()


class SearchFilterMenu(iconmenu.IconMenuButton):
    menuIcon = "menudots"
    filterTextAction = QtCore.Signal()
    filterHotkeyAction = QtCore.Signal()

    def __init__(self, parent=None):
        """ Filter menu button to switch between the filter types

        :param parent:
        """
        super(SearchFilterMenu, self).__init__(parent=parent)

    def initUi(self):
        super(SearchFilterMenu, self).initUi()

        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)

        searchIcon = iconlib.iconColorized("magnifier", qtutils.dpiScale(16))
        hotkeyIcon = iconlib.iconColorized("key2", qtutils.dpiScale(16))

        self.addAction("Filter by Text", connect=lambda: self.filterTextAction.emit(), icon=searchIcon)
        self.addAction("Filter by Hotkey", connect=lambda: self.filterHotkeyAction.emit(), icon=hotkeyIcon)

        self.setMenuAlign(QtCore.Qt.AlignRight)


class HotkeySearchEdit(searchwidget.SearchLineEdit):
    def __init__(self, parent=None, table=None):
        """ Filter by application command

        :param parent:
        :param table:
        """
        super(HotkeySearchEdit, self).__init__(parent=parent)

        self.hotkeyTable = table  # type: HotkeyTableWidget
        self.setPlaceholderText("Search Hotkey Command...")
        self.setFixedWidth(qtUtils.dpiScale(150))
        self.setFixedHeight(qtUtils.dpiScale(20))

        self.textChanged.connect(self.onSearchChanged)

    def onSearchChanged(self):
        if self.hotkeyTable is not None:
            text = self.text().lower()
            self.hotkeyTable.filterText(text)


class HotkeyEdit(elements.HotkeyDetectEdit):
    def __init__(self, parent=None, table=None):
        """ Filter by entered hotkey

        :param parent:
        :param table:
        """
        super(HotkeyEdit, self).__init__(parent=parent, iconsEnabled=True, searchIcon="key2")

        self.hotkeyTable = table  # type: HotkeyTableWidget
        self.setPlaceholderText("Enter Hotkey...")
        self.setFixedWidth(qtUtils.dpiScale(100))
        self.setFixedHeight(qtUtils.dpiScale(20))

        self.textChanged.connect(self.onSearchChanged)

    def onSearchChanged(self):
        if self.hotkeyTable is not None:
            text = self.text().lower()
            self.hotkeyTable.filterHotkey(text)


class HotkeyWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text):
        super(HotkeyWidgetItem, self).__init__(text)
        self.setFlags(QtCore.Qt.ItemIsEnabled)

        self.hotkeyData = ""  # type: hotkeys.Hotkey


class HotkeyDetectEditMod(elements.HotkeyDetectEdit):
    def __init__(self, text, parent, item):
        super(HotkeyDetectEditMod, self).__init__(text)

        self.tableParent = parent

        self.hotkeyData = ""
        self.item = item

    def focusInEvent(self, event):
        self.tableParent.tableClicked(self.tableParent.row(self.item))

