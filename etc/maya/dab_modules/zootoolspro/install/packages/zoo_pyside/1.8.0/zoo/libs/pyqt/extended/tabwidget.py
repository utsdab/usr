from functools import partial
from Qt import QtWidgets, QtCore
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.utils import uiconstants


class TabWidget(QtWidgets.QTabWidget):
    # allow for custom actions, the qmenu instance is passed to the signal
    contextMenuRequested = QtCore.Signal(object)
    newTabRequested = QtCore.Signal(object, str)

    def __init__(self, name="", showNewTab=False, parent=None):
        super(TabWidget, self).__init__(parent=parent)
        self.setObjectName(name)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenu)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.newTabBtn = elements.buttonExtended(style=uiconstants.BTN_DEFAULT,
                                                 text="+",
                                                 toolTip="Add New Tab",
                                                 maxWidth=40,
                                                 parent=self)
        self.newTabBtn.setVisible(showNewTab)
        self.setCornerWidget(self.newTabBtn, QtCore.Qt.TopLeftCorner)
        self.newTabBtn.clicked.connect(partial(self.addTabWidget, None, True))

    def onAddTab(self, widget, name):

        # Add tab
        self.addTab(widget, name)

        # Set new tab active
        self.setCurrentIndex(self.count() - 1)

    def addTabWidget(self, childWidget=None, dialog=False, name=None):
        """Will open dialog to get tab name and create a new tab with the childWidget set as the child of the
        new tab.

        :param childWidget: QtWidget

        """
        name = name or "TEMP"
        if dialog:
            # Open input window
            name, ok = QtWidgets.QInputDialog.getText(self,
                                                      self.tr("Create new tab"),
                                                      self.tr('Tab name'),
                                                      QtWidgets.QLineEdit.Normal,
                                                      self.tr(''))
            if not (ok and name):
                return
        self.newTabRequested.emit(childWidget, name)

    def onTabCloseRequested(self):
        """Creates a inputDialog for removing the tab
        """
        # Get current tab index
        index = self.currentIndex()

        # Open confirmation
        reply = QtWidgets.QMessageBox.question(self, 'Delete',
                                               "Delete tab '{}'?".format(self.tabText(index)),
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

    def renameTab(self):
        """Creates a inputDialog for renaming the tab name
        """
        # Get current tab index
        index = self.currentIndex()

        # Open input window
        name, ok = QtWidgets.QInputDialog.getText(self,
                                                  self.tr("Tab name"),
                                                  self.tr('New name'),
                                                  QtWidgets.QLineEdit.Normal,
                                                  self.tr(self.tabText(index)))
        if not ok and name:
            return

        self.setTabText(index, name)

    def _contextMenu(self, pos):
        """ Set up a custom context menu, the contextMenuRequested signal is called at the end of
        the function so the user can add their own actions/child menus without overriding the function. exec is Called
        after user mode.

        :param pos: the mouse position
        :type pos: QPoint
        """
        menu = QtWidgets.QMenu()
        rename = menu.addAction("Rename")
        rename.triggered.connect(self.renameTab)

        add = menu.addAction("Add Tab")
        add.triggered.connect(self.addTabWidget)

        self.contextMenuRequest.emit(menu)
        menu.exec_(self.mapToGlobal(pos))
