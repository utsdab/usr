from Qt import QtCore, QtWidgets

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements, searchwidget
from zoo.libs.pyqt.widgets import extendedbutton
from zoo.libs.pyqt.widgets.slidingwidget import SlidingWidget


class DirectoriesTree(QtWidgets.QTreeWidget):
    def __init__(self, *args, **kwargs):
        """ Directories Tree

        :param args:
        :param kwargs:
        """
        super(DirectoriesTree, self).__init__(*args, **kwargs)


class DirectoriesWidget(QtWidgets.QFrame):
    def __init__(self, parent=None, themePref=None):
        """ Directories Widget

        :param parent:
        :param themePref:
        """
        super(DirectoriesWidget, self).__init__(parent=parent)
        self.menuBtn = extendedbutton.ExtendedButton()

        self.searchEdit = searchwidget.SearchLineEdit(parent=self)
        self.searchEdit.setMinimumSize(utils.sizeByDpi(QtCore.QSize(21, 20)))

        self.titleLabel = elements.ClippedLabel(parent=self, text="DIRECTORIES")
        utils.setStylesheetObjectName(self.titleLabel, "HeaderLabel")

        self.slidingWidget = SlidingWidget(self)
        self.slidingWidget.setWidgets(self.searchEdit, self.titleLabel)

        self.mainLayout = elements.vBoxLayout(self)

        self.tree = DirectoriesTree(parent=self)
        self.themePref = themePref
        self.initUi()

    def initUi(self):
        """ Init Ui

        :return:
        """
        # header
        headerLayout = self.headerLayoutInit()

        self.mainLayout.addLayout(headerLayout)
        self.mainLayout.addWidget(self.tree)
        headerLayout.setContentsMargins(*utils.marginsDpiScale(8, 6, 6, 6))

        self.tree.header().hide()

        testNames = ["Pure White", "Strong Colors", "Outdoor", "Mood"]
        for t in testNames:
            item = QtWidgets.QTreeWidgetItem(self.tree)
            item.setText(0, t)

    def headerLayoutInit(self):
        """ Init Header layout

        :return:
        """
        headerLayout = elements.hBoxLayout()

        col = self.themePref.FRAMELESS_TITLELABEL_COLOR

        self.menuBtn.setIconByName("menudots", col, 13)
        self.menuBtn.setMenuAlign(QtCore.Qt.AlignRight)
        self.menuBtn.addAction("Add Directory")
        self.menuBtn.addAction("Browse to Directory")

        headerLayout.addWidget(self.slidingWidget)
        headerLayout.addWidget(self.menuBtn)
        headerLayout.setStretch(0, 1)

        return headerLayout

