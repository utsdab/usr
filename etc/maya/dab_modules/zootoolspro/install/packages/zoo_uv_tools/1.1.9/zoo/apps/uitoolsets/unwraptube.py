from functools import partial

from Qt import QtWidgets

from maya import cmds
from maya.api import OpenMaya as om2

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.maya.cmds.objutils import uvtransfer
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.general import undodecorator

from zoo.libs.maya.cmds.uvs import uvmacros, uvfunctions

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
UNWRAP_TYPES = ["Unfold And Straighten", "Unfold No Straighten", "Gridify No Unfold"]
UNFOLD_OPTIONS = ["Automatic Direction", "Regular Unfold", "Horizontal U Direction", "Vertical V Direction"]
UNFOLD_PLUGIN_NAME = uvfunctions.UNFOLD_PLUGIN_NAME


class UnwrapTube(toolsetwidgetmaya.ToolsetWidgetMaya):
    """Unwraps tubes and gridded meshes.  Extra straighten functions.
    """
    id = "unwrapTube"
    uiData = {"label": "Unfold Tube",
              "icon": "unwrapTube",
              "tooltip": "Unwrap Tube Tool, easy unwrap tubes and gridded meshes",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-unfold-tube/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.advancedWidget = GuiAdvanced(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        self.toggleDisableEnable()  # auto set the disable values of all widgets

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        properties are auto-linked if the name matches the widget name

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "unwrapTypeCombo", "value": 0},
                {"name": "unfoldOptionsCombo", "value": 0},
                {"name": "shaderSpaceCombo", "value": 2},
                {"name": "skinnedCombo", "value": 1}]

    def saveProperties(self):
        """Saves properties, keeps self.properties up to date with every widget change
        Overridden function which automates properties updates. Exposed here in case of extra functionality.

        properties are auto-linked if the name matches the widget name
        """
        super(UnwrapTube, self).saveProperties()
        self.toggleDisableEnable()  # disable or enable widgets

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return [
            {"type": "action",
             "name": "uv",
             "label": "Transfer UVs",
             "icon": "transferUVs",
             "tooltip": ""},
            {"type": "action",
             "name": "shader",
             "label": "Transfer Shader",
             "icon": "transferUVs",
             "tooltip": ""},
            {"type": "action",
             "name": "uv_shader",
             "label": "Transfer UVs & Shaders",
             "icon": "transferUVs",
             "tooltip": ""}
        ]

    @undodecorator.undoDecorator
    def executeActions(self, action):
        """Right click actions on the main toolset icon

        :param action:
        :type action:
        """
        name = action['name']
        if name == "uv":
            uvtransfer.transferSelected(transferUvs=True, transferShader=False)
        elif name == "shader":
            uvtransfer.transferSelected(transferUvs=False, transferShader=True)
        elif name == "uv_shader":
            uvtransfer.transferSelected(transferUvs=True, transferShader=True)

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def loadUnfoldPlugin(self):
        message = "The Unfold 3d plugin is not loaded. Load now?"
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox_ok(windowName="Load Unfold 3d Plugin", parent=None, message=message)
        return okPressed

    # ------------------
    # DISABLE/ENABLE WIDGETS
    # ------------------

    def toggleDisableEnable(self):
        """Will disable the name textbox with the autoName checkbox is off"""
        if self.properties.unwrapTypeCombo.value == 2:
            for uiInstance in self.widgets():  # Gridify disable Unfold Options
                uiInstance.children()[0].unfoldOptionsCombo.setDisabled(True)
        else:
            for uiInstance in self.widgets():  # Gridify disable Unfold Options
                uiInstance.children()[0].unfoldOptionsCombo.setDisabled(False)

    # ------------------
    # LOGIC
    # ------------------

    @undodecorator.undoDecorator
    def straightenUvs(self, dirType="all"):
        uvfunctions.straightenUvSelection(angle=self.properties.straightenAngleEdit.value,
                                          dirType=dirType)

    @undodecorator.undoDecorator
    def alignUVs(self, straightenType="minV"):
        uvfunctions.alignUvSelection(straightenType=straightenType)

    @undodecorator.undoDecorator
    def straightenLoopsWalk(self):
        uvmacros.walkEdgeLoopsStraightenSelection()

    @undodecorator.undoDecorator
    def edgeUnwrapTube(self, mode="tube"):
        """Does the edge selection Tube Unwrap
        Select a single edge that is the seam for a tube and run.
        """
        if self.properties.unwrapTypeCombo.value == 0:
            unfold = True
            straightenLoops = True
        elif self.properties.unwrapTypeCombo.value == 1:
            unfold = True
            straightenLoops = False
        else:  # == 2
            unfold = False
            straightenLoops = False
        dirType = "automatic"
        if unfold:
            if self.properties.unfoldOptionsCombo.value == 0:
                dirType = "automatic"
            elif self.properties.unfoldOptionsCombo.value == 1:
                dirType = "regular"
            elif self.properties.unfoldOptionsCombo.value == 2:
                dirType = "horizontal"
            else:  # == 3
                dirType = "vertical"
        if dirType == "regular":
            # Check plugin has loaded
            loaded = cmds.pluginInfo(UNFOLD_PLUGIN_NAME, query=True, loaded=True)
            if not loaded:
                okPressed = self.loadUnfoldPlugin()
                if okPressed:
                    cmds.loadPlugin(UNFOLD_PLUGIN_NAME)
                    om2.MGlobal.displayInfo("Please run the unfold tool now the plugin has loaded")
                    return
                return
        # Run
        if mode == "tube":
            uvmacros.unwrapTubeSelection(dirType=dirType,
                                         straightenLoops=straightenLoops,
                                         unfold=unfold,
                                         straightenAngle=self.properties.straightenAngleEdit.value,
                                         deleteHistory=self.properties.delHistoryCheckBox.value)
        else:
            uvmacros.unwrapGridShellSelection(dirType=dirType,
                                              straightenLoops=straightenLoops,
                                              unfold=unfold,
                                              straightenAngle=self.properties.straightenAngleEdit.value,
                                              deleteHistory=self.properties.delHistoryCheckBox.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        for widget in self.widgets():
            uiInstance = widget.children()[0]
            # Main Button
            uiInstance.unwrapTube.leftClicked.connect(partial(self.edgeUnwrapTube, mode="tube"))
            uiInstance.unwrapShell.leftClicked.connect(partial(self.edgeUnwrapTube, mode="grid"))
        # Straighten Buttons
        self.advancedWidget.straightenAllBtn.clicked.connect(partial(self.straightenUvs, dirType="all"))
        self.advancedWidget.straightenHorizontalBtn.clicked.connect(partial(self.straightenUvs, dirType="horizontal"))
        self.advancedWidget.straightenVerticalBtn.clicked.connect(partial(self.straightenUvs, dirType="vertical"))
        # Align Buttons
        self.advancedWidget.horizontalAlignCenterBtn.clicked.connect(partial(self.alignUVs, straightenType="avgU"))
        self.advancedWidget.horizontalAlignLeftBtn.clicked.connect(partial(self.alignUVs, straightenType="minU"))
        self.advancedWidget.horizontalAlignRightBtn.clicked.connect(partial(self.alignUVs, straightenType="maxU"))
        self.advancedWidget.verticalAlignCenterBtn.clicked.connect(partial(self.alignUVs, straightenType="avgV"))
        self.advancedWidget.verticalAlignTopBtn.clicked.connect(partial(self.alignUVs, straightenType="maxV"))
        self.advancedWidget.verticalAlignBottomBtn.clicked.connect(partial(self.alignUVs, straightenType="minV"))
        # Straight Loops Walk Buttons
        self.advancedWidget.edgeLoopStraightenBtn.clicked.connect(self.straightenLoopsWalk)


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
        # Transfer UV Sample Space Combobox -----------------------------------------------------
        toolTip = "Unfold: Gridify then unfold with the options as per 'Unfold Options'. \n" \
                  "Straighten: Gridify and unfold then straightens UVs. \n" \
                  "Gridify No Unfold:  Uses Maya's unitize then move and sew to unwrap.  Does not unfold."
        self.unwrapTypeCombo = elements.ComboBoxRegular(label="Unwrap Type",
                                                        items=UNWRAP_TYPES,
                                                        toolTip=toolTip,
                                                        setIndex=self.properties.unwrapTypeCombo.value)
        # Transfer Shader Space Combobox -----------------------------------------------------
        toolTip = "Automatic Direction: Recommended, will auto rotate the shell vertically and unfold vertically. \n" \
                  "Regular Unfold:  Uses Maya's Unfold3d plugin to unfold in all directions, ignores straighten. \n" \
                  "Horizontal U Direction: Does not rotate shell and unfolds on U only. \n" \
                  "Vertical V Direction: Does not rotate shell and unfolds on V only"
        self.unfoldOptionsCombo = elements.ComboBoxRegular(label="Unfold Options",
                                                           items=UNFOLD_OPTIONS,
                                                           toolTip=toolTip,
                                                           setIndex=self.properties.unfoldOptionsCombo.value)
        # Unwrap Tube Main Button ---------------------------------------
        toolTip = "UV unwrap a quad tube. \n" \
                  "Select one edge length-ways down a tube, \n" \
                  "the edge will become the seam, then run."
        self.unwrapTube = elements.styledButton("Unfold Tube (By Edge)",
                                                "unwrapTube",
                                                toolTip=toolTip,
                                                style=uic.BTN_DEFAULT)
        # Unwrap Grid Shell Main Button ---------------------------------------
        toolTip = "UV unwrap a quad grid shell, such as a road. \n" \
                  "Select one interior edge loop length-ways down a shell grid. \n" \
                  "Run the tool."
        self.unwrapShell = elements.styledButton("Unfold Shell Grid (Edge)",
                                                 "checker",
                                                 toolTip=toolTip,
                                                 style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # Edgeloop Straighten Button ---------------------------------------
            toolTip = "Edgeloop Straighten \n" \
                      "Select a single edgeloop inside the shell and run. \n" \
                      "Straightens multiple edgeloops along a quad grid UV shell. \n" \
                      "Edgeloop can be horizontal or vertical. "
            self.edgeLoopStraightenBtn = elements.styledButton("Edgeloop Straighten",
                                                               "straightenEdge",
                                                               toolTip=toolTip,
                                                               style=uic.BTN_LABEL_SML)
            # Align Buttons ---------------------------------------
            toolTip = "Align selection - most left position "
            self.alignLabel = elements.Label("Align Selection", None, toolTip=toolTip)
            self.horizontalAlignLeftBtn = elements.styledButton("",
                                                                "horizontalAlignLeft",
                                                                toolTip=toolTip,
                                                                style=uic.BTN_TRANSPARENT_BG,
                                                                minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Align selection - most right position "
            self.horizontalAlignRightBtn = elements.styledButton("",
                                                                 "horizontalAlignRight",
                                                                 toolTip=toolTip,
                                                                 style=uic.BTN_TRANSPARENT_BG,
                                                                 minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Align selection - center horizontal position "
            self.horizontalAlignCenterBtn = elements.styledButton("",
                                                                  "horizontalAlignCenter",
                                                                  toolTip=toolTip,
                                                                  style=uic.BTN_TRANSPARENT_BG,
                                                                  minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Align selection - most top position "
            self.verticalAlignTopBtn = elements.styledButton("",
                                                             "verticalAlignTop",
                                                             toolTip=toolTip,
                                                             style=uic.BTN_TRANSPARENT_BG,
                                                             minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Align selection - most bottom position"
            self.verticalAlignBottomBtn = elements.styledButton("",
                                                                "verticalAlignBottom",
                                                                toolTip=toolTip,
                                                                style=uic.BTN_TRANSPARENT_BG,
                                                                minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Align straighten selection - center vertical position "
            self.verticalAlignCenterBtn = elements.styledButton("",
                                                                "verticalAlignCenter",
                                                                toolTip=toolTip,
                                                                style=uic.BTN_TRANSPARENT_BG,
                                                                minWidth=uic.BTN_W_ICN_SML)
            # Straighten Angle ---------------------------------------
            toolTip = "Straighten multiple selection with an angle limit. "
            self.straightenAngleLabel = elements.Label("Straighten Angle Limit", toolTip=toolTip)
            toolTip = "The angle limit for the straighten buttons (right). "
            self.straightenAngleEdit = elements.FloatEdit("",
                                                           editText="80",
                                                           labelRatio=1,
                                                           editRatio=1,
                                                           toolTip=toolTip)
            # Straighten Buttons ---------------------------------------
            toolTip = "Straighten selection, can be any component selection. \n" \
                      "Can select multiple rows and or columns to straighten. \n" \
                      "Will attempt to straighten within an angle limit."
            self.straightenAllBtn = elements.styledButton("",
                                                          "arrowFourWay",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Straighten a horizontal selection \n" \
                      "Can select multiple rows to straighten. \n" \
                      "Will attempt to straighten within the angle limit."
            self.straightenHorizontalBtn = elements.styledButton("",
                                                                 "arrowLeftRight",
                                                                 toolTip=toolTip,
                                                                 style=uic.BTN_TRANSPARENT_BG,
                                                                 minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Straighten a vertical selection \n" \
                      "Can select multiple columns to straighten. \n" \
                      "Will attempt to straighten within the angle limit."
            self.straightenVerticalBtn = elements.styledButton("",
                                                               "arrowUpDown",
                                                               toolTip=toolTip,
                                                               style=uic.BTN_TRANSPARENT_BG,
                                                               minWidth=uic.BTN_W_ICN_SML)
            # Delete History CheckBox ---------------------------------------
            toolTip = "Delete history after completing functions?"
            self.delHistoryCheckBox = elements.CheckBox(label="Delete History",
                                                        checked=True,
                                                        toolTip=toolTip)


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
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.LRGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Btn Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.unwrapTube)
        btnLayout.addWidget(self.unwrapShell)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addWidget(self.unwrapTypeCombo)
        contentsLayout.addWidget(self.unfoldOptionsCombo)
        contentsLayout.addItem(elements.Spacer(0, uic.REGPAD))  # extra space between widgets, width, height
        contentsLayout.addLayout(btnLayout)


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
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.LRGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Straighten Layout ---------------------------------------
        straightenLayout = elements.hBoxLayout(spacing=0)
        straightenLayout.addWidget(self.straightenAngleEdit, 3)
        straightenLayout.addWidget(self.straightenHorizontalBtn, 1)
        straightenLayout.addWidget(self.straightenVerticalBtn, 1)
        straightenLayout.addWidget(self.straightenAllBtn, 1)
        # Align Layout ---------------------------------------
        alignLayout = elements.hBoxLayout(spacing=0)
        alignLayout.addWidget(self.horizontalAlignLeftBtn)
        alignLayout.addWidget(self.horizontalAlignCenterBtn)
        alignLayout.addWidget(self.horizontalAlignRightBtn)
        alignLayout.addWidget(self.verticalAlignTopBtn)
        alignLayout.addWidget(self.verticalAlignCenterBtn)
        alignLayout.addWidget(self.verticalAlignBottomBtn)
        # Main Layout ---------------------------------------
        gridLayout = elements.GridLayout()
        gridLayout.addWidget(self.straightenAngleLabel, 0, 0)
        gridLayout.addLayout(straightenLayout, 0, 1)
        gridLayout.addWidget(self.delHistoryCheckBox, 1, 0)
        gridLayout.addWidget(self.edgeLoopStraightenBtn, 1, 1)
        gridLayout.addWidget(self.alignLabel, 2, 0)
        gridLayout.addLayout(alignLayout, 2, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Btn Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.unwrapTube)
        btnLayout.addWidget(self.unwrapShell)
        # Main Layout ---------------------------------------
        contentsLayout.addWidget(self.unwrapTypeCombo)
        contentsLayout.addWidget(self.unfoldOptionsCombo)
        contentsLayout.addLayout(gridLayout)
        contentsLayout.addLayout(btnLayout)
