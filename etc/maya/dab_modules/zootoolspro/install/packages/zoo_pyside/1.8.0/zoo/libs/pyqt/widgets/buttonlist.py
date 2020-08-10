# Embedded file name: D:\git\zootools_pro\zoocore\zoo\libs\pyqt\widgets\buttonlist.py
from Qt import QtWidgets, QtCore

class ButtonList(QtWidgets.QWidget):
    """
    A nice vertical button list with an optional header and with a searchable feature.
    """

    def __init__(self, parent=None, title='', showTitle=True, showSearch=True):
        super(ButtonList, self).__init__(parent=parent)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(2, 4, 2, 4)
        self.titleLbl = QtWidgets.QLabel(title)
        self.searchEdit = QtWidgets.QLineEdit()
        self.toolBar = QtWidgets.QHBoxLayout()
        self.buttonList = ButtonListTable(self)
        self.initUi()

    def initUi(self):
        self.searchEdit.setPlaceholderText('Search...')
        self.toolBar.addWidget(self.searchEdit)
        self.mainLayout.addWidget(self.titleLbl)
        self.mainLayout.addLayout(self.toolBar)
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.buttonList)

    def connections(self):
        """ Test connection """
        self.searchEdit.textChanged.connect(self.onSearchChanged)

    def onSearchChanged(self):
        text = self.searchEdit.text().lower()
        self.buttonList.filter(text)


class ButtonListTable(QtWidgets.QTableWidget):

    def __init__(self, parent = None):
        super(ButtonListTable, self).__init__(parent)
        self.listItems = []
        self.initUi()

    def initUi(self):
        self.setColumnCount(1)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)

    def filter(self, text):
        """
        Filter table based on text. Hides the row if doesn't match the text
        :param text: Text to match
        """
        for i in range(self.rowCount()):
            found = text not in self.cellWidget(i, 0).text().lower()
            self.setRowHidden(i, found)