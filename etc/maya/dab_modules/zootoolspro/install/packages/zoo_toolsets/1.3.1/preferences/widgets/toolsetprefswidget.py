from Qt import QtWidgets

from zoo.apps.preferencesui import model
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended import combobox
from zoo.libs.pyqt.widgets import togglewidgets
from zoo.libs.pyqt.widgets import elements

class ToolsetsPrefsWidget(model.SettingWidget):
    # categoryTitle = "toolsets"  # commenting out this line disables the widget from appearing WIP

    def __init__(self, parent=None):
        # Todo: add documentation
        super(ToolsetsPrefsWidget, self).__init__(parent)

        self._initUI()

    def _initUI(self):
        mLayout = elements.hBoxLayout(self)

        def loremWidget():
            contentsLayout = elements.vBoxLayout()

            exportBox = QtWidgets.QHBoxLayout()
            exportBox.addWidget(QtWidgets.QLabel("Export Options:"))
            exportBox.addWidget(combobox.ExtendedComboBox(["Scene Objects & Shaders"], parent=self.parent()))

            contentsLayout.addLayout(exportBox)
            contentsLayout.addWidget(
                QtWidgets.QPushButton(iconlib.iconColorized("save", size=240), "Export"))
            contentsLayout.addSpacing(10)

            hbox1 = QtWidgets.QHBoxLayout()
            hbox1.addWidget(togglewidgets.CheckBox("Lorem Ipsum", color=(255, 255, 255)))

            arnoldBox = QtWidgets.QHBoxLayout()
            arnoldBox.addWidget(QtWidgets.QLabel("Import as:"))
            arnoldBox.addWidget(combobox.ExtendedComboBox(["Arnold"], parent=self.parent()))
            hbox1.addLayout(arnoldBox)

            hbox2 = QtWidgets.QHBoxLayout()
            hbox2.addWidget(togglewidgets.CheckBox("Lorem Ipsum"))
            hbox2.addWidget(togglewidgets.CheckBox("Lorem Ipsum"))

            contentsLayout.addLayout(hbox1)
            contentsLayout.addLayout(hbox2)
            contentsLayout.addWidget(
                QtWidgets.QPushButton(iconlib.iconColorized("copy", size=240), "Import"))

            contentsLayout.addStretch(1)
            return contentsLayout

        mLayout.addLayout(loremWidget())
        mLayout.addLayout(loremWidget())
        mLayout.setContentsMargins(*utils.marginsDpiScale(4, 4, 4, 4))
