from Qt import QtWidgets

import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

PLACE_R_TLTIP = "Place Reflection by www.braverabbit.com (Ingo Clemens)\n" \
                "With a light selected click on a surface to place the light (and it's highlight) \n" \
                "Hold Ctrl or Shift and click-drag to vary the distance of the light from the surface \n" \
                "https://github.com/IngoClemens/placeReflection"


class PlaceReflection(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "placeReflection"

    uiData = {"label": "Place Reflection",
              "icon": "circlecursor",
              "tooltip": PLACE_R_TLTIP,
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-place-reflection/"}

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced, in this case we are only building one UI mode """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.widgetsLayoutAll(parent)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------------------------
    # WIDGETS AND LAYOUT
    # ------------------------------------

    def widgetsLayoutAll(self, parent):
        """Creates the only UI for the toolset
        """
        self.mainLayout = elements.vBoxLayout(parent,
                                              margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                              spacing=0)
        self.placeReflectionBtn = elements.styledButton("Place Reflection", "placeReflection", parent,
                                                        toolTip=PLACE_R_TLTIP, style=uic.BTN_DEFAULT)
        self.mainLayout.addWidget(self.placeReflectionBtn)
        self.mainLayout.addStretch(1)

    # ------------------------------------
    # THIRD PARTY
    # ------------------------------------

    def placeReflection(self):
        """placeReflection by braverabbit https://github.com/IngoClemens/placeReflection"""
        try:  # Place reflection is a community tool and may not be installed with the light suite
            from zoo.apps.braverabbit_place_reflection import placeReflection
            placeReflectionTool = placeReflection.PlaceReflection()
            placeReflectionTool.create()
        except ImportError:
            om2.MGlobal.displayWarning("The package `third_party_community` must be installed for "
                                       "Place Reflection by Braverabbit.")

    def uiConnections(self):
        """Add the connections
        """
        self.placeReflectionBtn.clicked.connect(self.placeReflection)
