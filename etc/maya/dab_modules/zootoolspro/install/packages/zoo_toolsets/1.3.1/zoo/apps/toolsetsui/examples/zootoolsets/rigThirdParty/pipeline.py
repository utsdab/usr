from Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs import iconlib
from zoo.libs.pyqt.extended import combobox
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import roundbutton


class Pipeline(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "pipeline"
    uiData = {"label": "Open Pipeline - By Lior Ben Horin",
              "icon": "pipeline",
              "tooltip": "Open The Pipeline Project Manager - By Lior Ben Horin",
              "defaultActionDoubleClick": False
    }

    @classmethod
    def contents(cls):
        return [cls.initCompactWidget, cls.initAdvancedWidget]

    @classmethod
    def initCompactWidget(cls, parent):
        contentsLayout = elements.vBoxLayout(parent)
        parent.setLayout(contentsLayout)

        exportBox = QtWidgets.QHBoxLayout()
        exportBox.addWidget(
            QtWidgets.QPushButton(iconlib.iconColorized("pipeline", size=240,
                                                        color=parent.property("color")), "Anim Clip"))
        contentsLayout.addLayout(exportBox)
        contentsLayout.addStretch(1)

    @classmethod
    def initAdvancedWidget(cls, parent):
        contentsLayout = elements.vBoxLayout(parent)
        parent.setLayout(contentsLayout)

        exportBox = QtWidgets.QHBoxLayout()
        exportBox.addWidget(QtWidgets.QLabel("Export Options:"))
        exportBox.addWidget(combobox.ExtendedComboBox(["Scene Objects & Shaders"], parent=parent))

        contentsLayout.addLayout(exportBox)
        contentsLayout.addWidget(
            QtWidgets.QPushButton(iconlib.iconColorized("pipeline", size=240,
                                                        color=parent.property("color")), "Anim CLip"))
        contentsLayout.addSpacing(10)

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(QtWidgets.QCheckBox("Lorem Ipsum"))

        arnoldBox = QtWidgets.QHBoxLayout()
        arnoldBox.addWidget(QtWidgets.QLabel("Import as:"))
        arnoldBox.addWidget(combobox.ExtendedComboBox(["Arnold"], parent=parent))
        hbox1.addLayout(arnoldBox)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(QtWidgets.QCheckBox("Lorem Ipsum"))
        hbox2.addWidget(QtWidgets.QCheckBox("Lorem Ipsum"))

        contentsLayout.addLayout(hbox1)
        contentsLayout.addLayout(hbox2)
        contentsLayout.addWidget(
            QtWidgets.QPushButton(iconlib.iconColorized("copy", size=240, color=parent.property("color")), "Import"))


        btn = roundbutton.RoundButton(icon=iconlib.iconColorized("arrowRight"))
        btn.setFixedSize(QtCore.QSize(32,32))

        contentsLayout.addWidget(btn)

        contentsLayout.addStretch(1)

    def defaultAction(self):
        pass
