from Qt import QtWidgets

from zoo.libs.maya.cmds.general import undodecorator
from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.objutils import curves
from zoo.libs.maya.cmds.rig import splines

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


AXIS_LIST = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]


class CurveDuplicate(toolsetwidgetmaya.ToolsetWidgetMaya):
    id = "curveDuplicate"
    info = "Duplicates objects along a curve."
    uiData = {"label": "Duplicate Along Curve (beta)",
              "icon": "objectsOnCurve",
              "tooltip": "Duplicates objects along a curve.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-duplicate-along-curve/"
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
        return super(CurveDuplicate, self).widgets()

    # ------------------
    # HELPER
    # ------------------

    def upFollowAxis(self):
        """Helper function for extracting upAxis, upAxisInvert, followAxis, followAxisInvert from the UI combobox's

        Takes the AXIS_LIST and returns the expected variables
        """
        upAxisInvert = False
        followAxisInvert = False

        upAxis = AXIS_LIST[self.properties.upAxisCombo.value].lower()
        followAxis = AXIS_LIST[self.properties.followAxisCombo.value].lower()

        plusMinusUp = upAxis[0]
        plusMinusFollow = followAxis[0]

        if plusMinusUp == "-":
            upAxisInvert = True
        if plusMinusFollow == "-":
            followAxisInvert = True

        upAxis = upAxis[1]
        followAxis = followAxis[1]

        return upAxis, upAxisInvert, followAxis, followAxisInvert

    # ------------------
    # LOGIC
    # ------------------

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """
        curves.createCurveContext(degrees=3)

    @undodecorator.undoDecorator
    def duplicateAlignObjects(self):
        """Run the duplicate
        """
        rotStart = [self.properties.rollStartFloat.value,
                    self.properties.headingStartFloat.value,
                    self.properties.tiltStartFloat.value]
        rotEnd = [self.properties.rollEndFloat.value,
                  self.properties.headingEndFloat.value,
                  self.properties.tiltEndFloat.value]
        if self.currentWidget == self.advancedWidget:
            scaleStart = [self.properties.scaleStartFloat.value,
                          self.properties.scaleStartFloat.value,
                          self.properties.scaleStartFloat.value]
            scaleEnd = [self.properties.scaleEndFloat.value,
                        self.properties.scaleEndFloat.value,
                        self.properties.scaleEndFloat.value]
        else:
            scaleStart = [self.properties.scaleStartFloat.value,
                          self.properties.scaleStartFloat.value,
                          self.properties.scaleStartFloat.value]
            scaleEnd = [self.properties.scaleEndFloat.value,
                        self.properties.scaleEndFloat.value,
                        self.properties.scaleEndFloat.value]
        upAxis, upAxisInvert, followAxis, followAxisInvert = self.upFollowAxis()
        splines.objectsAlongSplineSelected(multiplyObjects=self.properties.multipleInt.value - 1,
                                           spacingStart=self.properties.startPosFloat.value,
                                           spacingEnd=self.properties.endPosFloat.value,
                                           rotationStart=rotStart,
                                           rotationEnd=rotEnd,
                                           scaleStart=scaleStart,
                                           scaleEnd=scaleEnd,
                                           instance=self.properties.duplicateInstanceCombo.value,
                                           follow=self.properties.followModeCheckbox.value,
                                           fractionMode=self.properties.fractionModeCheckbox.value,
                                           upAxis=upAxis,
                                           followAxis=followAxis,
                                           group=self.properties.groupGeoCheckbox.value,
                                           deleteMotionPaths=not self.properties.keepLiveCheckbox.value,
                                           inverseFront=followAxisInvert,
                                           inverseUp=upAxisInvert,
                                           spacingWeight=self.properties.spacingWeightFSlider.value,
                                           weightPosition=self.properties.weightPositionCheckbox.value,
                                           weightRotation=self.properties.weightRotationCheckbox.value,
                                           weightScale=self.properties.weightScaleCheckbox.value,
                                           worldUpType="objectrotation",
                                           autoWorldUpV=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.alignObjectsBtn.clicked.connect(self.duplicateAlignObjects)
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
        """
        Options to add
        spacingWeight=0.5, worldUpVector=(0, 1, 0), worldUpType=WORLD_UP_SCENE, motionPName="moPth", worldUpObject=""
        """
        # Multiple Textbox ---------------------------------------
        tooltip = "Duplicate or Instance the object/s by this amount"
        self.multipleInt = elements.IntEdit(label="Multiple",
                                               editText=20,
                                               toolTip=tooltip,
                                               editRatio=2,
                                               labelRatio=1)
        # Instance Textbox ---------------------------------------
        tooltip = "Duplicate or Instance objects?"
        self.duplicateInstanceCombo = elements.ComboBoxRegular(label="",
                                                               items=["Duplicate", "Instance"],
                                                               toolTip=tooltip)
        # Object Up Textbox ---------------------------------------
        tooltip = "Set the object's up axis"
        self.upAxisCombo = elements.ComboBoxRegular(label="Up",
                                                    items=["+X", "-X", "+Y", "-Y", "+Z", "-Z"],
                                                    toolTip=tooltip,
                                                    setIndex=2,
                                                    boxRatio=2,
                                                    labelRatio=1)
        # Object Up Textbox ---------------------------------------
        tooltip = "Set the object's follow axis"
        self.followAxisCombo = elements.ComboBoxRegular(label="Follow",
                                                        items=["+X", "-X", "+Y", "-Y", "+Z", "-Z"],
                                                        toolTip=tooltip,
                                                        setIndex=4,
                                                        boxRatio=2,
                                                        labelRatio=1)
        # Start End Titles ---------------------------------------
        self.startTitle = elements.LabelDivider(text="Start")
        self.endTitle = elements.LabelDivider(text="End")
        self.objectAxisTitle = elements.LabelDivider(text="Object Axis")
        # Start Position Textbox ---------------------------------------
        tooltip = "The starting position along the curve. \n" \
                  "The value is either a faction (0.0 - 1.0) or a distance value. \n" \
                  "See the `Position As Fraction` checkbox."
        self.startPosFloat = elements.FloatEdit(label="Position",
                                                 editText="0.0",
                                                 toolTip=tooltip,
                                                 editRatio=2,
                                                 labelRatio=1)
        # End Position Textbox ---------------------------------------
        tooltip = "The end position along the curve. Value is \n" \
                  "The value is either a faction (0.0 - 1.0) or a distance value. \n" \
                  "See the `Position As Fraction` checkbox."
        self.endPosFloat = elements.FloatEdit(label="Position",
                                               editText="1.0",
                                               toolTip=tooltip,
                                               editRatio=2,
                                               labelRatio=1)
        # Roll Start Textbox ---------------------------------------
        tooltip = "The start roll rotation value"
        self.rollStartFloat = elements.FloatEdit(label="Roll",
                                                  editText="0.0",
                                                  toolTip=tooltip,
                                                  editRatio=2,
                                                  labelRatio=1)
        # Roll End Textbox ---------------------------------------
        tooltip = "The end roll rotation value"
        self.rollEndFloat = elements.FloatEdit(label="Roll",
                                                editText="0.0",
                                                toolTip=tooltip,
                                                editRatio=2,
                                                labelRatio=1)
        # Scale Start Textbox ---------------------------------------
        tooltip = "The start scale value"
        self.scaleStartFloat = elements.FloatEdit(label="Scale",
                                                   editText="1.0",
                                                   toolTip=tooltip,
                                                   editRatio=2,
                                                   labelRatio=1)
        # Scale End Textbox ---------------------------------------
        tooltip = "The end scale value"
        self.scaleEndFloat = elements.FloatEdit(label="Scale",
                                                 editText="1.0",
                                                 toolTip=tooltip,
                                                 editRatio=2,
                                                 labelRatio=1)
        # Spacing Weight Slider  ------------------------------------
        tooltip = "The spacing weight between object from one end of the curve or the other. \n" \
                  "A value of 0.0 will evenly space objects."
        self.spacingWeightFSlider = elements.FloatSlider(label="Weight",
                                                         toolTip=tooltip,
                                                         sliderMin=-2.0,
                                                         sliderMax=2.0,
                                                         labelRatio=1,
                                                         editBoxRatio=2)
        # Create CV Curve Button ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic)"
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=parent,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Align Button ---------------------------------------
        tooltip = "Select object or objects and then a NURBS curve. \n" \
                  "The first selected object/s will be duplicated/instanced \n " \
                  "and aligned to the curve."
        self.alignObjectsBtn = elements.styledButton("Align/Duplicate Objects",
                                                     icon="objectsOnCurve",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # Follow Checkbox ---------------------------------------
            tooltip = "Orient the object/s along the curve?"
            self.followModeCheckbox = elements.CheckBox(label="Follow Rotation",
                                                        toolTip=tooltip,
                                                        checked=True)
            # Fraction Checkbox ---------------------------------------
            tooltip = "On: Position textbox of 1.0 represents the full curve length and 0.5 is half way. \n" \
                      "Off: The position textbox will be in Maya units, usually cms though  \n " \
                      "curve CVs must be equally spaced"
            self.fractionModeCheckbox = elements.CheckBox(label="Position As Fraction",
                                                          toolTip=tooltip,
                                                          checked=True)
            # Keep Live Checkbox ---------------------------------------
            tooltip = "If on the setup will continue to snap to the live curve. \n" \
                      "If off the motion path nodes will be deleted"
            self.keepLiveCheckbox = elements.CheckBox(label="Keep Live",
                                                      toolTip=tooltip,
                                                      checked=True)
            # Group Geo Checkbox ---------------------------------------
            tooltip = "Will group the geo in a group called `curveName_objs_grp`"
            self.groupGeoCheckbox = elements.CheckBox(label="Group All Geo",
                                                      toolTip=tooltip,
                                                      checked=True)
            # Tilt Start Textbox ---------------------------------------
            tooltip = "The start heading rotation value"
            self.tiltStartFloat = elements.FloatEdit(label="Tilt",
                                                      editText="0.0",
                                                      toolTip=tooltip,
                                                      editRatio=2,
                                                      labelRatio=1)
            # Tilt End Textbox ---------------------------------------
            tooltip = "The end tilt rotation value"
            self.tiltEndFloat = elements.FloatEdit(label="Tilt",
                                                    editText="0.0",
                                                    toolTip=tooltip,
                                                    editRatio=2,
                                                    labelRatio=1)
            # Heading Start Textbox ---------------------------------------
            tooltip = "The start heading rotation value"
            self.headingStartFloat = elements.FloatEdit(label="Heading",
                                                         editText="0.0",
                                                         toolTip=tooltip,
                                                         editRatio=2,
                                                         labelRatio=1)
            # Heading End Textbox ---------------------------------------
            tooltip = "The end roll rotation value"
            self.headingEndFloat = elements.FloatEdit(label="Heading",
                                                       editText="0.0",
                                                       toolTip=tooltip,
                                                       editRatio=2,
                                                       labelRatio=1)
            # Weight Position Checkbox ---------------------------------------
            self.weightTitle = elements.LabelDivider(text="Weight Spacing")
            # Weight Position Checkbox ---------------------------------------
            tooltip = "The weight slider will affect position spacing"
            self.weightPositionCheckbox = elements.CheckBox(label="Weight Position",
                                                            toolTip=tooltip,
                                                            checked=True)
            # Weight Position Checkbox ---------------------------------------
            tooltip = "The weight slider will affect rotation offsets"
            self.weightRotationCheckbox = elements.CheckBox(label="Weight Rotation",
                                                            toolTip=tooltip,
                                                            checked=True)
            # Weight Scale Checkbox ---------------------------------------
            tooltip = "The weight slider will affect scale offsets"
            self.weightScaleCheckbox = elements.CheckBox(label="Weight Scale",
                                                         toolTip=tooltip,
                                                         checked=True)


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
        # Multiply Layout ---------------------------------------
        multiplyLayout = elements.hBoxLayout()
        multiplyLayout.addWidget(self.multipleInt, 1)
        multiplyLayout.addWidget(self.duplicateInstanceCombo, 1)
        # Up Axis Layout ---------------------------------------
        upAxisLayout = elements.hBoxLayout()
        upAxisLayout.addWidget(self.upAxisCombo, 1)
        upAxisLayout.addWidget(self.followAxisCombo, 1)
        # Start end title Layout ---------------------------------------
        titleLayout = elements.hBoxLayout()
        titleLayout.addWidget(self.startTitle, 1)
        titleLayout.addWidget(self.endTitle, 1)
        # Start end Pos Layout ---------------------------------------
        posLayout = elements.hBoxLayout()
        posLayout.addWidget(self.startPosFloat, 1)
        posLayout.addWidget(self.endPosFloat, 1)
        # Start end roll Layout ---------------------------------------
        rollLayout = elements.hBoxLayout()
        rollLayout.addWidget(self.rollStartFloat, 1)
        rollLayout.addWidget(self.rollEndFloat, 1)
        # Start end Scale Layout ---------------------------------------
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        scaleLayout.addWidget(self.scaleStartFloat, 1)
        scaleLayout.addWidget(self.scaleEndFloat, 1)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.alignObjectsBtn, 9)
        btnLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(multiplyLayout)
        mainLayout.addWidget(self.objectAxisTitle)
        mainLayout.addLayout(upAxisLayout)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(posLayout)
        mainLayout.addLayout(rollLayout)
        mainLayout.addLayout(scaleLayout)
        mainLayout.addWidget(self.spacingWeightFSlider)
        mainLayout.addLayout(btnLayout)


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
        # Follow Fraction Layout ---------------------------------------
        followLayout = elements.hBoxLayout(margins=(uic.SLRG, uic.SREG, uic.SLRG, 0))
        followLayout.addWidget(self.followModeCheckbox, 1)
        followLayout.addWidget(self.fractionModeCheckbox, 1)
        # Keep Live Layout ---------------------------------------
        keepLiveLayout = elements.hBoxLayout(margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SREG))
        keepLiveLayout.addWidget(self.keepLiveCheckbox, 1)
        keepLiveLayout.addWidget(self.groupGeoCheckbox, 1)
        # Multiply Layout ---------------------------------------
        multiplyLayout = elements.hBoxLayout()
        multiplyLayout.addWidget(self.multipleInt, 1)
        multiplyLayout.addWidget(self.duplicateInstanceCombo, 1)
        # Up Axis Layout ---------------------------------------
        upAxisLayout = elements.hBoxLayout()
        upAxisLayout.addWidget(self.upAxisCombo, 1)
        upAxisLayout.addWidget(self.followAxisCombo, 1)
        # Start end title Layout ---------------------------------------
        titleLayout = elements.hBoxLayout()
        titleLayout.addWidget(self.startTitle, 1)
        titleLayout.addWidget(self.endTitle, 1)
        # Start end Pos Layout ---------------------------------------
        posLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        posLayout.addWidget(self.startPosFloat, 1)
        posLayout.addWidget(self.endPosFloat, 1)
        # Start end roll Layout ---------------------------------------
        rollLayout = elements.hBoxLayout()
        rollLayout.addWidget(self.rollStartFloat, 1)
        rollLayout.addWidget(self.rollEndFloat, 1)
        # Start end Heading Layout ---------------------------------------
        headingLayout = elements.hBoxLayout()
        headingLayout.addWidget(self.headingStartFloat, 1)
        headingLayout.addWidget(self.headingEndFloat, 1)
        # Start end Tilt Layout ---------------------------------------
        tiltLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        tiltLayout.addWidget(self.tiltStartFloat, 1)
        tiltLayout.addWidget(self.tiltEndFloat, 1)
        # Start end Scale Layout ---------------------------------------
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        scaleLayout.addWidget(self.scaleStartFloat, 1)
        scaleLayout.addWidget(self.scaleEndFloat, 1)
        # Keep Live Layout ---------------------------------------
        weightCheckLayout = elements.hBoxLayout(margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SREG))
        weightCheckLayout.addWidget(self.weightPositionCheckbox, 1)
        weightCheckLayout.addWidget(self.weightRotationCheckbox, 1)
        weightCheckLayout.addWidget(self.weightScaleCheckbox, 1)
        # Slider Layout ---------------------------------------
        sliderLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        sliderLayout.addWidget(self.spacingWeightFSlider)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout()
        btnLayout.addWidget(self.alignObjectsBtn, 9)
        btnLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(followLayout)
        mainLayout.addLayout(keepLiveLayout)
        mainLayout.addLayout(multiplyLayout)
        mainLayout.addWidget(self.objectAxisTitle)
        mainLayout.addLayout(upAxisLayout)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(posLayout)
        mainLayout.addLayout(rollLayout)
        mainLayout.addLayout(headingLayout)
        mainLayout.addLayout(tiltLayout)
        mainLayout.addLayout(scaleLayout)
        mainLayout.addWidget(self.weightTitle)
        mainLayout.addLayout(weightCheckLayout)
        mainLayout.addLayout(sliderLayout)

        mainLayout.addLayout(btnLayout)
