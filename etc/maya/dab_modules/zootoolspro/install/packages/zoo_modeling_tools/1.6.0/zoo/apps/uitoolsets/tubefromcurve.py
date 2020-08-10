from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.modeling import paintfxtube
from zoo.libs.maya.cmds.objutils import curves

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class TubeFromCurve(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "tubeFromCurve"
    info = "Template file for building new GUIs."
    uiData = {"label": "Tube From Curve (beta)",
              "icon": "createTube",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-tube-from-curve/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiModeList()
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        """
        return self.widgets()[self.displayIndex()].children()[0]

    def uiModeList(self):
        """Creates self.uiInstanceList
        A list of the uiMode widget classes eg [self.compactWidget, self.advancedWidget]
        """
        self.uiInstanceList = list()
        for widget in self.widgets():
            self.uiInstanceList.append(widget.children()[0])

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(TubeFromCurve, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """
        curves.createCurveContext(degrees=3)

    @undodecorator.undoDecorator
    def createTube(self):
        """
        """
        paintfxtube.paintFxTubeRigSelected(radius=self.properties.radiusFloat.value,
                                           tubeSections=self.properties.axisDivisionsFloat.value,
                                           minClip=self.properties.minClipFloat.value,
                                           maxClip=self.properties.maxClipFloat.value,
                                           density=self.properties.densityFloat.value,
                                           polyLimit=self.properties.polyLimitFloat.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.createTubeBtn.clicked.connect(self.createTube)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Radius Float ---------------------------------------
        tooltip = "The radius of the tube."
        self.radiusFloat = elements.FloatEdit(label="Radius",
                                               editText=0.5,
                                               toolTip=tooltip)
        # Axis Divisions Float ---------------------------------------
        tooltip = "The amount of divisions around the axis of the tube"
        self.axisDivisionsFloat = elements.FloatEdit(label="Axis Divisions",
                                                      editText=12.0,
                                                      toolTip=tooltip)
        # Density Float ---------------------------------------
        tooltip = "The density of the polygon count of the tube \n" \
                  "More dense is more polygons."
        self.densityFloat = elements.FloatSlider(label="Density",
                                                 defaultValue=2.0,
                                                 toolTip=tooltip,
                                                 sliderMax=50.0)
        if uiMode == UI_MODE_ADVANCED:
            # Min Float ---------------------------------------
            tooltip = "The minimum end point of the tube relative to the curve. "
            self.minClipFloat = elements.FloatSlider(label="Min Clip",
                                                     defaultValue=0.0,
                                                     toolTip=tooltip,
                                                     sliderMax=1.0)
            # Max Float ---------------------------------------
            tooltip = "The minimum start point of the tube relative to the curve. "
            self.maxClipFloat = elements.FloatSlider(label="Max Clip",
                                                     defaultValue=1.0,
                                                     toolTip=tooltip,
                                                     sliderMax=1.0)
            # Poly Limit Float ---------------------------------------
            tooltip = "The total polygon limit of the tube. \n " \
                      "Small values will limit the poly count. "
            self.polyLimitFloat = elements.FloatEdit(label="Poly Limit",
                                                      editText=200000,
                                                      toolTip=tooltip)
        # Create Button ---------------------------------------
        tooltip = "Select a curve and click to create a polygon tube rig"
        self.createTubeBtn = elements.styledButton("Create Tube",
                                                   icon="createTube",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        # Bake Button ---------------------------------------
        tooltip = "Keeps the tube in it's current state while deleting the tube rig."
        self.bakeTubeBtn = elements.styledButton("Bake",
                                                 icon="checkMark",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT)
        # Create CV Curve Button ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic)"
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=parent,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Create CV Curve Button ------------------------------------
        toolTip = "Delete the tube setup, leaves the original curve."
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               toolTip=toolTip,
                                               parent=parent,
                                               minWidth=uic.BTN_W_ICN_MED)
        # todo: unhide and use buttons
        self.deleteBtn.hide()
        self.bakeTubeBtn.hide()


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Radius Layout ---------------------------------------
        radiusLayout = elements.hBoxLayout()
        radiusLayout.addWidget(self.radiusFloat, 1)
        radiusLayout.addWidget(self.axisDivisionsFloat, 1)
        # Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout()
        buttonLayout.addWidget(self.createTubeBtn, 7)
        buttonLayout.addWidget(self.bakeTubeBtn, 3)
        buttonLayout.addWidget(self.deleteBtn, 1)
        buttonLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(radiusLayout)
        mainLayout.addWidget(self.densityFloat)
        mainLayout.addLayout(buttonLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Radius Layout ---------------------------------------
        radiusLayout = elements.hBoxLayout()
        radiusLayout.addWidget(self.radiusFloat, 1)
        radiusLayout.addWidget(self.axisDivisionsFloat, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SREG)
        gridLayout.addWidget(self.polyLimitFloat, 1, 0)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout()
        buttonLayout.addWidget(self.createTubeBtn, 7)
        buttonLayout.addWidget(self.bakeTubeBtn, 3)
        buttonLayout.addWidget(self.deleteBtn, 1)
        buttonLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(radiusLayout)
        mainLayout.addWidget(self.densityFloat)
        mainLayout.addWidget(self.minClipFloat)
        mainLayout.addWidget(self.maxClipFloat)
        mainLayout.addLayout(gridLayout)
        mainLayout.addLayout(buttonLayout)
