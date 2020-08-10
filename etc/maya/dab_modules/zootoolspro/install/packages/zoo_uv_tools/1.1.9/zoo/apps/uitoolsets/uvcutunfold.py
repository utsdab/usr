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
UI_MODE_MEDIUM = 1
UI_MODE_ADVANCED = 2
IMAGE_SIZES = ["32", "64", "128", "256", "512", "1024", "2048", "4096", "8192", "16384"]
DISPLAY_MODES = uvfunctions.DISPLAY_MODES
UNFOLD_PLUGIN_NAME = uvfunctions.UNFOLD_PLUGIN_NAME


class UvCutUnfold(toolsetwidgetmaya.ToolsetWidgetMaya):
    """Primary UV tools for cutting, projecting and unfolding.
    """
    id = "uvUnfold"
    uiData = {"label": "UV Cut Unfold",
              "icon": "unfold",
              "tooltip": "Primary UV tools for cutting, projecting and unfolding.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-uv-cut-unfold/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initmediumWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.compactWidget = GuiCompact(parent=parent, properties=self.properties, toolsetWidget=self)
        return parent

    def initmediumWidget(self):
        """Builds the Advanced GUI (self.mediumWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.mediumWidget = GuiMedium(parent=parent, properties=self.properties, toolsetWidget=self)
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
        return [{"name": "delHistoryCheckBox", "value": False},
                {"name": "imageSizeCombo", "value": 2},
                {"name": "autoSeamUnfoldSlider", "value": 0.0}]

    def saveProperties(self):
        """Saves properties, keeps self.properties up to date with every widget change
        Overridden function which automates properties updates. Exposed here in case of extra functionality.

        properties are auto-linked if the name matches the widget name
        """
        super(UvCutUnfold, self).saveProperties()
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

    @toolsetwidgetmaya.undoDecorator
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
        pass

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def openUvEditor(self):
        displayStyle = DISPLAY_MODES[self.properties.displayCombo.value]
        uvfunctions.openUVEditor(displayStyle=displayStyle)

    def setDisplayMode(self, index):
        displayStyle = DISPLAY_MODES[self.properties.displayCombo.value]
        uvfunctions.uvDisplayModePresets(displayStyle=displayStyle)

    @toolsetwidgetmaya.undoDecorator
    def planarProjectionCamera(self):
        # needs to check for active camera cause can fail
        # should fid the last node highlight it and t
        uvfunctions.uvProjectionSelection(type="planar", mapDirection="c", message=True)

    @toolsetwidgetmaya.undoDecorator
    def planarProjectionBestPlane(self):
        # should loop through shells and find the best plane of each
        uvfunctions.uvProjectionSelection(type="planar", mapDirection="bestPlane", message=True)

    @toolsetwidgetmaya.undoDecorator
    def cutUVs(self):
        uvfunctions.cutUvsSelection()

    @toolsetwidgetmaya.undoDecorator
    def cutPerimeterUVs(self):
        uvfunctions.cutPerimeterUVsSelection(constructionHistory=True)

    @toolsetwidgetmaya.undoDecorator
    def sewUVs(self):
        uvfunctions.sewUvsSelection()

    @toolsetwidgetmaya.undoDecorator
    def cutAndSewTool3d(self):
        uvfunctions.cutAndSewTool3d()

    @toolsetwidgetmaya.undoDecorator
    def autoSeamsUnfold(self):
        splitShells = self.properties.autoSeamUnfoldSlider.value
        mapSize = int(IMAGE_SIZES[self.properties.imageSizeCombo.value])
        uvfunctions.autoSeamsUnfoldSelection(splitShells=splitShells, cutPipes=1, select=1, mapSize=mapSize)

    @undodecorator.undoDecorator
    def unfoldUVs(self):
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
        mapSize = int(IMAGE_SIZES[self.properties.imageSizeCombo.value])
        uvfunctions.regularUnfoldSelectionPackOption(mapsize=mapSize, roomspace=1)  # packs if in object mode

    @undodecorator.undoDecorator
    def unfoldUVsDirection(self, dirType="horizontal"):
        uvfunctions.legacyUnfoldSelection(dirType=dirType)

    @undodecorator.undoDecorator
    def edgeUnwrapTube(self, mode="tube"):
        """Does the edge selection Tube Unwrap
        Select a single edge that is the seam for a tube and run.
        """
        if mode == "tube":
            uvmacros.unwrapTubeSelection(dirType="automatic",
                                         straightenLoops=True,
                                         unfold=True,
                                         straightenAngle=80,
                                         deleteHistory=self.properties.delHistoryCheckBox.value)
        else:
            uvmacros.unwrapGridShellSelection(dirType="automatic",
                                              straightenLoops=True,
                                              unfold=True,
                                              straightenAngle=80,
                                              deleteHistory=self.properties.delHistoryCheckBox.value)

    @undodecorator.undoDecorator
    def symmetryBrush(self):
        uvfunctions.symmetryBrush()

    @undodecorator.undoDecorator
    def orientToEdge(self):
        uvfunctions.orientEdge()

    @undodecorator.undoDecorator
    def orientToShell(self):
        uvfunctions.orientShell()

    @undodecorator.undoDecorator
    def layoutUvs(self):
        mapSize = int(IMAGE_SIZES[self.properties.imageSizeCombo.value])
        uvfunctions.layoutUvs(resolution=mapSize)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        for widget in self.widgets():
            uiInstance = widget.children()[0]
            uiInstance.openUvBtn.clicked.connect(self.openUvEditor)
            uiInstance.displayCombo.currentIndexChanged.connect(self.setDisplayMode)
            uiInstance.planarProjCamBtn.clicked.connect(self.planarProjectionCamera)
            uiInstance.unfoldBtn.clicked.connect(self.unfoldUVs)
            uiInstance.cutSewToolBtn.clicked.connect(self.cutAndSewTool3d)
            uiInstance.layoutBtn.clicked.connect(self.layoutUvs)
        # Medium
        self.mediumWidget.planarProjAutoBtn.clicked.connect(self.planarProjectionBestPlane)
        self.mediumWidget.unfoldTubeBtn.clicked.connect(partial(self.edgeUnwrapTube, mode="tube"))
        self.mediumWidget.unfoldGridBtn.clicked.connect(partial(self.edgeUnwrapTube, mode="grid"))
        self.mediumWidget.cutBtn.clicked.connect(self.cutUVs)
        self.mediumWidget.cutPerimeterBtn.clicked.connect(self.cutPerimeterUVs)
        self.mediumWidget.sewBtn.clicked.connect(self.sewUVs)
        self.mediumWidget.autoSeamUnfoldBtn.clicked.connect(self.autoSeamsUnfold)
        self.mediumWidget.symmetryBrushBtn.clicked.connect(self.symmetryBrush)
        self.mediumWidget.orientEdgeBtn.clicked.connect(self.orientToEdge)
        self.mediumWidget.orientShellBtn.clicked.connect(self.orientToShell)
        self.mediumWidget.unfoldHorizontalBtn.clicked.connect(partial(self.unfoldUVsDirection, dirType="horizontal"))
        self.mediumWidget.unfoldVerticalBtn.clicked.connect(partial(self.unfoldUVsDirection, dirType="vertical"))


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
        # Open UV Editor Button ---------------------------------------
        toolTip = "Open Maya's UV Editor"
        self.openUvBtn = elements.styledButton("Open UV Editor",
                                               "uvEditor",
                                               toolTip=toolTip,
                                               style=uic.BTN_LABEL_SML)
        # Display Combobox -----------------------------------------------------
        toolTip = "Change the UV display mode of the UV Editor \n" \
                  "Use 'middle-scroll' to quickly cycle through modes. \n" \
                  "Note: Presets may act unexpectedly due to Maya code issues."
        self.displayCombo = elements.ComboBoxRegular(label="",
                                                     items=DISPLAY_MODES,
                                                     toolTip=toolTip,
                                                     setIndex=2)
        # Planar Proj Camera Button ---------------------------------------
        toolTip = "Planar UV maps from the current camera. \n" \
                  "Click the channel box node in input history and press `T` \n" \
                  "to show the UV manipulator."
        self.planarProjCamBtn = elements.styledButton("Planar Projection Camera",
                                                      "planarCamera",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_LABEL_SML)
        # 3d Cut And Sew Button ---------------------------------------
        toolTip = "Mayas 3d Cut and Sew Tool. \n\n" \
                  "  LMB - Cut by dragging along edges \n" \
                  "  Double Click - Cuts edgeloop \n" \
                  "  Ctrl LMB - Sew along edges \n" \
                  "  Shift Drag - Grows an edge loop \n" \
                  "  Shift Double Click - Cut to second edge \n" \
                  "  Tab - Highlights edgeloops \n" \
                  "  X - Cut highlighted edges \n" \
                  "  S - Sew highlighted edges \n" \
                  "  Right Click - Exit tool and marking menu"
        self.cutSewToolBtn = elements.styledButton("3d Cut/Sew Tool",
                                                   "knife",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_LABEL_SML)
        # Unfold Main Button ---------------------------------------
        toolTip = "Unfold with Maya's Unfold 3d plugin. \n" \
                  "Also runs layout if not in component selection. \n" \
                  "Layout uses Texture Size to add 2 pixels between shells."
        self.unfoldBtn = elements.styledButton("Unfold",
                                               "unfold",
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        # Layout Main Button ---------------------------------------
        toolTip = "Layout (Pack) objects into 0-1 UV space. \n" \
                  "Uses Texture Size to add 2 pixels between shells. \n" \
                  "Increasing Texture Size slows the pack calculation."
        self.layoutBtn = elements.styledButton("Layout",
                                               "layout",
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_MEDIUM:
            # Planar Proj Camera Button ---------------------------------------
            toolTip = "Planar UV maps while keeping to the 'average normal' of the current selection. \n" \
                      "Usually used with face selection. \n" \
                      "Click the channel box node in input history and press `T` \n" \
                      "to show the UV manipulator."
            self.planarProjAutoBtn = elements.styledButton("Planar Projection Auto",
                                                           "planarAuto",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_LABEL_SML)
            # Cut Button ---------------------------------------
            toolTip = "UV cuts edge selection, select edges and run."
            self.cutBtn = elements.styledButton("Cut",
                                                "cut",
                                                toolTip=toolTip,
                                                style=uic.BTN_LABEL_SML)
            # Paste Button ---------------------------------------
            toolTip = "UV sews edge selection (opposite of cut), select cut edges and run."
            self.sewBtn = elements.styledButton("Sew",
                                                "sew",
                                                toolTip=toolTip,
                                                style=uic.BTN_LABEL_SML)
            # Cut Border Button ---------------------------------------
            toolTip = "Cuts around the perimeter of the selection, usually a face selection."
            self.cutPerimeterBtn = elements.styledButton("Cut Perimeter",
                                                         "cutPerimeter",
                                                         toolTip=toolTip,
                                                         style=uic.BTN_LABEL_SML)
            # Auto Unfold Button ---------------------------------------
            toolTip = "Creates seams automatically on an object, also runs unfold and layout. \n" \
                      "Use the slider to create more seams."
            self.autoSeamUnfoldBtn = elements.styledButton("Auto Seam Unfold",
                                                           "autoUnfold",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_LABEL_SML)
            toolTip = "Split Tolerance slider for 'Auto Seam Unfold'. \n" \
                      "Empty slider creates less seams. \n" \
                      "Full slider creates more seams"
            self.autoSeamUnfoldSlider = elements.HSlider(defaultValue=0.5, toolTip=toolTip)
            # Unfold Tube Button ---------------------------------------
            toolTip = "UV unwrap a quad tube. \n" \
                      "Select one edge length-ways down a tube, \n" \
                      "the edge will become the seam, then run."
            self.unfoldTubeBtn = elements.styledButton("Unfold Tube (By Edge)",
                                                       "unwrapTube",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
            # Unfold Shell Grid Button ---------------------------------------
            toolTip = "UV unwrap a quad grid shell, such as a road. \n" \
                      "Select one interior edge length-ways down a shell grid. \n" \
                      "Run the tool."
            self.unfoldGridBtn = elements.styledButton("Unfold Shell Grid (Edge)",
                                                       "checker",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
            # Unfold Direction Buttons ---------------------------------------
            toolTip = "Unfolds while restricting to the horizontal U axis only. \n" \
                      "Uses Maya's legacy unfold method."
            self.unfoldHorizontalBtn = elements.styledButton("Horizontal",
                                                             "arrowLeftRight",
                                                             toolTip=toolTip,
                                                             style=uic.BTN_DEFAULT,
                                                             minWidth=uic.BTN_W_ICN_SML)
            toolTip = "Unfolds while restricting to the vertical V axis only. \n" \
                      "Uses Maya's legacy unfold method."
            self.unfoldVerticalBtn = elements.styledButton("Vertical",
                                                           "arrowUpDown",
                                                           toolTip=toolTip,
                                                           style=uic.BTN_DEFAULT,
                                                           minWidth=uic.BTN_W_ICN_SML)
            # Symmetry Brush Button ---------------------------------------
            toolTip = "Symmetry Brush mirrors shells with a brush paint. \n" \
                      "Zoo version automatically finds the shell symmetry direction and pivot \n" \
                      " - Select a shell center edge, and run the tool. \n" \
                      " - Select the same edge again and paint."
            self.symmetryBrushBtn = elements.styledButton("Symmetry Brush",
                                                          "symmetryTri",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_LABEL_SML)
            # Orient To Edges Button ---------------------------------------
            toolTip = "Orient whole shell by selecting an edge. \n" \
                      "Will orient the whole shell so the edge becomes straight. \n" \
                      "- Select an edge and run."
            self.orientEdgeBtn = elements.styledButton("Orient To Edges",
                                                       "orientEdge",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
            # Image Size Combobox -----------------------------------------------------
            toolTip = "Texture size adjust Layout packing. \n" \
                      "Will add 2 pixels relative to the texture size between shells. \n" \
                      "Increasing Texture Size slows the pack calculation."
            self.imageSizeCombo = elements.ComboBoxRegular(label="",
                                                           items=IMAGE_SIZES,
                                                           toolTip=toolTip,
                                                           setIndex=5,
                                                           boxRatio=7,
                                                           labelRatio=9)
            # Orient To Shells Button ---------------------------------------
            toolTip = "Orient shells automatically. \n" \
                      "Select an object or UV shell and run."
            self.orientShellBtn = elements.styledButton("Orient",
                                                        "orientShell",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT,
                                                        minWidth=uic.BTN_W_ICN_SML)


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
                                             margins=(uic.WINSIDEPAD, uic.REGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.openUvBtn, 0, 0)
        gridLayout.addWidget(self.displayCombo, 0, 1)
        gridLayout.addWidget(self.planarProjCamBtn, 1, 0)
        gridLayout.addWidget(self.cutSewToolBtn, 1, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Grid Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.unfoldBtn, 1)
        btnLayout.addWidget(self.layoutBtn, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(gridLayout)
        contentsLayout.addLayout(btnLayout)


class GuiMedium(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_MEDIUM, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_MEDIUM)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiMedium, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                        toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(parent,
                                             margins=(uic.WINSIDEPAD, uic.REGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Unfold Btn Layout ---------------------------------------
        unfoldBtnLayout = elements.hBoxLayout()
        unfoldBtnLayout.addWidget(self.unfoldVerticalBtn, 1)
        unfoldBtnLayout.addWidget(self.unfoldHorizontalBtn, 1)
        # image size and orient shells
        imageSizeOrientLayout = elements.hBoxLayout()
        imageSizeOrientLayout.addWidget(self.imageSizeCombo, 1)
        imageSizeOrientLayout.addWidget(self.orientShellBtn, 1)
        # Grid Top Layout ---------------------------------------
        gridTopLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridTopLayout.addWidget(self.openUvBtn, 0, 0)
        gridTopLayout.addWidget(self.displayCombo, 0, 1)
        gridTopLayout.addWidget(self.planarProjAutoBtn, 1, 0)
        gridTopLayout.addWidget(self.planarProjCamBtn, 1, 1)
        gridTopLayout.addWidget(self.cutBtn, 2, 0)
        gridTopLayout.addWidget(self.sewBtn, 2, 1)
        gridTopLayout.addWidget(self.cutPerimeterBtn, 3, 0)
        gridTopLayout.addWidget(self.cutSewToolBtn, 3, 1)
        gridTopLayout.addWidget(self.symmetryBrushBtn, 4, 0)
        gridTopLayout.addWidget(self.orientEdgeBtn, 4, 1)
        gridTopLayout.addWidget(self.autoSeamUnfoldBtn, 5, 0)
        gridTopLayout.addWidget(self.autoSeamUnfoldSlider, 5, 1)
        gridTopLayout.addWidget(self.unfoldTubeBtn, 6, 0)
        gridTopLayout.addWidget(self.unfoldGridBtn, 6, 1)
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Grid Bot Layout ---------------------------------------
        gridBotLayout = elements.GridLayout(margins=(0, uic.SMLPAD, 0, 0))
        gridBotLayout.addLayout(unfoldBtnLayout, 5, 0)
        gridBotLayout.addWidget(self.unfoldBtn, 5, 1)
        gridBotLayout.addLayout(imageSizeOrientLayout, 6, 0)
        gridBotLayout.addWidget(self.layoutBtn, 6, 1)
        gridBotLayout.setColumnStretch(0, 1)
        gridBotLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(gridTopLayout)
        contentsLayout.addLayout(gridBotLayout)
