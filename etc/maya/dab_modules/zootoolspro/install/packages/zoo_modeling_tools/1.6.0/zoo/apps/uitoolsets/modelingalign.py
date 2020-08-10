from Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.modeling import pivots
from zoo.libs.maya.cmds.objutils import alignutils

from zoo.libs.maya.cmds.general import undodecorator

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

CENTER_SPACE_LIST = ["World Center", "Parent", "Object Center"]
ALIGN_OBJECTS_LIST = ["Rot/Trans", "Translation", "Rotation", "Scale", "Pivot", "All"]


class ModelingAlign(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "modelingAlign"
    info = "Alignment tools for modeling."
    uiData = {"label": "Modeling Align",
              "icon": "alignTool",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-modeling-align/"
              }

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

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidgetmaya.undoDecorator
    def centerPivotWorld(self, worldSpace=True):
        """Centers the pivot of all selected objects at the world center or local space center ie parent zero.
        """
        combo = self.properties.centerWorldCombo.value
        if combo == 0:
            pivots.centerPivotWorldSel(message=True)
        elif combo == 1:
            # match pivot to parent
            pivots.matchPivotParentSel(message=True)
        else:
            # center pivot
            pivots.centerPivotSelected()

    @toolsetwidgetmaya.undoDecorator
    def placeObjectOnGround(self):
        """Centers the pivot of all selected objects at the world center or local space center ie parent zero.
        """
        alignutils.placeObjectOnGroundSel()

    def snapTogetherTool(self):
        """Enters Maya's Snap Together Tool"""
        alignutils.mayaSnapTogetherTool()

    def alignTool(self):
        """Enters Maya's Align Tool"""
        alignutils.mayaAlignTool()

    def snapPointToPoint(self):
        """Enters Maya's Align Tool"""
        alignutils.snapPointToPoint()

    def snap2PointsTo2Points(self):
        """Enters Maya's Align Tool"""
        alignutils.snap2PointsTo2Points()

    def snap3PointsTo3Points(self):
        """Enters Maya's Align Tool"""
        alignutils.snap3PointsTo3Points()

    @toolsetwidgetmaya.undoDecorator
    def matchObjects(self):
        """Match objects to each other"""
        optionsInt = self.properties.matchObjectsCombo.value
        if optionsInt == 0:
            alignutils.matchAllSelection(translate=True, rotate=True, message=True)
        elif optionsInt == 1:
            alignutils.matchAllSelection(translate=True, message=True)
        elif optionsInt == 2:
            alignutils.matchAllSelection(rotate=True, message=True)
        elif optionsInt == 3:
            alignutils.matchAllSelection(scale=True, message=True)
        elif optionsInt == 4:
            alignutils.matchAllSelection(pivot=True, message=True)
        elif optionsInt == 5:
            alignutils.matchAllSelection(translate=True, rotate=True, scale=True, pivot=True, message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for uiInstance in self.uiInstanceList:
            uiInstance.centerWorldBtn.clicked.connect(self.centerPivotWorld)
            uiInstance.placeOnGroundBtn.clicked.connect(self.placeObjectOnGround)
            uiInstance.alignToolBtn.clicked.connect(self.alignTool)
            uiInstance.snapTogetherBtn.clicked.connect(self.snapTogetherTool)
            uiInstance.matchObjectsBtn.clicked.connect(self.matchObjects)
            uiInstance.snapAlignOneBtn.clicked.connect(self.snapPointToPoint)
            uiInstance.snapAlignTwoBtn.clicked.connect(self.snap2PointsTo2Points)
            uiInstance.snapAlignThreeBtn.clicked.connect(self.snap3PointsTo3Points)


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
        # Pivot Space Combo ---------------------------------------
        toolTip = "Center the pivot to \n" \
                  "  1. World Space: Pivot centers in the middle of the world. \n" \
                  "  2. Local Space: Pivot centers at the zero position of it's parent."
        self.centerWorldCombo = elements.ComboBoxRegular(label="Move Pivot",
                                                         items=CENTER_SPACE_LIST,
                                                         toolTip=toolTip,
                                                         boxRatio=15,
                                                         labelRatio=10)
        # Center World Pivot ---------------------------------------
        toolTip = "Center the pivot/s of the selected object at the center of the world or local space."
        self.centerWorldBtn = elements.styledButton("Center Pivot",
                                                    icon="centerTarget",
                                                    style=uic.BTN_DEFAULT,
                                                    toolTip=toolTip)
        # Match Objects Combo ---------------------------------------
        toolTip = "Match Objects Options \n" \
                  "  1. Rot/Trans: Match Rotation and Translation \n" \
                  "  2. Translation: Match Translation Only \n" \
                  "  3. Rotation: Match Rotation Only \n" \
                  "  4. Scale: Match Scale Only \n" \
                  "  5. Pivot: Match Pivot Only \n" \
                  "  6. All: Match Translate, Rotate, Scale and Pivot"
        self.matchObjectsCombo = elements.ComboBoxRegular(label="Match Type",
                                                          items=ALIGN_OBJECTS_LIST,
                                                          toolTip=toolTip,
                                                          boxRatio=15,
                                                          labelRatio=10)
        # Match Objects Button ---------------------------------------
        toolTip = "Matches multiple objects to the last selected.  \n" \
                  "  1. Select multiple objects \n" \
                  "  2. Run the tool" \
                  "First objects will be matched to the last. \n" \
                  "Uses the `Match Type` drop down settings"
        self.matchObjectsBtn = elements.styledButton("Match Objects",
                                                     icon="magnet",
                                                     style=uic.BTN_DEFAULT,
                                                     toolTip=toolTip)
        # Align Tool ---------------------------------------
        toolTip = "Activates Maya's `Align Tool`"
        self.alignToolBtn = elements.styledButton("Align Tool",
                                                  icon="alignTool",
                                                  style=uic.BTN_LABEL_SML,
                                                  toolTip=toolTip)
        # Snap Together Tool ---------------------------------------
        toolTip = "Activates Maya's `Snap Together Tool` \n" \
                  "  1. Click and drag on a surface of one object. \n" \
                  "  2. Then click and drag on another object \n" \
                  "  3. Press Enter"
        self.snapTogetherBtn = elements.styledButton("Snap Together Tool",
                                                     icon="snapTogether",
                                                     style=uic.BTN_LABEL_SML,
                                                     toolTip=toolTip)
        # Snap Align 1 ---------------------------------------
        toolTip = "Select two objects and select a point on each object. \n" \
                  "Run and the first object will be snaped to the last."
        self.snapAlignOneBtn = elements.styledButton("Snap Align One Point",
                                                      icon="snapAlignOne",
                                                      style=uic.BTN_LABEL_SML,
                                                      toolTip=toolTip)
        # Snap Align 2 ---------------------------------------
        toolTip = "Select two objects and select two points on each object. \n" \
                  "Run and the first object will be snaped to the last."
        self.snapAlignTwoBtn = elements.styledButton("Snap Align Two Points",
                                                      icon="snapAlignTwo",
                                                      style=uic.BTN_LABEL_SML,
                                                      toolTip=toolTip)
        # Snap Align 3 ---------------------------------------
        toolTip = "Select two objects and select three points on each object. \n" \
                  "Run and the first object will be snaped to the last."
        self.snapAlignThreeBtn = elements.styledButton("Snap Align Three Points",
                                                      icon="snapAlignThree",
                                                      style=uic.BTN_LABEL_SML,
                                                      toolTip=toolTip)
        # Place Object On Ground ---------------------------------------
        toolTip = "Places object's bounding box on the world ground place.  Zero Y. \n" \
                  "Rotated objects may need to have their transforms frozen to snap correctly."
        self.placeOnGroundBtn = elements.styledButton("Place On Ground Zero Y ",
                                                      icon="verticalAlignBottom",
                                                      style=uic.BTN_LABEL_SML,
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
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Pivot Layout ----------------------------
        pivotLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML))
        pivotLayout.addWidget(self.centerWorldCombo, 1)
        pivotLayout.addWidget(self.centerWorldBtn, 1)
        # Align Objects Layout --------------------------
        alignObjLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML))
        alignObjLayout.addWidget(self.matchObjectsCombo, 1)
        alignObjLayout.addWidget(self.matchObjectsBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.alignToolBtn, 2, 0)
        gridLayout.addWidget(self.placeOnGroundBtn, 2, 1)
        gridLayout.addWidget(self.snapAlignOneBtn, 3, 0)
        gridLayout.addWidget(self.snapAlignTwoBtn, 3, 1)
        gridLayout.addWidget(self.snapAlignThreeBtn, 4, 0)
        gridLayout.addWidget(self.snapTogetherBtn, 4, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(pivotLayout)
        mainLayout.addLayout(alignObjLayout)
        mainLayout.addLayout(gridLayout)


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
        mainLayout = elements.vBoxLayout(parent, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Pivot Layout ----------------------------
        pivotLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML))
        pivotLayout.addWidget(self.centerWorldCombo, 1)
        pivotLayout.addWidget(self.centerWorldBtn, 1)
        # Align Objects Layout --------------------------
        alignObjLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML))
        alignObjLayout.addWidget(self.matchObjectsCombo, 1)
        alignObjLayout.addWidget(self.matchObjectsBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.alignToolBtn, 2, 0)
        gridLayout.addWidget(self.placeOnGroundBtn, 2, 1)
        gridLayout.addWidget(self.snapAlignOneBtn, 3, 0)
        gridLayout.addWidget(self.snapAlignTwoBtn, 3, 1)
        gridLayout.addWidget(self.snapAlignThreeBtn, 4, 0)
        gridLayout.addWidget(self.snapTogetherBtn, 4, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(pivotLayout)
        mainLayout.addLayout(alignObjLayout)
        mainLayout.addLayout(gridLayout)
