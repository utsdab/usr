from Qt import QtWidgets, QtCore

from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import extendedbutton, togglewidgets
from zoo.libs.pyqt.widgets import flowlayout


class SettingsTweakBar(QtWidgets.QFrame):
    def __init__(self, parent=None, themePref=None):
        """ Bottom tweak bar widget

        :param parent:
        :param themePref:
        """
        super(SettingsTweakBar, self).__init__(parent=parent)
        self.bulbOnBtn = extendedbutton.ExtendedButton(parent=self)
        self.bulbOffBtn = extendedbutton.ExtendedButton(parent=self)
        self.rightBtn = extendedbutton.ExtendedButton(parent=self)
        self.leftBtn = extendedbutton.ExtendedButton(parent=self)
        self.mainLayout = elements.hBoxLayout(parent=self)
        self.flowWgt = QtWidgets.QFrame(parent=self)
        self.flowLayout = flowlayout.FlowLayout()

        self.themePref = themePref

        self.initUi()

    def initUi(self):
        """ Initialize tweak bar

        :return:
        """
        self.mainLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.flowLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.mainLayout.setContentsMargins(*utils.marginsDpiScale(5, 7, 5, 5))
        self.mainLayout.addWidget(self.flowWgt)
        self.flowWgt.setLayout(self.flowLayout)

        col = self.themePref.MAIN_FOREGROUND_COLOR
        self.leftBtn.setIconByName("arrowRotLeft", colors=tuple(col))
        self.rightBtn.setIconByName("arrowRotRight", colors=tuple(col))
        self.bulbOffBtn.setIconByName("bulbdark", colors=tuple(col))
        self.bulbOnBtn.setIconByName("bulbbright2", colors=tuple(col))
        iblCheckBox = togglewidgets.CheckBox("IBL Vis ", parent=self)
        iblCheckBox.setLayoutDirection(QtCore.Qt.RightToLeft)

        self.flowLayout.addWidget(iblCheckBox)
        self.flowLayout.addSpacing(utils.dpiScale(5))

        self.flowLayout.addWidget(TweakLineEdit("Rot ", parent=self))

        self.flowLayout.addWidget(self.leftBtn)
        self.flowLayout.addWidget(self.rightBtn)
        self.flowLayout.addWidget(TweakLineEdit("Scl cm ", parent=self))
        self.flowLayout.addWidget(TweakLineEdit("Intsty ", parent=self))

        self.flowLayout.addWidget(self.bulbOffBtn)
        self.flowLayout.addWidget(self.bulbOnBtn)


class TweakLineEdit(elements.StringEdit):
    def __init__(self, *args, **kwargs):
        super(TweakLineEdit, self).__init__(*args, **kwargs)
        self.edit.setFixedWidth(utils.dpiScale(30))
        self.layout.setContentsMargins(0, 0, 0, 0)

