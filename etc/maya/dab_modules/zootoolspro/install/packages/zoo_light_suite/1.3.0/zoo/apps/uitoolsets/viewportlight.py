from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.lighting import viewportlights
from zoo.libs.maya.cmds.cameras import cameras

UI_MODE_COMPACT = 0


class ViewportLight(toolsetwidgetmaya.ToolsetWidgetMaya):
    """
    """
    id = "viewportLight"
    uiData = {"label": "Viewport Light SurfaceStandard",
              "icon": "bandAid",
              "tooltip": "Creates a light that compensates for the 2020 darkness of the surface standard shader",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-viewport-light-surface-standard/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        currentCam = cameras.getFocusCamera()
        if currentCam:  # then add as the GUI name
            self.properties.nameTxt.value = currentCam
            self.updateFromProperties()

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # PROPERTIES
    # ------------------

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return []

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def createViewportLight(self):
        """Creates the viewport light and constrains to the current camera in the GUI
        """
        camera = self.properties.nameTxt.value
        viewportlights.createViewportLight_surfaceStandard(cameraActive=camera)

    def getCameraName(self):
        """Gets the camera name in the current panel or in focus and adds it to the GUI"""
        self.properties.nameTxt.value = cameras.getFocusCamera()
        self.updateFromProperties()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        self.compactWidget.createLightBtn.clicked.connect(self.createViewportLight)
        self.compactWidget.getCameraBtn.clicked.connect(self.getCameraName)


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
        # Camera Name -----------------------------------------------------
        toolTip = "The name of the camera that the light will be constrained to."
        self.nameTxt = elements.StringEdit(label="Camera",
                                           editText="persp",
                                           toolTip=toolTip,
                                           labelRatio=1,
                                           editRatio=2)
        # Get Camera Name -----------------------------------------------------
        toolTip = "Gets the camera name from the active panel or panel in focus."
        self.getCameraBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        # Create Btn --------------------------------------------
        toolTip = "Creates a viewport light adjusted to compensate for the darker \n" \
                  "Arnold and surfaceStandard shaders in Maya 2020."
        self.createLightBtn = elements.styledButton("Viewport Light",
                                                    "bandAid",
                                                    parent,
                                                    toolTip,
                                                    style=uic.BTN_DEFAULT)


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
        contentsLayout = elements.vBoxLayout(parent=parent,
                                             margins=(uic.WINSIDEPAD, uic.LRGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SLRG)
        # Top Combo Layout ---------------------------------------
        nameLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                         spacing=uic.SREG)
        nameLayout.addWidget(self.nameTxt, 9)
        nameLayout.addWidget(self.getCameraBtn, 1)
        nameLayout.addWidget(self.createLightBtn, 12)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(nameLayout)
