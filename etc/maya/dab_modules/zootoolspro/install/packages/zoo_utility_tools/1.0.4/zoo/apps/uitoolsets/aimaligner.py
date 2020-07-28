from maya import cmds
from maya.api import OpenMaya as om2

from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.command import executor
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

DFLT_UP_VECTOR = (0.00, 1.00, 0.00)
DFLT_AIM_VECTOR = (0.00, 0.00, 1.00)


class AimAligner(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "aimAligner"
    uiData = {"label": "Aim Aligner",
              "icon": "zooAlign",
              "tooltip": "Align Nodes & Objects",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-aim-aligner/"
              }

    def contents(self):
        return [self.initAdvancedWidget()]

    def initAdvancedWidget(self):
        parent = QtWidgets.QWidget(parent=self)
        advancedUI = UI(parent, self.properties, toolsetWidget=self)
        advancedUI.ui_advanced(parent)
        return parent


class UI(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, toolsetWidget=None):
        super(UI, self).__init__(parent=parent)
        self.properties = properties
        self.toolsetWidget = toolsetWidget
        self.executor = executor.Executor()

    def ui_advanced(self, parent):
        """Creates the medium UI for the toolset, UI Code goes here

        :param parent: the parent widget
        :type parent: obj
        """
        # Main Layout
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # UpVector vector box ------------------------------------
        tooTip = "The aim object/s will be rolled so this up axis (X, Y, Z) is up in the world."

        self.upVector = elements.VectorSpinBox("Up Vector",
                                               DFLT_UP_VECTOR,
                                               -1.0, 1.0,
                                               ("X", "Y", "Z"),
                                               toolTip=tooTip)
        # AimVector vector box ------------------------------------
        tooTip = "The aim axis (X, Y, Z) of the first selected object/s will be aimed at \n" \
                 "the last selected object in the selection."
        self.aimVector = elements.VectorSpinBox("Aim Vector",
                                                DFLT_AIM_VECTOR,
                                                -1.0,
                                                1.0,
                                                ("X", "Y", "Z"),
                                                toolTip=tooTip)
        # Aim Align button ------------------------------------
        toolTip = "Aim the first selected object/s towards the last selected object. \n" \
                  "At least two objects must be selected."
        self.alignBtn = elements.styledButton("Align Selected Objects",
                                              "zooAlign",
                                              parent,
                                              toolTip,
                                              style=uic.BTN_DEFAULT)
        mainLayout.addWidget(self.aimVector)
        mainLayout.addWidget(self.upVector)
        mainLayout.addItem(elements.Spacer(0, 5))  # width, height
        mainLayout.addWidget(self.alignBtn)
        self.connections()

    def alignCommand(self):
        """Runs the add suffix command
        """
        selObjs = cmds.ls(selection=True)
        if len(selObjs) < 2:
            om2.MGlobal.displayWarning("Please select more than one object, "
                                       "all objects will aim towards the last selected object")
            return
        self.executor.execute("zoo.maya.alignSelected",
                              aimVector=om2.MVector(self.properties.aimVector.value),
                              upVector=om2.MVector(self.properties.upVector.value))

    def connections(self):
        self.alignBtn.clicked.connect(self.alignCommand)
