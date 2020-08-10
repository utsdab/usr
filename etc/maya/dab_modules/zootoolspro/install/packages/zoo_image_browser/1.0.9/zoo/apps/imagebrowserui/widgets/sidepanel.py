from Qt import QtCore, QtWidgets

from zoo.libs import iconlib
from zoo.libs.pyqt.widgets import elements


class SidePanel(QtWidgets.QStackedWidget):
    def __init__(self, parent=None, themePref=None, startHidden=True):
        """ Side panel (currently on the right panel)

        :param parent:
        :param themePref:
        :param startHidden:
        """
        super(SidePanel, self).__init__(parent=parent)

        self.propertiesPanel = PropertiesPanel(self, themePref)

        self.addWidget(self.propertiesPanel)
        self.initUi()

        if startHidden:
            self.hide()

    def activateProperties(self):
        """ Activate the properties panel

        :return:
        """
        self.setCurrentWidget(self.propertiesPanel)

    def initUi(self):
        pass

    def addWidget(self, *args, **kwargs):
        super(SidePanel, self).addWidget(*args, **kwargs)


class PropertiesPanel(QtWidgets.QWidget):
    def __init__(self, parent=None, themePref=None):
        """ Properties panel

        :param parent:
        :param themePref:
        """
        super(PropertiesPanel, self).__init__(parent=parent)
        self.imageWgt = QtWidgets.QFrame(self)
        self.mainLayout = elements.vBoxLayout(self)

        self.doneBtn = QtWidgets.QPushButton("Done", parent=self)
        self.cancelBtn = QtWidgets.QPushButton("Cancel", parent=self)
        self.themePref = themePref
        self.initUi()
        self.setMinimumWidth(0)

    def initUi(self):
        self.mainLayout.setContentsMargins(3, 3, 3, 3)

        self.mainLayout.setSpacing(5)
        foreColour = self.themePref.MAIN_FOREGROUND_COLOR
        headerLayout = elements.hBoxLayout()
        headerLayout.addWidget(self.imageWgt)
        headerLayout.addWidget(QtWidgets.QLineEdit(self, "Red Blue Sides"))
        headerLayout.setSpacing(8)
        headerLayout.setAlignment(QtCore.Qt.AlignTop)

        self.mainLayout.addLayout(headerLayout)
        self.imageWgt.setStyleSheet("background-color: grey")
        self.imageWgt.setFixedSize(QtCore.QSize(50, 50))

        typeLayout = elements.hBoxLayout()
        typeLayout.setContentsMargins(0, 0, 0, 0)
        typeLayout.addWidget(QtWidgets.QLabel("Type : "))
        typeLayout.addWidget(QtWidgets.QComboBox(self))
        self.mainLayout.addLayout(typeLayout)

        self.mainLayout.addSpacing(5)
        self.mainLayout.addWidget(QtWidgets.QLabel("Creator/s :"))
        self.mainLayout.addWidget(QtWidgets.QTextEdit("Andrew Silke", parent=self))

        self.mainLayout.addSpacing(5)
        self.mainLayout.addWidget(QtWidgets.QLabel("Website/s :"))
        self.mainLayout.addWidget(QtWidgets.QTextEdit("www.create3dcharacters.com", parent=self))

        self.mainLayout.addSpacing(5)
        self.mainLayout.addWidget(QtWidgets.QLabel("Tags :"))
        self.mainLayout.addWidget(QtWidgets.QTextEdit("beauty, pure, white, studio, softbox", parent=self))

        self.mainLayout.addSpacing(5)
        self.mainLayout.addWidget(QtWidgets.QLabel("Description :"))
        self.mainLayout.addWidget(QtWidgets.QTextEdit("Pure white light setup based on a studio light setup, "
                                                      "key lit from side", parent=self))

        buttonLayout = elements.hBoxLayout()
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.doneBtn.setIcon(iconlib.iconColorized("save", color=foreColour))
        self.cancelBtn.setIcon(iconlib.iconColorized("close", color=foreColour))
        buttonLayout.addWidget(self.doneBtn)
        buttonLayout.addWidget(self.cancelBtn)

        self.mainLayout.addLayout(buttonLayout)
